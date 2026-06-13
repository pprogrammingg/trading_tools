#!/usr/bin/env python3
"""
Backtest Super Guppy orange_reversal signal for BTC across timeframes.

Tests:
1. When orange_reversal appears at bottoms → does it predict double bottoms / reversals?
2. When orange_reversal does NOT appear at bottoms → does that mean continued decline?

For BTC across: 4H, 1D, 2D, 1W, 2W, 1M timeframes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

try:
    from indicators.super_guppy import get_super_guppy_state
except ImportError:
    try:
        from technical_analysis.indicators.super_guppy import get_super_guppy_state
    except ImportError:
        print("Error: Could not import get_super_guppy_state")
        sys.exit(1)


def resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample daily data to specified timeframe."""
    if timeframe == "4H":
        return df.resample("4h").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
    elif timeframe == "1D":
        return df
    elif timeframe == "2D":
        return df.resample("2D").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
    elif timeframe == "1W":
        return df.resample("W").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
    elif timeframe == "2W":
        return df.resample("2W").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
    elif timeframe == "1M":
        return df.resample("ME").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()
    return df


def identify_bottoms(close: pd.Series, lookback: int = 20, threshold_pct: float = 8.0) -> pd.Series:
    """Identify bottoms: price within threshold_pct% of lookback-period low."""
    bottoms = pd.Series(False, index=close.index)
    for i in range(lookback, len(close)):
        window = close.iloc[i - lookback:i]
        window_low = window.min()
        current_price = close.iloc[i]
        if current_price <= window_low * (1 + threshold_pct / 100):
            bottoms.iloc[i] = True
    return bottoms


def backtest_super_guppy_btc(timeframe: str, period: str = "5y") -> dict:
    """
    Backtest Super Guppy orange_reversal at bottoms for BTC on given timeframe.
    
    Returns:
        dict with stats: n_bottoms, n_with_orange, n_without_orange,
        orange_forward_ret_1w, orange_forward_ret_2w, orange_forward_ret_1m,
        no_orange_forward_ret_1w, etc., hit_rates, etc.
    """
    print(f"\n--- Testing {timeframe} ---")
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(period=period, interval="1d")
    if df is None or len(df) < 100:
        return {"error": "Insufficient data"}
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    df.index = pd.to_datetime(df.index)

    df_tf = resample_to_timeframe(df, timeframe)
    if len(df_tf) < 100:
        return {"error": f"Insufficient data after resampling to {timeframe}"}

    close = df_tf['close']
    bottoms = identify_bottoms(close, lookback=20, threshold_pct=8.0)

    # For each bottom, get Super Guppy state and forward returns
    orange_at_bottom = []
    no_orange_at_bottom = []
    orange_forward_1w = []
    orange_forward_2w = []
    orange_forward_1m = []
    no_orange_forward_1w = []
    no_orange_forward_2w = []
    no_orange_forward_1m = []

    # Convert timeframe to forward periods (approximate)
    bars_1w = {"4H": 42, "1D": 7, "2D": 3.5, "1W": 1, "2W": 0.5, "1M": 0.25}
    bars_2w = {"4H": 84, "1D": 14, "2D": 7, "1W": 2, "2W": 1, "1M": 0.5}
    bars_1m = {"4H": 180, "1D": 30, "2D": 15, "1W": 4, "2W": 2, "1M": 1}

    for i in range(60, len(close) - max(int(bars_1m.get(timeframe, 30)), 30)):
        if not bottoms.iloc[i]:
            continue

        # Get Super Guppy state at this bottom
        close_window = close.iloc[:i + 1]
        if len(close_window) < 60:
            continue

        try:
            guppy = get_super_guppy_state(close_window)
            state = guppy.get('state', 'unknown')
        except Exception as e:
            continue

        current_price = close.iloc[i]

        # Forward returns
        idx_1w = min(i + int(bars_1w.get(timeframe, 7)), len(close) - 1)
        idx_2w = min(i + int(bars_2w.get(timeframe, 14)), len(close) - 1)
        idx_1m = min(i + int(bars_1m.get(timeframe, 30)), len(close) - 1)

        forward_1w = (close.iloc[idx_1w] / current_price - 1) * 100 if idx_1w > i else None
        forward_2w = (close.iloc[idx_2w] / current_price - 1) * 100 if idx_2w > i else None
        forward_1m = (close.iloc[idx_1m] / current_price - 1) * 100 if idx_1m > i else None

        if state == 'orange_reversal':
            orange_at_bottom.append(i)
            if forward_1w is not None:
                orange_forward_1w.append(forward_1w)
            if forward_2w is not None:
                orange_forward_2w.append(forward_2w)
            if forward_1m is not None:
                orange_forward_1m.append(forward_1m)
        else:
            no_orange_at_bottom.append(i)
            if forward_1w is not None:
                no_orange_forward_1w.append(forward_1w)
            if forward_2w is not None:
                no_orange_forward_2w.append(forward_2w)
            if forward_1m is not None:
                no_orange_forward_1m.append(forward_1m)

    n_bottoms = len(orange_at_bottom) + len(no_orange_at_bottom)
    n_with_orange = len(orange_at_bottom)
    n_without_orange = len(no_orange_at_bottom)

    result = {
        "timeframe": timeframe,
        "n_bottoms": n_bottoms,
        "n_with_orange": n_with_orange,
        "n_without_orange": n_without_orange,
        "orange_pct": (n_with_orange / n_bottoms * 100) if n_bottoms > 0 else 0,
    }

    # Forward returns: orange vs no orange
    if orange_forward_1w:
        result["orange_avg_ret_1w"] = float(np.mean(orange_forward_1w))
        result["orange_win_rate_1w"] = (np.array(orange_forward_1w) > 0).sum() / len(orange_forward_1w) * 100
    if orange_forward_2w:
        result["orange_avg_ret_2w"] = float(np.mean(orange_forward_2w))
        result["orange_win_rate_2w"] = (np.array(orange_forward_2w) > 0).sum() / len(orange_forward_2w) * 100
    if orange_forward_1m:
        result["orange_avg_ret_1m"] = float(np.mean(orange_forward_1m))
        result["orange_win_rate_1m"] = (np.array(orange_forward_1m) > 0).sum() / len(orange_forward_1m) * 100

    if no_orange_forward_1w:
        result["no_orange_avg_ret_1w"] = float(np.mean(no_orange_forward_1w))
        result["no_orange_win_rate_1w"] = (np.array(no_orange_forward_1w) > 0).sum() / len(no_orange_forward_1w) * 100
    if no_orange_forward_2w:
        result["no_orange_avg_ret_2w"] = float(np.mean(no_orange_forward_2w))
        result["no_orange_win_rate_2w"] = (np.array(no_orange_forward_2w) > 0).sum() / len(no_orange_forward_2w) * 100
    if no_orange_forward_1m:
        result["no_orange_avg_ret_1m"] = float(np.mean(no_orange_forward_1m))
        result["no_orange_win_rate_1m"] = (np.array(no_orange_forward_1m) > 0).sum() / len(no_orange_forward_1m) * 100

    return result


