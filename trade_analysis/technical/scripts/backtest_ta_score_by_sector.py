#!/usr/bin/env python3
"""
Sector backtest: does our TA composite / display Tech score predict forward returns?

For each sector (liquid tickers from configuration.json):
  - Download ~4y daily OHLCV
  - Every 4 weeks, score trailing data on 1W + 1M using improved_scoring
  - Map raw avg to 0–10 Tech (same formula as index_tech_score display base)
  - Bucket High (≥6.5) / Mid / Low (≤4.0)
  - Measure 4-week and 12-week forward returns

Usage (from trade_analysis/technical):
  ../.venv/bin/python scripts/backtest_ta_score_by_sector.py
  ../.venv/bin/python scripts/backtest_ta_score_by_sector.py --sectors ai_semiconductors,healthcare,gold_miners
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

TECH = Path(__file__).resolve().parents[1]
if str(TECH) not in sys.path:
    sys.path.insert(0, str(TECH))

from result_score_access import tech_score_to_display  # noqa: E402
from scoring.improved_scoring import improved_scoring  # noqa: E402

# Liquid / representative names per niche (avoid illiquid microcaps).
SECTOR_BASKETS: Dict[str, List[str]] = {
    "ai_semiconductors": ["SMH", "SOXX", "NVDA", "AMD", "AVGO", "TSM"],
    "faang_hot_stocks": ["QQQ", "XLK", "AAPL", "MSFT", "GOOGL", "META"],
    "healthcare": ["XLV", "UNH", "ISRG", "ABT", "MDT", "SYK"],
    "gold_miners": ["GDX", "GDXJ", "AEM", "KGC", "FNV", "AGI"],
    "precious_metals": ["GLD", "SLV", "IAU"],
    "energy_commodities": ["XLE", "USO", "XOM", "CVX"],
    "cryptocurrencies": ["IBIT", "MSTR", "COIN"],
    "real_estate": ["VNQ", "XLRE", "O", "WELL"],
    "renewable_energy": ["TAN", "ICLN", "ENPH", "FSLR", "NEE"],
    "industrial_metals": ["COPX", "FCX", "SCCO", "PICK"],
}

HIGH = 6.5
LOW = 4.0
REBALANCE_EVERY = 4  # weekly bars
FWD_WEEKS = (4, 12)


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    out = (
        df.resample(rule)
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna()
    )
    return out


def _raw_score(df_tf: pd.DataFrame, category: str, timeframe: str) -> Optional[float]:
    if df_tf is None or len(df_tf) < 55:
        return None
    try:
        res = improved_scoring(df_tf.copy(), category=category, timeframe=timeframe)
        sc = res.get("score")
        return float(sc) if sc is not None else None
    except Exception:
        return None


def _tech_at(
    daily: pd.DataFrame,
    asof: pd.Timestamp,
    category: str,
) -> Optional[float]:
    hist = daily.loc[:asof]
    if len(hist) < 120:
        return None
    w = _resample(hist, "W")
    m = _resample(hist, "ME")
    scores: List[float] = []
    for frame, tf in ((w, "1W"), (m, "1M")):
        if frame is None or len(frame) < 55:
            continue
        sc = _raw_score(frame.iloc[:-1] if len(frame) > 55 else frame, category, tf)
        # Use last complete bar in frame that ends on/before asof
        if sc is None:
            sc = _raw_score(frame, category, tf)
        if sc is not None:
            scores.append(sc)
    if not scores:
        return None
    return tech_score_to_display(sum(scores) / len(scores))


def _download(symbol: str, period: str = "4y") -> Optional[pd.DataFrame]:
    try:
        import yfinance as yf

        df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.title)
        need = {"Open", "High", "Low", "Close", "Volume"}
        if not need.issubset(set(df.columns)):
            return None
        return df[list(need)].dropna()
    except Exception:
        return None


def backtest_symbol(symbol: str, category: str) -> List[Dict[str, Any]]:
    daily = _download(symbol)
    if daily is None or len(daily) < 200:
        return []
    weekly = _resample(daily, "W")
    if len(weekly) < 80:
        return []

    rows: List[Dict[str, Any]] = []
    # Start after enough history; step every REBALANCE_EVERY weeks
    for i in range(60, len(weekly) - max(FWD_WEEKS) - 1, REBALANCE_EVERY):
        asof = weekly.index[i]
        tech = _tech_at(daily, asof, category)
        if tech is None:
            continue
        entry = float(weekly["Close"].iloc[i])
        if entry <= 0:
            continue
        rec: Dict[str, Any] = {"symbol": symbol, "category": category, "date": asof, "tech": tech}
        ok = True
        for w in FWD_WEEKS:
            j = i + w
            if j >= len(weekly):
                ok = False
                break
            fwd = (float(weekly["Close"].iloc[j]) / entry - 1.0) * 100.0
            rec[f"fwd_{w}w"] = fwd
        if ok:
            rows.append(rec)
    return rows


def _bucket(tech: float) -> str:
    if tech >= HIGH:
        return "high"
    if tech <= LOW:
        return "low"
    return "mid"


def summarize(rows: List[Dict[str, Any]], *, use_terciles: bool = False) -> Dict[str, Any]:
    by_b: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if use_terciles and rows:
        scores = sorted(r["tech"] for r in rows)
        t1 = scores[len(scores) // 3]
        t2 = scores[(2 * len(scores)) // 3]
        for r in rows:
            if r["tech"] >= t2:
                by_b["high"].append(r)
            elif r["tech"] <= t1:
                by_b["low"].append(r)
            else:
                by_b["mid"].append(r)
        out_meta = {"mode": "tercile", "t1": t1, "t2": t2}
    else:
        for r in rows:
            by_b[_bucket(r["tech"])].append(r)
        out_meta = {"mode": "fixed", "high": HIGH, "low": LOW}

    out: Dict[str, Any] = {"n": len(rows), **out_meta}
    for b in ("high", "mid", "low"):
        xs = by_b.get(b, [])
        out[b] = {"n": len(xs)}
        for w in FWD_WEEKS:
            key = f"fwd_{w}w"
            vals = [x[key] for x in xs if key in x]
            if vals:
                out[b][key] = {
                    "avg": sum(vals) / len(vals),
                    "win": 100.0 * sum(1 for v in vals if v > 0) / len(vals),
                }
            else:
                out[b][key] = None
    for w in FWD_WEEKS:
        key = f"fwd_{w}w"
        h = out["high"].get(key)
        l = out["low"].get(key)
        if h and l:
            out[f"spread_{w}w"] = h["avg"] - l["avg"]
        else:
            out[f"spread_{w}w"] = None
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtest TA Tech score by sector")
    parser.add_argument(
        "--sectors",
        type=str,
        default=",".join(SECTOR_BASKETS.keys()),
        help="Comma-separated sector keys",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(TECH / "result_scores" / "ta_score_sector_backtest.json"),
        help="JSON output path",
    )
    args = parser.parse_args()
    sectors = [s.strip() for s in args.sectors.split(",") if s.strip()]

    all_rows: List[Dict[str, Any]] = []
    sector_sum: Dict[str, Any] = {}

    print("TA Tech-score sector backtest")
    print(f"  Fixed buckets: High Tech≥{HIGH} · Low Tech≤{LOW} (plus terciles for fair compare)")
    print(f"  Rebalance every {REBALANCE_EVERY} weeks · Forward {FWD_WEEKS} weeks\n")

    for cat in sectors:
        tickers = SECTOR_BASKETS.get(cat)
        if not tickers:
            print(f"  skip {cat}: no basket")
            continue
        print(f"▸ {cat} ({', '.join(tickers)})")
        cat_rows: List[Dict[str, Any]] = []
        for sym in tickers:
            rows = backtest_symbol(sym, cat)
            print(f"    {sym}: {len(rows)} signals")
            cat_rows.extend(rows)
        all_rows.extend(cat_rows)
        fixed = summarize(cat_rows, use_terciles=False)
        terc = summarize(cat_rows, use_terciles=True)
        sector_sum[cat] = {"fixed": fixed, "tercile": terc}
        print("  [tercile High/Mid/Low]")
        _print_sector(cat, terc)

    overall_t = summarize(all_rows, use_terciles=True)
    overall_f = summarize(all_rows, use_terciles=False)
    print("═" * 72)
    print("OVERALL — terciles (balanced sample)")
    _print_sector("ALL SECTORS", overall_t)
    print("OVERALL — fixed High≥6.5 / Low≤4.0")
    _print_sector("ALL SECTORS", overall_f)

    payload = {
        "high_threshold": HIGH,
        "low_threshold": LOW,
        "fwd_weeks": list(FWD_WEEKS),
        "rebalance_every_weeks": REBALANCE_EVERY,
        "sectors": sector_sum,
        "overall_tercile": overall_t,
        "overall_fixed": overall_f,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


def _print_sector(name: str, s: Dict[str, Any]) -> None:
    extra = ""
    if s.get("mode") == "tercile":
        extra = f" (cuts ≤{s.get('t1'):.1f} / ≥{s.get('t2'):.1f})"
    print(f"  {name}: n={s.get('n', 0)}{extra}")
    for b, label in (("high", "High"), ("mid", "Mid"), ("low", "Low")):
        bucket = s.get(b) or {}
        parts = [f"n={bucket.get('n', 0)}"]
        for w in FWD_WEEKS:
            cell = bucket.get(f"fwd_{w}w")
            if cell:
                parts.append(f"{w}w avg {cell['avg']:+.1f}% win {cell['win']:.0f}%")
            else:
                parts.append(f"{w}w —")
        print(f"    {label:4s}: " + " · ".join(parts))
    for w in FWD_WEEKS:
        sp = s.get(f"spread_{w}w")
        if sp is not None:
            verdict = "High>Low ✓" if sp > 0 else "High≤Low ✗"
            print(f"    spread High−Low @ {w}w: {sp:+.1f}%  ({verdict})")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
