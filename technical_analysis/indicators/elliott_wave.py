"""
Elliott Wave Analysis for Price Targets
Identifies wave patterns and calculates price targets
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List

def identify_swing_points(close: pd.Series, lookback: int = 5) -> Tuple[pd.Series, pd.Series]:
    """
    Identify swing highs and swing lows for Elliott Wave analysis
    
    Returns:
        Tuple of (swing_highs, swing_lows) as boolean series
    """
    swing_highs = pd.Series(False, index=close.index)
    swing_lows = pd.Series(False, index=close.index)
    
    for i in range(lookback, len(close) - lookback):
        # Swing high: higher than lookback periods before and after
        if all(close.iloc[i] > close.iloc[i-j] for j in range(1, lookback+1)) and \
           all(close.iloc[i] > close.iloc[i+j] for j in range(1, lookback+1)):
            swing_highs.iloc[i] = True
        
        # Swing low: lower than lookback periods before and after
        if all(close.iloc[i] < close.iloc[i-j] for j in range(1, lookback+1)) and \
           all(close.iloc[i] < close.iloc[i+j] for j in range(1, lookback+1)):
            swing_lows.iloc[i] = True
    
    return swing_highs, swing_lows

def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels
    
    Returns:
        Dictionary of Fibonacci levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
    """
    diff = high - low
    return {
        'fib_236': high - (diff * 0.236),
        'fib_382': high - (diff * 0.382),
        'fib_500': high - (diff * 0.500),
        'fib_618': high - (diff * 0.618),
        'fib_786': high - (diff * 0.786),
    }

def identify_elliott_wave_pattern(close: pd.Series, lookback: int = 20) -> Optional[Dict]:
    """
    Identify Elliott Wave pattern and calculate price targets
    
    Returns:
        Dictionary with wave pattern, current wave, and price targets
    """
    if len(close) < lookback * 2:
        return None
    
    # Get recent swing points
    swing_highs, swing_lows = identify_swing_points(close, lookback=3)
    
    # Get recent significant highs and lows
    recent_data = close.iloc[-lookback:]
    recent_high = recent_data.max()
    recent_low = recent_data.min()
    high_idx = recent_data.idxmax()
    low_idx = recent_data.idxmin()
    
    # Determine if we're in an uptrend or downtrend
    if high_idx > low_idx:  # High came after low = uptrend
        trend = "uptrend"
        wave_start = recent_low
        wave_high = recent_high
    else:  # Low came after high = downtrend
        trend = "downtrend"
        wave_start = recent_high
        wave_low = recent_low
    
    current_price = close.iloc[-1]
    
    # Calculate Fibonacci levels
    if trend == "uptrend":
        fib_levels = calculate_fibonacci_levels(wave_high, wave_start)
        # Price targets for wave 3, 5 (uptrend)
        wave_3_target = wave_high + (wave_high - wave_start) * 1.618  # 161.8% extension
        wave_5_target = wave_high + (wave_high - wave_start) * 2.618  # 261.8% extension
        
        # Support levels (Fibonacci retracements)
        support_levels = {
            'fib_382': fib_levels['fib_382'],
            'fib_500': fib_levels['fib_500'],
            'fib_618': fib_levels['fib_618'],
        }
        
        # Determine current wave position
        if current_price > wave_high * 0.95:
            wave_position = "Wave 3 or 5"
        elif current_price > fib_levels['fib_618']:
            wave_position = "Wave 2 or 4 (correction)"
        else:
            wave_position = "Wave 1 or correction"
        
    else:  # downtrend
        fib_levels = calculate_fibonacci_levels(wave_start, wave_low)
        # Price targets for wave 3, 5 (downtrend)
        wave_3_target = wave_low - (wave_start - wave_low) * 1.618
        wave_5_target = wave_low - (wave_start - wave_low) * 2.618
        
        # Resistance levels (Fibonacci retracements)
        support_levels = {
            'fib_382': fib_levels['fib_382'],
            'fib_500': fib_levels['fib_500'],
            'fib_618': fib_levels['fib_618'],
        }
        
        # Determine current wave position
        if current_price < wave_low * 1.05:
            wave_position = "Wave 3 or 5"
        elif current_price < fib_levels['fib_618']:
            wave_position = "Wave 2 or 4 (correction)"
        else:
            wave_position = "Wave 1 or correction"
    
    return {
        'trend': trend,
        'wave_position': wave_position,
        'current_price': current_price,
        'wave_start': wave_start,
        'recent_extreme': wave_high if trend == "uptrend" else wave_low,
        'price_targets': {
            'wave_3': wave_3_target,
            'wave_5': wave_5_target,
        },
        'support_resistance': support_levels,
        'fibonacci_levels': fib_levels,
    }

def calculate_elliott_wave_targets(close: pd.Series, high: pd.Series, low: pd.Series) -> Optional[Dict]:
    """
    Main function to calculate Elliott Wave price targets
    
    Returns:
        Dictionary with wave analysis and price targets
    """
    if len(close) < 50:
        return None
    
    try:
        wave_analysis = identify_elliott_wave_pattern(close, lookback=20)
        return wave_analysis
    except Exception:
        return None