def main():
    print("=" * 70)
    print("Super Guppy Orange Reversal Backtest - BTC")
    print("=" * 70)
    print("\nTesting: When orange_reversal appears at bottoms vs when it doesn't")
    print("Forward returns: 1 week, 2 weeks, 1 month")

    timeframes = ["4H", "1D", "2D", "1W", "2W", "1M"]
    results = []

    for tf in timeframes:
        r = backtest_super_guppy_btc(tf, period="5y")
        if "error" not in r:
            results.append(r)

    # Print summary table
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'TF':<6} {'Bottoms':<8} {'Orange':<8} {'%':<6} {'Orange 1W':<12} {'No Orange 1W':<14} {'Orange 2W':<12} {'No Orange 2W':<14}")
    print("-" * 70)

    for r in results:
        tf = r.get("timeframe", "?")
        n_b = r.get("n_bottoms", 0)
        n_o = r.get("n_with_orange", 0)
        pct = r.get("orange_pct", 0)
        o1w = r.get("orange_avg_ret_1w", None)
        no1w = r.get("no_orange_avg_ret_1w", None)
        o2w = r.get("orange_avg_ret_2w", None)
        no2w = r.get("no_orange_avg_ret_2w", None)

        o1w_str = f"{o1w:+.1f}%" if o1w is not None else "N/A"
        no1w_str = f"{no1w:+.1f}%" if no1w is not None else "N/A"
        o2w_str = f"{o2w:+.1f}%" if o2w is not None else "N/A"
        no2w_str = f"{no2w:+.1f}%" if no2w is not None else "N/A"

        print(f"{tf:<6} {n_b:<8} {n_o:<8} {pct:<5.1f}% {o1w_str:<12} {no1w_str:<14} {o2w_str:<12} {no2w_str:<14}")

    # Detailed analysis
    print("\n" + "=" * 70)
    print("DETAILED ANALYSIS")
    print("=" * 70)
    for r in results:
        tf = r.get("timeframe", "?")
        print(f"\n{tf}:")
        print(f"  Bottoms found: {r.get('n_bottoms', 0)}")
        print(f"  With orange_reversal: {r.get('n_with_orange', 0)} ({r.get('orange_pct', 0):.1f}%)")
        print(f"  Without orange: {r.get('n_without_orange', 0)}")

        if r.get("orange_avg_ret_1w") is not None:
            print(f"  Orange → 1W: avg {r['orange_avg_ret_1w']:+.2f}%, win rate {r.get('orange_win_rate_1w', 0):.1f}%")
        if r.get("no_orange_avg_ret_1w") is not None:
            print(f"  No orange → 1W: avg {r['no_orange_avg_ret_1w']:+.2f}%, win rate {r.get('no_orange_win_rate_1w', 0):.1f}%")

        if r.get("orange_avg_ret_2w") is not None:
            print(f"  Orange → 2W: avg {r['orange_avg_ret_2w']:+.2f}%, win rate {r.get('orange_win_rate_2w', 0):.1f}%")
        if r.get("no_orange_avg_ret_2w") is not None:
            print(f"  No orange → 2W: avg {r['no_orange_avg_ret_2w']:+.2f}%, win rate {r.get('no_orange_win_rate_2w', 0):.1f}%")

        if r.get("orange_avg_ret_1m") is not None:
            print(f"  Orange → 1M: avg {r['orange_avg_ret_1m']:+.2f}%, win rate {r.get('orange_win_rate_1m', 0):.1f}%")
        if r.get("no_orange_avg_ret_1m") is not None:
            print(f"  No orange → 1M: avg {r['no_orange_avg_ret_1m']:+.2f}%, win rate {r.get('no_orange_win_rate_1m', 0):.1f}%")

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("If orange_reversal at bottom → better forward returns: signal works.")
    print("If no orange at bottom → worse forward returns: absence is informative (no double bottom).")


if __name__ == "__main__":
    main()
