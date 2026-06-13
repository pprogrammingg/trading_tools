#!/usr/bin/env python3
"""
Build fundamental_hot_picks.json for the hot pick plan page.

Screens configuration categories + extra tickers with fundamental_halal_screen (excludes
defense, gambling, alcohol, etc.), ranks by EBITDA/growth metrics from yfinance, and
writes JSON consumed by ui_assets.write_landing_artifacts.

Usage (from repo root):
  python trade_analysis/fundamentals/generate_fundamental_hot_picks.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

_FUND_ROOT = Path(__file__).resolve().parent
_TRADE_ROOT = _FUND_ROOT.parent
if str(_TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRADE_ROOT))
from trade_paths import TECH_ROOT, setup_import_paths  # noqa: E402

setup_import_paths()

from exclusion_policy import FUNDAMENTAL_SCAN_SKIP_CATEGORIES  # noqa: E402
from fundamental_halal_screen import (  # noqa: E402
    composite_score,
    fetch_screen_info,
    format_fundamental_blurb,
)
from universe_collectors import collect_equity_symbols_from_config  # noqa: E402

EXTRA_TICKERS: Tuple[str, ...] = (
    "CRWD",
    "ZS",
    "PANW",
    "SNPS",
    "CDNS",
    "ANET",
    "FTNT",
    "NET",
    "DDOG",
    "MDB",
    "TEAM",
    "HUBS",
    "DOCN",
    "GTLB",
    "CFLT",
    "VEEV",
    "DXCM",
    "ISRG",
    "IDXX",
    "VRT",
    "STX",
)


def _price_str(info: Dict[str, Any]) -> str:
    p = info.get("price")
    if p is None:
        return "—"
    if p >= 1000:
        return f"{p:,.0f}"
    if p >= 1:
        return f"{p:.2f}".rstrip("0").rstrip(".")
    return f"{p:.4f}".rstrip("0").rstrip(".")


def run_screen(limit: int, skip_fetch: bool = False) -> Dict[str, Any]:
    """Rank by yfinance fundamentals after halal keyword screen. Empty → static fallback rows."""
    if skip_fetch:
        from ui_assets import FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS

        rows_fb = [list(r) for r in FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS[:limit]]
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "fallback_no_yfinance",
            "criteria": (
                "Install yfinance to screen your configuration universe; until then this file uses "
                "the same static fallback as ui_assets (halal-aware narrative rows)."
            ),
            "universe_size": 0,
            "rows": rows_fb,
        }

    universe = collect_equity_symbols_from_config(
        skip_categories=FUNDAMENTAL_SCAN_SKIP_CATEGORIES,
        extra_tickers=EXTRA_TICKERS,
    )
    rows_raw: List[Dict[str, Any]] = []
    for sym in universe:
        try:
            m = fetch_screen_info(sym)
        except Exception as e:
            rows_raw.append({"ticker": sym, "error": str(e)})
            continue
        if m.get("excluded"):
            continue
        rows_raw.append(m)

    scored = [(composite_score(m), m) for m in rows_raw if "error" not in m]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    rows_out: List[List[str]] = []
    for _score, m in top:
        t = m["ticker"]
        ind = m.get("industry") or m.get("sector") or "—"
        fund = format_fundamental_blurb(m)
        tech = (
            "Cross-check the matching category scores HTML in this repo; "
            "use 1–6M horizon for entry timing after fundamentals pass."
        )
        rows_out.append(
            [
                t,
                _price_str(m),
                ind[:80] if isinstance(ind, str) else "—",
                fund,
                tech,
            ]
        )

    source = "yfinance_ranked"
    if not rows_out:
        from ui_assets import FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS

        rows_out = [list(r) for r in FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS[:limit]]
        source = "fallback_static"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "criteria": (
            "Halal-aware keyword screen on yfinance sector/industry; excludes defense/military, "
            "alcohol, tobacco, gambling, adult, pork-forward names, and typical banks/insurers. "
            "Ranks by EBITDA margin and revenue/earnings growth fields from yfinance (verify in filings)."
        ),
        "universe_size": len(universe),
        "rows": rows_out,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fundamental_hot_picks.json")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=TECH_ROOT / "visualizations_output" / "fundamental_hot_picks.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=22,
        help="Max rows to keep (default 22)",
    )
    args = parser.parse_args()
    try:
        import yfinance  # noqa: F401
    except ImportError:
        print(
            "Warning: yfinance not installed; writing static fallback rows only. "
            "Install: pip install -r technical/requirements.txt",
            file=sys.stderr,
        )
        data = run_screen(limit=args.limit, skip_fetch=True)
    else:
        data = run_screen(limit=args.limit, skip_fetch=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    src = data.get("source", "")
    print(f"Wrote {len(data['rows'])} rows to {args.output} ({src})")


if __name__ == "__main__":
    main()
