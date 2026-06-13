"""
Super Guppy indicator for crypto (and optionally other categories).

Uses the same EMA ribbon as GMMA (short: 3,5,8,10,12,15; long: 30,35,40,45,50,60).
Interpretation:
- Grey: ribbons compressed (no clear trend) → often signals bad times / caution.
- Orange at bottom: short EMAs in downtrend (orange) but price at/near low and
  compression or turn starting → double-bottom / reversal signal.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

# Same periods as GMMA
SHORT_PERIODS = [3, 5, 8, 10, 12, 15]
LONG_PERIODS = [30, 35, 40, 45, 50, 60]

# Grey = compression when ribbon spread (as % of price) is below this
COMPRESSION_PCT = 2.5

# Orange reversal: price within this % of N-bar low to consider "at bottom"
BOTTOM_NEAR_LOW_PCT = 8.0
BOTTOM_LOOKBACK = 20

# Short ribbon "turning up" if short_avg now > short_avg this many bars ago
TURN_LOOKBACK = 3


def _compute_ribbons(close: pd.Series) -> tuple:
    """Compute short and long EMA ribbons. Returns (short_df, long_df)."""
    short_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in SHORT_PERIODS})
    long_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in LONG_PERIODS})
    return short_emas, long_emas


def get_super_guppy_state(close: pd.Series, timeframe: str = "1W") -> Dict[str, Any]:
    """
    Compute Super Guppy state from close series.

    Returns dict with:
      - state: 'bullish' | 'bearish' | 'grey' | 'orange_reversal'
      - short_avg, long_avg: current ribbon mid values
      - spread_pct: (long_avg - short_avg) / price * 100 (positive when bearish)
      - at_bottom: bool (price near recent low)
      - short_turning_up: bool (short ribbon turning up from recent lows)
    """
    if len(close) < max(LONG_PERIODS) + BOTTOM_LOOKBACK:
        return {"state": "unknown", "short_avg": None, "long_avg": None, "spread_pct": None}

    short_emas, long_emas = _compute_ribbons(close)
    price = float(close.iloc[-1])

    short_last = short_emas.iloc[-1]
    long_last = long_emas.iloc[-1]
    short_avg = float(short_last.mean())
    long_avg = float(long_last.mean())

    spread_pct = ((long_avg - short_avg) / price * 100) if price > 0 else 0
    short_min = short_last.min()
    short_max = short_last.max()
    long_min = long_last.min()
    long_max = long_last.max()
    ribbon_spread_pct = (max(short_max, long_max) - min(short_min, long_min)) / price * 100 if price > 0 else 0

    # At bottom: price within BOTTOM_NEAR_LOW_PCT of BOTTOM_LOOKBACK low
    # For longer timeframes, use longer lookback and wider threshold
    timeframe_lookback = {"4H": 20, "1D": 20, "2D": 15, "1W": 12, "2W": 8, "1M": 6}.get(timeframe, 20)
    timeframe_threshold = {"4H": 8.0, "1D": 8.0, "2D": 10.0, "1W": 12.0, "2W": 15.0, "1M": 18.0}.get(timeframe, 8.0)
    lookback_low = close.iloc[-timeframe_lookback:].min() if len(close) >= timeframe_lookback else close.min()
    at_bottom = (price <= lookback_low * (1 + timeframe_threshold / 100)) if lookback_low > 0 else False

    # Short ribbon turning up: short_avg now > short_avg TURN_LOOKBACK bars ago
    # For longer timeframes, use longer lookback for "turning up" (more lenient)
    turn_lookback = {"4H": 3, "1D": 3, "2D": 2, "1W": 2, "2W": 1, "1M": 1}.get(timeframe, 3)
    short_avg_prev = float(short_emas.iloc[-1 - turn_lookback].mean()) if len(short_emas) > turn_lookback else short_avg
    short_turning_up = short_avg > short_avg_prev
    # Also consider compression at bottom (ribbons compressing) as a reversal signal for longer timeframes
    if timeframe in ["1W", "2W", "1M"]:
        short_avg_2prev = float(short_emas.iloc[-1 - turn_lookback * 2].mean()) if len(short_emas) > turn_lookback * 2 else short_avg
        compressing = abs(short_avg - long_avg) < abs(short_avg_2prev - long_avg) * 0.9  # Ribbons getting closer
        short_turning_up = short_turning_up or (at_bottom and compressing and spread_pct < 8)

    # --- State logic ---
    # Grey: ribbons compressed (spread as % of price small) → no clear trend, bad times
    if ribbon_spread_pct < COMPRESSION_PCT:
        state = "grey"
    # Bullish: short ribbon above long
    elif short_min > long_max:
        state = "bullish"
    # Bearish (orange/red): short below long
    elif short_max < long_min:
        # Orange at bottom = double-bottom signal.
        # On 1W/2W/1M: orange at bottom = at_bottom + bearish (what you see on chart).
        # On 4H/1D/2D: also require short_turning_up (backtest showed that works best).
        if at_bottom:
            if timeframe in ["1W", "2W", "1M"]:
                state = "orange_reversal"  # Orange at bottom = double bottom on weekly
            elif short_turning_up:
                state = "orange_reversal"
            else:
                state = "bearish"
        else:
            state = "bearish"
    else:
        # Mixed / expansion but no clear dominance
        if at_bottom and (timeframe in ["1W", "2W", "1M"] or short_turning_up) and spread_pct < 5:
            state = "orange_reversal"
        elif ribbon_spread_pct < COMPRESSION_PCT * 1.5:
            state = "grey"
        elif short_avg > long_avg:
            state = "bullish"
        else:
            state = "bearish"

    return {
        "state": state,
        "short_avg": round(short_avg, 4),
        "long_avg": round(long_avg, 4),
        "spread_pct": round(spread_pct, 2),
        "ribbon_spread_pct": round(ribbon_spread_pct, 2),
        "at_bottom": at_bottom,
        "short_turning_up": short_turning_up,
    }
