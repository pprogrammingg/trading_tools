"""
CME Sunday 6 PM Eastern Open Indicator

On Sundays at 6:00 PM Eastern, CME opens trading for crypto futures (e.g. Bitcoin, Ether),
equity index futures (ES, NQ), and metals (gold, silver, copper). The direction and
strength of the move from that open can "reveal the market hand" for the week ahead.

This module:
- Computes the price at Sunday 6pm ET (CME open) and the move in the first 24h
- Returns direction (-1, 0, +1), strength (pct), and an icon label for display
- Supports proxy symbols: BTC-USD, ETH-USD, GC=F, SI=F, CL=F, SPY (spot/futures)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None

# Sunday 6pm Eastern = first CME open of the week
CME_OPEN_HOUR_ET = 18  # 6 PM
CME_OPEN_WEEKDAY = 6   # Sunday

# Strength thresholds for icon (pct move in first 24h)
THRESHOLD_STRONG_UP = 0.5
THRESHOLD_UP = 0.0
THRESHOLD_DOWN = -0.0
THRESHOLD_STRONG_DOWN = -0.5


def _ensure_tz_et(ts: pd.Timestamp) -> pd.Timestamp:
    """Ensure timestamp is in Eastern time."""
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC").tz_convert("America/New_York")
    else:
        ts = ts.tz_convert("America/New_York")
    return ts


def _sunday_6pm_et_in_utc(d: datetime) -> datetime:
    """Return Sunday 6pm ET for the week containing d, as naive UTC for comparison with yfinance."""
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from datetime import timezone
        ZoneInfo = lambda x: timezone.utc  # fallback
    et = ZoneInfo("America/New_York")
    # d in ET, find Sunday of that week (Sunday = start of week)
    d_et = d.astimezone(et) if d.tzinfo else pd.Timestamp(d, tz=et).to_pydatetime()
    # weekday: Monday=0, Sunday=6 -> go back to Sunday
    days_back = (d_et.weekday() + 1) % 7
    if days_back == 0:
        days_back = 7
    sunday = d_et - timedelta(days=days_back)
    sunday_6pm = sunday.replace(hour=18, minute=0, second=0, microsecond=0)
    return sunday_6pm.astimezone(datetime.now().astimezone().tzinfo or timezone.utc).replace(tzinfo=None)


def get_cme_sunday_open_from_1h(
    symbol: str,
    period: str = "60d",
    interval: str = "1h",
) -> Optional[Dict]:
    """
    Use 1h data to get CME Sunday 6pm ET open and first-24h move.
    yfinance 1h is typically limited to ~60d, so we get ~8 Sundays.

    Returns:
        dict with: cme_open, cme_close_24h, move_pct, direction (-1/0/1), strength_label, icon, n_weeks
        or None if insufficient data.
    """
    if yf is None:
        return None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or len(df) < 24 * 7 * 2:  # at least 2 weeks of hourly
            return None
        df = df.dropna(subset=["Close"])
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df = df.tz_localize("UTC")
        df_et = df.tz_convert("America/New_York")

        # Find all Sundays at 6pm ET (hour 18)
        sundays_6pm = df_et[(df_et.index.weekday == 6) & (df_et.index.hour == 18)]
        if len(sundays_6pm) == 0:
            return None

        # For each Sunday 6pm, get open and ~24h later (next day 6pm or last available)
        results = []
        for t in sundays_6pm.index:
            if t not in df_et.index:
                continue
            row = df_et.loc[t]
            open_price = row.get("Open", row.get("Close"))
            if open_price is None or open_price <= 0:
                continue
            t_24h = t + timedelta(hours=24)
            # get closest bar at or after t_24h
            future = df_et.index[df_et.index >= t_24h]
            if len(future) == 0:
                continue
            t_next = future[0]
            close_24h = df_et.loc[t_next, "Close"]
            move_pct = (close_24h - open_price) / open_price * 100
            results.append({"open": open_price, "close_24h": close_24h, "move_pct": move_pct, "ts": t})

        if not results:
            return None
        latest = results[-1]
        move = latest["move_pct"]
        if move >= THRESHOLD_STRONG_UP:
            direction, strength_label, icon = 1, "strong_up", "↑↑"
        elif move >= THRESHOLD_UP:
            direction, strength_label, icon = 1, "up", "↑"
        elif move <= THRESHOLD_STRONG_DOWN:
            direction, strength_label, icon = -1, "strong_down", "↓↓"
        elif move <= THRESHOLD_DOWN:
            direction, strength_label, icon = -1, "down", "↓"
        else:
            direction, strength_label, icon = 0, "flat", "→"

        return {
            "symbol": symbol,
            "cme_open": latest["open"],
            "cme_close_24h": latest["close_24h"],
            "move_pct": latest["move_pct"],
            "direction": direction,
            "strength_label": strength_label,
            "icon": icon,
            "n_weeks": len(results),
            "latest_sunday_et": str(results[-1]["ts"]),
        }
    except Exception:
        return None


def get_cme_weekly_gap_from_daily(
    symbol: str,
    period: str = "2y",
) -> Optional[Dict]:
    """
    Fallback using daily data: "CME gap" = (Monday open - Friday close) / Friday close.
    Approximates the weekend/CME open move with more history for backtest.
    """
    if yf is None:
        return None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        if df is None or len(df) < 14:
            return None
        df = df.dropna(subset=["Open", "Close"])
        df.index = pd.to_datetime(df.index)
        df["weekday"] = df.index.weekday
        fridays = df[df.weekday == 4]
        mondays = df[df.weekday == 0]
        if len(fridays) < 2 or len(mondays) < 2:
            return None
        # Align: same week Friday close -> next Monday open
        gaps = []
        for i, (_, fr) in enumerate(fridays.iterrows()):
            fri_close = fr["Close"]
            # next Monday
            mon_idx = df.index[df.index > fr.name]
            if len(mon_idx) == 0:
                continue
            next_bars = df.loc[mon_idx].head(5)
            next_mon = next_bars[next_bars.weekday == 0]
            if len(next_mon) == 0:
                continue
            mon_open = next_mon.iloc[0]["Open"]
            gap_pct = (mon_open - fri_close) / fri_close * 100
            gaps.append({"gap_pct": gap_pct, "fri_close": fri_close, "mon_open": mon_open})

        if not gaps:
            return None
        latest = gaps[-1]
        move = latest["gap_pct"]
        if move >= THRESHOLD_STRONG_UP:
            direction, strength_label, icon = 1, "strong_up", "↑↑"
        elif move >= THRESHOLD_UP:
            direction, strength_label, icon = 1, "up", "↑"
        elif move <= THRESHOLD_STRONG_DOWN:
            direction, strength_label, icon = -1, "strong_down", "↓↓"
        elif move <= THRESHOLD_DOWN:
            direction, strength_label, icon = -1, "down", "↓"
        else:
            direction, strength_label, icon = 0, "flat", "→"

        return {
            "symbol": symbol,
            "gap_pct": latest["gap_pct"],
            "direction": direction,
            "strength_label": strength_label,
            "icon": icon,
            "n_weeks": len(gaps),
            "source": "daily_gap",
        }
    except Exception:
        return None


def get_cme_direction_for_symbol(symbol: str, use_1h_first: bool = True) -> Optional[Dict]:
    """
    Get CME Sunday open direction for a symbol.
    Tries 1h-based CME open first; falls back to weekly gap from daily.
    """
    if use_1h_first:
        out = get_cme_sunday_open_from_1h(symbol)
        if out is not None:
            return out
    return get_cme_weekly_gap_from_daily(symbol)


# Symbols that have a CME Sunday 6pm open (crypto futures, index futures, metals)
CME_PROXY_SYMBOLS = [
    "BTC-USD",
    "ETH-USD",
    "GC=F",
    "SI=F",
    "HG=F",
    "CL=F",
    "SPY",
    "QQQ",
]


def get_cme_direction_all(use_1h_first: bool = True) -> Dict[str, Dict]:
    """Get CME direction for all CME_PROXY_SYMBOLS."""
    result = {}
    for sym in CME_PROXY_SYMBOLS:
        r = get_cme_direction_for_symbol(sym, use_1h_first=use_1h_first)
        if r is not None:
            result[sym] = r
    return result
