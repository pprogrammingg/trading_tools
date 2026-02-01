#!/usr/bin/env python3
"""
Backtest: Cup-and-handle breakout pattern across assets, timeframes, USD/Gold/Silver.
When a cup breakout is detected at bar T, measure forward return at T+1, T+3, T+6 bars.
Used to justify score bonus for recent_breakout in improved_scoring.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

from technical_analysis import download_data, resample_ohlcv
from indicators.cup_pattern import detect_cup_and_breakout


def _load_config():
    config_path = Path(__file__).resolve().parent.parent / "symbols_config.json"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return json.load(f)


def _convert_to_benchmark_terms(df: pd.DataFrame, bench_df: pd.DataFrame) -> pd.DataFrame:
    """Convert OHLC to benchmark terms (e.g. price / gold)."""
    if df.empty or bench_df.empty:
        return pd.DataFrame()
    bench_close = bench_df["Close"].reindex(df.index.union(bench_df.index)).ffill()
    aligned = df.reindex(bench_close.index).ffill()
    aligned = aligned.dropna(how="all")
    bench_close = bench_close.reindex(aligned.index).ffill()
    out = aligned.div(bench_close, axis=0)
    out["Volume"] = aligned.get("Volume", 0)
    return out.dropna(subset=["Close"])


def run_cup_backtest_one_series(
    close: pd.Series,
    lookback_rim: int = 40,
    min_cup_bars: int = 6,
    breakout_pct: float = 0.001,
    forward_bars: list = None,
):
    """
    For each bar T where we have enough history, check if T is a "breakout" bar;
    if so, record forward return over forward_bars.
    Returns list of {bar_idx, forward_1, forward_3, forward_6} (pct).
    """
    if forward_bars is None:
        forward_bars = [1, 3, 6]
    close = close.astype(float).dropna()
    if len(close) < lookback_rim + min_cup_bars + max(forward_bars) + 5:
        return []
    results = []
    for T in range(lookback_rim + min_cup_bars, len(close) - max(forward_bars)):
        hist = close.iloc[: T + 1]
        out = detect_cup_and_breakout(hist, lookback_rim=lookback_rim, min_cup_bars=min_cup_bars, breakout_pct=breakout_pct, recent_bars=3)
        if not out or not out.get("cup_breakout"):
            continue
        # Breakout at T; get forward returns
        p0 = close.iloc[T]
        fwd = {}
        for b in forward_bars:
            if T + b < len(close):
                fwd[f"forward_{b}"] = (close.iloc[T + b] - p0) / p0 * 100
        if fwd:
            results.append({"bar_idx": T, "price_at_T": p0, **fwd})
    return results


def backtest_cup_pattern(
    symbols_by_category: dict,
    timeframes: dict = None,
    period: str = "5y",
):
    """
    Backtest cup breakout across categories. For each symbol load USD (and gold/silver if available),
    resample to each TF, run cup backtest on close series. Aggregate win rate and avg forward return.
    """
    if timeframes is None:
        timeframes = {"1W": "7D", "2W": "14D", "1M": "30D"}
    gold_df = download_data("GC=F", period=period, category="gold", use_cache=True, force_refresh=False)
    silver_df = download_data("SI=F", period=period, category="precious_metals", use_cache=True, force_refresh=False)
    gold_df = gold_df if gold_df is not None and len(gold_df) > 0 else None
    silver_df = silver_df if silver_df is not None and len(silver_df) > 0 else None

    agg = defaultdict(list)
    for category, symbols in symbols_by_category.items():
        for symbol in symbols[:8]:  # Limit per category for speed
            try:
                df = download_data(symbol, period=period, category=category, use_cache=True, force_refresh=False)
                if df is None or len(df) < 100:
                    continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                for tf_label, rule in timeframes.items():
                    resampled = resample_ohlcv(df, rule)
                    if resampled is None or len(resampled) < 50:
                        continue
                    lookback = {"1W": 52, "2W": 40, "1M": 24}.get(tf_label, 40)
                    rows = run_cup_backtest_one_series(resampled["Close"], lookback_rim=lookback)
                    for r in rows:
                        r["symbol"] = symbol
                        r["category"] = category
                        r["timeframe"] = tf_label
                        r["denomination"] = "usd"
                    agg["usd"].extend(rows)
                    if gold_df is not None and symbol not in ("GC=F", "SI=F"):
                        df_g = _convert_to_benchmark_terms(resampled, gold_df)
                        if len(df_g) >= 50:
                            rows_g = run_cup_backtest_one_series(df_g["Close"], lookback_rim=lookback)
                            for r in rows_g:
                                r["symbol"], r["category"], r["timeframe"], r["denomination"] = symbol, category, tf_label, "gold"
                            agg["gold"].extend(rows_g)
                    if silver_df is not None and symbol not in ("GC=F", "SI=F"):
                        df_s = _convert_to_benchmark_terms(resampled, silver_df)
                        if len(df_s) >= 50:
                            rows_s = run_cup_backtest_one_series(df_s["Close"], lookback_rim=lookback)
                            for r in rows_s:
                                r["symbol"], r["category"], r["timeframe"], r["denomination"] = symbol, category, tf_label, "silver"
                            agg["silver"].extend(rows_s)
            except Exception as e:
                continue
    return dict(agg)


def summarize_backtest(agg: dict) -> dict:
    """Compute win rate and avg forward return by denomination and timeframe."""
    summary = {}
    for denom, rows in agg.items():
        if not rows:
            continue
        df = pd.DataFrame(rows)
        summary[denom] = {}
        for tf in df["timeframe"].unique():
            sub = df[df["timeframe"] == tf]
            f1 = sub.get("forward_1")
            f3 = sub.get("forward_3")
            f6 = sub.get("forward_6")
            summary[denom][tf] = {
                "n_breakouts": len(sub),
                "win_1": (f1 > 0).sum() / len(f1) * 100 if f1 is not None and len(f1) else None,
                "win_3": (f3 > 0).sum() / len(f3) * 100 if f3 is not None and len(f3) else None,
                "win_6": (f6 > 0).sum() / len(f6) * 100 if f6 is not None and len(f6) else None,
                "avg_1": f1.mean() if f1 is not None else None,
                "avg_3": f3.mean() if f3 is not None else None,
                "avg_6": f6.mean() if f6 is not None else None,
            }
    return summary


if __name__ == "__main__":
    config = _load_config()
    if not config:
        print("No symbols_config.json found")
        sys.exit(1)
    print("Running cup pattern backtest (sample of symbols per category)...")
    agg = backtest_cup_pattern(config)
    summary = summarize_backtest(agg)
    print("\nCup breakout forward returns (win % and avg %):")
    for denom, tfs in summary.items():
        print(f"  {denom}:")
        for tf, s in tfs.items():
            print(f"    {tf}: n={s['n_breakouts']}, win_1={s.get('win_1')}, win_3={s.get('win_3')}, avg_1={s.get('avg_1')}, avg_3={s.get('avg_3')}")
    print("\nRecommendation: add score bonus for recent_breakout (e.g. +0.5) when backtest win rate > 50%.")
