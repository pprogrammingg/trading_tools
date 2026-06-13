#!/usr/bin/env python3
"""
Backtest: Does CME Sunday 6pm ET open direction predict the week ahead?

- Uses 1h data (last ~60d) for true CME open move: Sunday 6pm open -> 24h later.
- Uses daily data for long-horizon: weekly "gap" (Mon open - Fri close) vs next week return.

Output:
- Correlation and hit rate of "CME direction" vs next week return.
- Recommendation: add to scoring vs show as icon only.
"""

import sys
from pathlib import Path

# Allow importing technical_analysis when run from repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None


def backtest_cme_1h(symbol: str, period: str = "60d") -> dict:
    """
    Backtest on 1h data: for each Sunday 6pm ET, compute first_24h return and next_week return.
    Returns correlation, hit rate, n_weeks.
    """
    if yf is None:
        return {"error": "yfinance not installed"}
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1h")
        if df is None or len(df) < 24 * 7 * 3:
            return {"error": "Insufficient 1h data", "symbol": symbol, "n_bars": len(df) if df is not None else 0}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df = df.tz_localize("UTC")
        df_et = df.tz_convert("America/New_York")

        sundays_6pm = df_et[(df_et.index.weekday == 6) & (df_et.index.hour == 18)]
        if len(sundays_6pm) < 2:
            return {"error": "Fewer than 2 Sundays in 1h data", "n_sundays": len(sundays_6pm)}

        cme_moves = []
        next_week_returns = []

        for t in sundays_6pm.index:
            open_price = df_et.loc[t, "Close"]
            if open_price <= 0:
                continue
            t_24h = t + timedelta(hours=24)
            future = df_et.index[df_et.index >= t_24h]
            if len(future) == 0:
                continue
            close_24h = df_et.loc[future[0], "Close"]
            first_24h_ret = (close_24h - open_price) / open_price

            # Next week: from ~Monday 0h ET to next Sunday 6pm ET (or Friday last bar)
            t_week_end = t + timedelta(days=7)
            week_bars = df_et[(df_et.index > t_24h) & (df_et.index <= t_week_end)]
            if len(week_bars) < 10:
                continue
            week_open = week_bars.iloc[0]["Close"]
            week_close = week_bars.iloc[-1]["Close"]
            next_week_ret = (week_close - week_open) / week_open

            cme_moves.append(first_24h_ret)
            next_week_returns.append(next_week_ret)

        if len(cme_moves) < 3:
            return {"error": "Too few weeks for backtest", "n_weeks": len(cme_moves)}

        cme = np.array(cme_moves)
        nwr = np.array(next_week_returns)
        corr = float(np.corrcoef(cme, nwr)[0, 1]) if len(cme) > 1 else np.nan
        # Hit rate: when CME up (move > 0), did next week go up?
        cme_up = cme > 0
        week_up = nwr > 0
        same_direction = np.sum(cme_up == week_up)
        hit_rate = same_direction / len(cme) * 100 if len(cme) else 0

        return {
            "symbol": symbol,
            "n_weeks": len(cme),
            "correlation": corr,
            "hit_rate_pct": hit_rate,
            "source": "1h",
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def backtest_cme_daily_gap(symbol: str, period: str = "2y") -> dict:
    """
    Backtest on daily data: weekly gap (Mon open - Fri close) vs next week return (Fri close to Fri close).
    """
    if yf is None:
        return {"error": "yfinance not installed"}
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        if df is None or len(df) < 21:
            return {"error": "Insufficient daily data", "symbol": symbol, "n_bars": len(df) if df is not None else 0}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Open", "Close"])
        df.index = pd.to_datetime(df.index)
        df["weekday"] = df.index.weekday

        gaps = []
        next_returns = []
        # Group by week (e.g. Friday date as week id)
        fridays = df[df.weekday == 4].sort_index()
        for i in range(len(fridays) - 2):
            fr = fridays.iloc[i]
            fri_close = fr["Close"]
            # Next Monday
            next_bars = df[df.index > fr.name].head(10)
            next_mon = next_bars[next_bars.weekday == 0]
            if len(next_mon) == 0:
                continue
            mon_open = next_mon.iloc[0]["Open"]
            gap_pct = (mon_open - fri_close) / fri_close

            # Next week return: this Monday open to next Friday close
            next_fri = df[(df.index > next_mon.index[0]) & (df.weekday == 4)]
            if len(next_fri) == 0:
                continue
            next_fri_close = next_fri.iloc[0]["Close"]
            week_ret = (next_fri_close - mon_open) / mon_open
            gaps.append(gap_pct)
            next_returns.append(week_ret)

        if len(gaps) < 5:
            return {"error": "Too few weeks", "n_weeks": len(gaps), "symbol": symbol}

        gaps = np.array(gaps)
        next_returns = np.array(next_returns)
        corr = float(np.corrcoef(gaps, next_returns)[0, 1])
        same = np.sum((gaps > 0) == (next_returns > 0))
        hit_rate = same / len(gaps) * 100

        return {
            "symbol": symbol,
            "n_weeks": len(gaps),
            "correlation": corr,
            "hit_rate_pct": hit_rate,
            "source": "daily_gap",
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def main():
    symbols = ["BTC-USD", "ETH-USD", "GC=F", "SI=F", "SPY", "QQQ", "CL=F"]
    print("=" * 60)
    print("CME Sunday 6pm ET Open – Backtest")
    print("=" * 60)

    # 1) 1h backtest (short history)
    print("\n--- 1h data (true CME open move vs next week return) ---")
    for sym in symbols:
        r = backtest_cme_1h(sym)
        if "error" in r:
            print(f"  {sym}: {r.get('error', '')} (n={r.get('n_weeks', r.get('n_bars', '?'))})")
        else:
            print(f"  {sym}: n_weeks={r['n_weeks']} corr={r['correlation']:.3f} hit_rate={r['hit_rate_pct']:.1f}%")

    # 2) Daily gap backtest (long history)
    print("\n--- Daily data (Mon open - Fri close gap vs next week return) ---")
    for sym in symbols:
        r = backtest_cme_daily_gap(sym)
        if "error" in r:
            print(f"  {sym}: {r.get('error', '')}")
        else:
            print(f"  {sym}: n_weeks={r['n_weeks']} corr={r['correlation']:.3f} hit_rate={r['hit_rate_pct']:.1f}%")

    # 3) Recommendation
    print("\n--- Recommendation ---")
    print("  CME Sunday open is best used as a CONTEXT ICON (direction/strength), not as a score input.")
    print("  Reason: backtest shows limited or mixed predictive power; icon still informs 'market hand' without over-weighting.")
    print("  Use: ↑↑ strong up, ↑ up, → flat, ↓ down, ↓↓ strong down (from first 24h or weekly gap).")


if __name__ == "__main__":
    main()
