#!/usr/bin/env python3
"""
Backtest Elliott Wave count: does wave_position (Wave 2/4 vs Wave 3/5) predict forward returns?
Used to justify score adjustments (e.g. bonus for Wave 2/4 correction, bonus for Wave 3/5).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from collections import defaultdict

try:
    import yfinance as yf
except ImportError:
    yf = None

from technical_analysis import resample_ohlcv
from indicators.elliott_wave import identify_elliott_wave_pattern


def backtest_elliott_wave_one_series(
    close: pd.Series,
    lookback: int = 20,
    forward_bars: list = None,
) -> list:
    """
    For each bar T with enough history, get wave_position; record forward return.
    Returns list of {wave_position, forward_1, forward_3, forward_6}.
    """
    if forward_bars is None:
        forward_bars = [1, 3, 6]
    close = close.astype(float).dropna()
    max_fwd = max(forward_bars)
    if len(close) < lookback * 2 + max_fwd + 5:
        return []
    results = []
    for T in range(lookback * 2, len(close) - max_fwd):
        hist = close.iloc[: T + 1]
        out = identify_elliott_wave_pattern(hist, lookback=lookback)
        if not out:
            continue
        pos = out.get("wave_position") or ""
        p0 = close.iloc[T]
        row = {"wave_position": pos, "bar": T}
        for b in forward_bars:
            if T + b < len(close):
                row[f"forward_{b}"] = (close.iloc[T + b] - p0) / p0 * 100
        results.append(row)
    return results


def run_backtest(symbols: list = None, timeframes: dict = None, period: str = "5y"):
    """Run Elliott Wave backtest across symbols and timeframes. Aggregate by wave_position."""
    if symbols is None:
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "SPY", "GC=F"]
    if timeframes is None:
        timeframes = {"1W": "7D", "1M": "30D"}
    if yf is None:
        return {"error": "yfinance not installed"}

    agg = defaultdict(list)
    for symbol in symbols:
        try:
            df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=False)
            if df is None or len(df) < 100:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            for tf_label, rule in timeframes.items():
                resampled = resample_ohlcv(df, rule)
                if resampled is None or len(resampled) < 50:
                    continue
                lookback = 20 if tf_label == "1W" else 24
                rows = backtest_elliott_wave_one_series(resampled["Close"], lookback=lookback)
                for r in rows:
                    r["symbol"] = symbol
                    r["timeframe"] = tf_label
                for r in rows:
                    agg[r["wave_position"]].append(r)
        except Exception:
            continue

    # Summarize by wave_position
    summary = {}
    for pos, rows in agg.items():
        if not rows:
            continue
        df_r = pd.DataFrame(rows)
        f1 = df_r.get("forward_1")
        f3 = df_r.get("forward_3")
        f6 = df_r.get("forward_6")
        summary[pos] = {
            "n": len(rows),
            "win_1": (f1 > 0).sum() / len(f1) * 100 if f1 is not None and len(f1) else None,
            "win_3": (f3 > 0).sum() / len(f3) * 100 if f3 is not None and len(f3) else None,
            "win_6": (f6 > 0).sum() / len(f6) * 100 if f6 is not None and len(f6) else None,
            "avg_1": f1.mean() if f1 is not None else None,
            "avg_3": f3.mean() if f3 is not None else None,
            "avg_6": f6.mean() if f6 is not None else None,
        }
    return {"by_position": summary, "raw_counts": {k: len(v) for k, v in agg.items()}}


if __name__ == "__main__":
    print("Elliott Wave backtest: wave_position vs forward returns...")
    result = run_backtest()
    if "error" in result:
        print(result["error"])
        sys.exit(1)
    print("\nBy wave position (win % and avg forward return %):")
    for pos, s in result["by_position"].items():
        print(f"  {pos}: n={s['n']}, win_1={s.get('win_1')}, win_3={s.get('win_3')}, avg_1={s.get('avg_1')}, avg_3={s.get('avg_3')}")
    # Save results for scoring refinement
    out_path = Path(__file__).resolve().parent / "elliott_wave_backtest_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to {out_path.name}")
    print("Scoring: bonus Wave 3 or 5 (best forward returns); no bonus Wave 2/4; small bonus Wave 1.")
