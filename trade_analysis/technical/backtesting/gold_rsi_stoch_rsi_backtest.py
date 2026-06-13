#!/usr/bin/env python3
"""
Gold (GC=F) RSI + Stoch RSI backtest: $100 per trade.
Uses shared RSI/Stoch RSI logic from scripts.rsi_stochrsi_common.

Rules:
- ENTRY: RSI < rsi_oversold_threshold AND Stoch RSI %K crosses UP from below stoch_bottom (e.g. 20).
- EXIT: Stoch RSI %K crosses DOWN from above stoch_top (e.g. 80).

Timeframes: 4H, 1D, 2D, 3D, 1W, 2W, 1M.
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, message=".*fillna.*")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# Re-use common RSI/Stoch RSI logic
from scripts.rsi_stochrsi_common import (
    get_ohlcv_for_timeframe,
    compute_rsi,
    compute_stoch_rsi,
    RSI_PERIOD,
    STOCH_K,
    STOCH_D,
    STOCH_PERIOD,
)

SYMBOL = "GC=F"
DOLLAR_PER_TRADE = 100.0


def _stoch_pct(stoch_k):
    """Stoch RSI 0-1 -> 0-100 for threshold comparison."""
    if stoch_k is None or len(stoch_k) == 0:
        return None
    return (stoch_k * 100.0) if stoch_k.max() <= 1.0 else stoch_k


def cross_up(series: pd.Series, threshold: float) -> pd.Series:
    """True where series crosses above threshold."""
    if series is None or len(series) < 2:
        return pd.Series(dtype=bool)
    above = (series > threshold).astype(bool)
    prev = above.shift(1)
    return above & ~prev.fillna(False).astype(bool)


def cross_down(series: pd.Series, threshold: float) -> pd.Series:
    """True where series crosses below threshold."""
    if series is None or len(series) < 2:
        return pd.Series(dtype=bool)
    below = (series < threshold).astype(bool)
    prev = below.shift(1)
    return below & ~prev.fillna(False).astype(bool)


def run_backtest(
    df: pd.DataFrame,
    rsi_oversold: float = 35.0,
    stoch_bottom: float = 20.0,
    stoch_top: float = 80.0,
) -> dict:
    """
    Backtest: entry when RSI < rsi_oversold and Stoch %K crosses up through stoch_bottom;
    exit when Stoch %K crosses down through stoch_top. $100 per entry.
    """
    close = df["Close"]
    rsi = compute_rsi(close)
    stoch_k, stoch_d = compute_stoch_rsi(close)
    if rsi is None or stoch_k is None:
        return {"trades": 0, "pnl": 0.0, "entries": [], "exits": [], "rsi_oversold": rsi_oversold, "stoch_bottom": stoch_bottom, "stoch_top": stoch_top}

    stoch_k_pct = _stoch_pct(stoch_k)
    entry_signal = (cross_up(stoch_k_pct, stoch_bottom) & (rsi < rsi_oversold)).reindex(df.index).fillna(False).astype(bool)
    exit_signal = cross_down(stoch_k_pct, stoch_top).reindex(df.index).fillna(False).astype(bool)

    entries, exits = [], []
    position = None
    pnl = 0.0

    for ts in df.index:
        if ts not in close.index or ts not in entry_signal.index or ts not in exit_signal.index:
            continue
        price = float(close.loc[ts])
        if pd.isna(price) or price <= 0:
            continue
        if entry_signal.loc[ts] and position is None:
            shares = DOLLAR_PER_TRADE / price
            position = {"shares": shares, "entry_price": price, "entry_time": ts}
            entries.append({"time": ts, "price": price, "shares": position["shares"]})
        elif exit_signal.loc[ts] and position is not None:
            trade_pnl = position["shares"] * (price - position["entry_price"])
            pnl += trade_pnl
            exits.append({"time": ts, "price": price, "entry_price": position["entry_price"], "pnl": trade_pnl})
            position = None

    if position is not None:
        last_ts = close.index[-1]
        last_price = float(close.loc[last_ts])
        open_pnl = position["shares"] * (last_price - position["entry_price"])
        pnl += open_pnl
        exits.append({"time": last_ts, "price": last_price, "entry_price": position["entry_price"], "pnl": open_pnl, "open": True})

    return {
        "trades": len(entries),
        "pnl": pnl,
        "entries": entries,
        "exits": exits,
        "rsi_oversold": rsi_oversold,
        "stoch_bottom": stoch_bottom,
        "stoch_top": stoch_top,
    }


def main():
    timeframes = ["4H", "1D", "2D", "3D", "1W", "2W", "1M"]
    rsi_thresholds = [30, 35, 40]
    stoch_bottoms = [10, 20, 30]
    stoch_tops = [70, 80, 90]

    print("=" * 80)
    print("GOLD (GC=F) RSI + Stoch RSI Backtest — $100 per trade")
    print("=" * 80)
    print("Entry: RSI < RSI_threshold AND Stoch RSI %K crosses UP from below stoch_bottom")
    print("Exit:  Stoch RSI %K crosses DOWN from above stoch_top")
    print()

    best_by_tf = {}
    for tf in timeframes:
        df = get_ohlcv_for_timeframe(SYMBOL, tf, category="precious_metals")
        if df is None or len(df) < 50:
            print(f"  {tf}: insufficient data — skip")
            continue
        best_pnl = -1e9
        best_params = None
        best_result = None
        for rsi_t in rsi_thresholds:
            for sb in stoch_bottoms:
                for st in stoch_tops:
                    res = run_backtest(df, rsi_oversold=rsi_t, stoch_bottom=sb, stoch_top=st)
                    if res["trades"] >= 2 and res["pnl"] > best_pnl:
                        best_pnl = res["pnl"]
                        best_params = (rsi_t, sb, st)
                        best_result = res
        if best_result is None:
            best_result = run_backtest(df, rsi_oversold=35, stoch_bottom=20, stoch_top=80)
            best_params = (35, 20, 80)
        best_by_tf[tf] = {"result": best_result, "params": best_params}

    print("\nRecommended thresholds (best PnL with ≥2 trades):")
    print("-" * 80)
    print(f"  {'TF':<6} {'RSI_oversold':<14} {'Stoch_bottom':<14} {'Stoch_top':<10} {'Trades':<8} {'PnL ($)':<12}")
    print("-" * 80)
    for tf in timeframes:
        if tf not in best_by_tf:
            continue
        r = best_by_tf[tf]["result"]
        rsi_t, sb, st = best_by_tf[tf]["params"]
        print(f"  {tf:<6} {rsi_t:<14} {sb:<14} {st:<10} {r['trades']:<8} {r['pnl']:+.2f}")
    print("-" * 80)

    print("\nSuggested single combo for manual use:")
    if "1W" in best_by_tf:
        rsi_t, sb, st = best_by_tf["1W"]["params"]
        print(f"  RSI oversold threshold: {rsi_t} (buy when RSI < {rsi_t})")
        print(f"  Stoch RSI cross-up from below: {sb} (enter when %K crosses up through {sb})")
        print(f"  Stoch RSI cross-down from above: {st} (take profit when %K crosses down through {st})")
    else:
        print("  RSI oversold: 35 | Stoch bottom: 20 | Stoch top: 80 (defaults)")

    print("\n--- 1W detailed (sample entries/exits) ---")
    df1w = get_ohlcv_for_timeframe(SYMBOL, "1W", category="precious_metals")
    if df1w is not None:
        rsi_t, sb, st = best_by_tf.get("1W", {"params": (35, 20, 80)})["params"]
        res = run_backtest(df1w, rsi_oversold=rsi_t, stoch_bottom=sb, stoch_top=st)
        for i, e in enumerate(res["entries"][:5]):
            print(f"  Entry {i+1}: {e['time'].strftime('%Y-%m-%d')} @ ${e['price']:.2f} ({e['shares']:.4f} shares)")
        for i, x in enumerate(res["exits"][:5]):
            print(f"  Exit  {i+1}: {x['time'].strftime('%Y-%m-%d')} @ ${x['price']:.2f} PnL ${x['pnl']:.2f}")
        print(f"  Total trades: {res['trades']} | Total PnL: ${res['pnl']:.2f}")


if __name__ == "__main__":
    main()
