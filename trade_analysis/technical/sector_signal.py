"""Sector-level TA signal from benchmark ETFs for index.html summary rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from result_score_access import avg_and_metrics, index_tech_score
from technical_reasons import (
    Verdict,
    build_technical_reasons,
    verdict_color,
    verdict_display_label,
    verdict_sort_rank,
)

TECH_ROOT = Path(__file__).resolve().parent
SECTOR_ETFS_PATH = TECH_ROOT / "sector_etfs.json"
RANK_TFS: Tuple[str, ...] = ("1W", "2W", "1M", "2M")
TF_SHORT = {"1W": "W", "2W": "2W", "1M": "M", "2M": "2M"}

MAX_PICKS_PER_SECTOR = 10
MAX_ETFS_PER_SECTOR = 2

_SECTOR_VERDICTS: Tuple[str, ...] = (
    "Strong Accumulation",
    "Accumulation",
    "Neutral",
    "Sell",
    "Strong Sell (Get Out)",
)

SECTOR_ROW_CLASS = {
    "Strong Accumulation": "sector-strong-accumulation",
    "Accumulation": "sector-accumulation",
    "Neutral": "sector-neutral",
    "Sell": "sector-sell",
    "Strong Sell (Get Out)": "sector-strong-sell",
}

SECTOR_VERDICT_TEXT_CLASS = {
    "Strong Accumulation": "sector-verdict-strong-accum",
    "Accumulation": "sector-verdict-accum",
    "Neutral": "sector-verdict-neutral",
    "Sell": "sector-verdict-sell",
    "Strong Sell (Get Out)": "sector-verdict-strong-sell",
}


def sector_verdict_sort_rank(verdict: str) -> int:
    """Sort index sections: Strong Accum → Accum → Neutral → Sell → Strong Sell."""
    return verdict_sort_rank(verdict)


def sector_row_css_class(verdict: str) -> str:
    return SECTOR_ROW_CLASS.get(verdict, "sector-neutral")


def load_sector_etfs() -> Dict[str, List[str]]:
    if not SECTOR_ETFS_PATH.is_file():
        return {}
    try:
        data = json.loads(SECTOR_ETFS_PATH.read_text(encoding="utf-8"))
        out: Dict[str, List[str]] = {}
        for k, v in data.items():
            if str(k).startswith("_") or not isinstance(v, list):
                continue
            out[str(k)] = [str(s).upper() for s in v if s]
        return out
    except (json.JSONDecodeError, OSError):
        return {}


def _find_symbol_in_results(
    symbol: str,
    result_dir: Path,
) -> Optional[Tuple[dict, str]]:
    sym_u = symbol.upper()
    if not result_dir.is_dir():
        return None
    for path in sorted(result_dir.glob("*_results.json")):
        cat = path.stem.replace("_results", "")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if sym_u in data and isinstance(data[sym_u], dict):
            return data[sym_u], cat
        for k, v in data.items():
            if k.upper() == sym_u and isinstance(v, dict):
                return v, cat
    return None


def _normalize_verdict(v: str) -> str:
    legacy = {
        "Buy": "Strong Accumulation",
        "Take profit": "Sell",
    }
    return legacy.get(v, v)


def _aggregate_sector_verdict(votes: List[str]) -> str:
    if not votes:
        return "Neutral"
    counts = Counter(votes)
    top = counts.most_common()
    if len(top) == 1:
        return top[0][0]
    if top[0][1] > top[1][1]:
        return top[0][0]
    tied = [v for v, n in top if n == top[0][1]]
    if "Neutral" in tied:
        return "Neutral"
    tied.sort(key=verdict_sort_rank)
    return tied[0]


def compute_sector_signal(
    category: str,
    result_dir: Path,
    *,
    sector_etfs: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    mapping = sector_etfs or load_sector_etfs()
    etfs = mapping.get(category, [])
    details: List[Dict[str, Any]] = []
    votes: List[str] = []

    for sym in etfs:
        found = _find_symbol_in_results(sym, result_dir)
        if not found:
            details.append({"symbol": sym, "verdict": None, "tech_score": None, "missing": True})
            continue
        sym_data, _cat = found
        tech_avg, metrics = avg_and_metrics(sym_data, RANK_TFS, denom="usd", missing_sentinel=-999.0)
        if tech_avg <= -900:
            details.append({"symbol": sym, "verdict": None, "tech_score": None, "missing": True})
            continue
        tech_score = index_tech_score(tech_avg, metrics, RANK_TFS)
        verdict, _ = build_technical_reasons(metrics, RANK_TFS, TF_SHORT)
        sector_v = _normalize_verdict(verdict)
        votes.append(sector_v)
        details.append(
            {
                "symbol": sym,
                "verdict": sector_v,
                "tech_score": tech_score,
                "missing": False,
            }
        )

    sector_verdict = _aggregate_sector_verdict(votes)
    present = [d for d in details if not d.get("missing")]
    etf_labels = ", ".join(d["symbol"] for d in present) if present else "—"
    return {
        "category": category,
        "sector_verdict": sector_verdict,
        "sector_verdict_display": verdict_display_label(sector_verdict),  # type: ignore[arg-type]
        "sector_verdict_color": verdict_color(sector_verdict),  # type: ignore[arg-type]
        "sector_row_class": sector_row_css_class(sector_verdict),
        "sector_verdict_text_class": SECTOR_VERDICT_TEXT_CLASS.get(sector_verdict, "sector-verdict-neutral"),
        "etf_labels": etf_labels,
        "etf_details": details,
        "etf_summary": _format_etf_summary(details),
    }


def _format_etf_summary(details: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for d in details:
        sym = d["symbol"]
        if d.get("missing"):
            parts.append(f"{sym}: —")
            continue
        v = d.get("verdict") or "Neutral"
        ts = d.get("tech_score")
        if ts is not None:
            parts.append(f"{sym}: {v} ({ts:.1f})")
        else:
            parts.append(f"{sym}: {v}")
    return " · ".join(parts) if parts else "No ETF data — run full pipeline with updated configuration."


def _row_symbol_keys(row: Dict[str, Any]) -> Set[str]:
    keys: Set[str] = set()
    for k in ("yahoo_symbol", "symbol"):
        v = str(row.get(k, "")).strip().upper()
        if v:
            keys.add(v)
    return keys


def _resolve_must_include_symbols(symbols: Sequence[str]) -> Set[str]:
    keys: Set[str] = set()
    try:
        from config_loader import get_ticker
    except Exception:
        get_ticker = lambda x: None  # type: ignore[assignment, misc]
    for sym in symbols:
        s = str(sym).strip().upper()
        if not s:
            continue
        keys.add(s)
        resolved = get_ticker(sym) or get_ticker(s)
        if resolved:
            keys.add(resolved.upper())
    return keys


def pick_sector_index_rows(
    category: str,
    rows: List[Dict[str, Any]],
    *,
    max_picks: int = MAX_PICKS_PER_SECTOR,
    etfs_per_industry: int = MAX_ETFS_PER_SECTOR,
    sector_etfs: Optional[Dict[str, List[str]]] = None,
    must_include: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Top sector ETFs + stocks by final score; capped at max_picks (default 10) per sector."""
    mapping = sector_etfs or load_sector_etfs()
    etf_syms = {s.upper() for s in mapping.get(category, [])}

    if must_include is None:
        try:
            from config_loader import get_index_must_include

            must_include = get_index_must_include(category)
        except Exception:
            must_include = []
    must_keys = _resolve_must_include_symbols(must_include or [])

    def _is_sector_etf(row: Dict[str, Any]) -> bool:
        return bool(_row_symbol_keys(row) & etf_syms)

    def _is_must_include(row: Dict[str, Any]) -> bool:
        return bool(_row_symbol_keys(row) & must_keys)

    def _sort_key(row: Dict[str, Any]) -> Tuple[float, float, str]:
        return (-row["final_score"], -row["tech_score"], str(row.get("symbol", "")))

    etf_rows = sorted([r for r in rows if _is_sector_etf(r)], key=_sort_key)
    pinned = sorted([r for r in rows if _is_must_include(r) and not _is_sector_etf(r)], key=_sort_key)
    pinned_keys = {k for r in pinned for k in _row_symbol_keys(r)}
    stock_rows = sorted(
        [r for r in rows if not _is_sector_etf(r) and not (_row_symbol_keys(r) & pinned_keys)],
        key=_sort_key,
    )

    etf_cap = min(max(0, etfs_per_industry), max_picks)
    chosen = list(etf_rows[:etf_cap])
    chosen_keys = {k for r in chosen for k in _row_symbol_keys(r)}

    for r in pinned:
        if len(chosen) >= max_picks:
            break
        if not (_row_symbol_keys(r) & chosen_keys):
            chosen.append(r)
            chosen_keys |= _row_symbol_keys(r)

    for r in stock_rows:
        if len(chosen) >= max_picks:
            break
        if not (_row_symbol_keys(r) & chosen_keys):
            chosen.append(r)
            chosen_keys |= _row_symbol_keys(r)

    return chosen
