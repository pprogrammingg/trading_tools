"""
Cup-and-handle / cup breakout pattern detection.
Detects: cup formed (U-shaped bottom), then breakout above the rim (left high).
Reference: Gold monthly cup formed by ~Oct 2011, broke out Aug 2020.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any


def _swing_high_idx(close: pd.Series, lookback: int = 5) -> pd.Series:
    """Boolean series: True where close is a local high over ±lookback bars."""
    out = pd.Series(False, index=close.index)
    for i in range(lookback, len(close) - lookback):
        if close.iloc[i] == close.iloc[i - lookback : i + lookback + 1].max():
            out.iloc[i] = True
    return out


def _swing_low_idx(close: pd.Series, lookback: int = 5) -> pd.Series:
    """Boolean series: True where close is a local low over ±lookback bars."""
    out = pd.Series(False, index=close.index)
    for i in range(lookback, len(close) - lookback):
        if close.iloc[i] == close.iloc[i - lookback : i + lookback + 1].min():
            out.iloc[i] = True
    return out


def detect_cup_and_breakout(
    close: pd.Series,
    lookback_rim: int = 60,
    min_cup_bars: int = 6,
    breakout_pct: float = 0.001,
    recent_bars: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    Detect cup pattern and breakout above the rim (left high).

    Cup: price makes a significant high (left rim), declines to a low (cup bottom),
    then recovers. Breakout = close above the left rim.

    Args:
        close: Price series (e.g. Close).
        lookback_rim: Bars to look back for the left rim high (default 60).
        min_cup_bars: Minimum bars from rim to cup bottom (default 6).
        breakout_pct: Close must be > rim * (1 + breakout_pct) to count breakout (default 0.001).
        recent_bars: Consider "recent breakout" if breakout in last N bars (default 5).

    Returns:
        Dict with: cup_formed, cup_breakout, recent_breakout, rim_level, cup_bottom,
        rim_bar_idx, bottom_bar_idx, breakout_bar_idx, current_above_rim; or None if insufficient data.
    """
    if close is None or len(close) < lookback_rim + min_cup_bars + 10:
        return None

    close = close.astype(float)
    n = len(close)
    current_price = close.iloc[-1]

    # Left rim: significant high in the lookback window (we use the highest high in first half of lookback as "rim")
    half = lookback_rim // 2
    window = close.iloc[-lookback_rim:]
    rim_level = window.iloc[: half + 1].max()
    rim_bar_idx = window.iloc[: half + 1].idxmax()
    rim_pos_in_window = window.index.get_loc(rim_bar_idx)

    # Cup bottom: lowest low after the rim, within the window
    after_rim = window.iloc[rim_pos_in_window + min_cup_bars :]
    if len(after_rim) < min_cup_bars:
        return None
    cup_bottom = after_rim.min()
    bottom_bar_idx = after_rim.idxmin()
    bottom_pos = window.index.get_loc(bottom_bar_idx)

    # Recovery: price must have risen from bottom toward rim
    after_bottom = window.iloc[bottom_pos + 1 :]
    if len(after_bottom) < 2:
        return None
    cup_formed = cup_bottom < rim_level and after_bottom.max() >= cup_bottom * 1.01

    # Breakout: any close after the bottom that is above rim * (1 + breakout_pct)
    breakout_bar_idx = None
    for i, (idx, val) in enumerate(after_bottom.items()):
        if val >= rim_level * (1 + breakout_pct):
            breakout_bar_idx = idx
            break
    cup_breakout = breakout_bar_idx is not None
    current_above_rim = current_price >= rim_level * (1 + breakout_pct)

    # Recent breakout: breakout in the last `recent_bars` bars
    last_bars = close.index[-recent_bars:] if recent_bars else []
    recent_breakout = (
        cup_breakout
        and breakout_bar_idx is not None
        and breakout_bar_idx in last_bars
    )

    return {
        "cup_formed": bool(cup_formed),
        "cup_breakout": bool(cup_breakout),
        "recent_breakout": bool(recent_breakout),
        "rim_level": float(rim_level),
        "cup_bottom": float(cup_bottom),
        "rim_bar_idx": rim_bar_idx,
        "bottom_bar_idx": bottom_bar_idx,
        "breakout_bar_idx": breakout_bar_idx,
        "current_above_rim": bool(current_above_rim),
        "current_price": float(current_price),
    }


def get_cup_signal_for_scoring(
    close: pd.Series,
    timeframe: str,
    lookback_rim: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get cup pattern state for scoring integration.
    Uses timeframe-appropriate lookback (more bars for longer TFs).

    Returns:
        Dict with cup_formed, cup_breakout, recent_breakout, and optional score_boost recommendation.
    """
    # Default lookback by timeframe (approx bars: 2D~90, 1W~52, 2W~26, 1M~24, 2M~12, 6M~6)
    if lookback_rim is None:
        lookback_rim = {
            "4H": 120,
            "1D": 90,
            "2D": 90,
            "1W": 52,
            "2W": 40,
            "1M": 24,
            "2M": 18,
            "6M": 12,
        }.get(timeframe, 40)
    out = detect_cup_and_breakout(close, lookback_rim=lookback_rim, recent_bars=5)
    if not out:
        return {"cup_formed": False, "cup_breakout": False, "recent_breakout": False}
    return {
        "cup_formed": out["cup_formed"],
        "cup_breakout": out["cup_breakout"],
        "recent_breakout": out["recent_breakout"],
        "rim_level": out["rim_level"],
        "cup_bottom": out["cup_bottom"],
        "current_above_rim": out["current_above_rim"],
    }
