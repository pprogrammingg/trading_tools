"""
Advanced Bottoming Structure Detection
Identifies specific bottom patterns that precede explosive moves
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

def detect_double_bottom(close: pd.Series, lookback: int = 40) -> Tuple[bool, Optional[float]]:
    """
    Detect double bottom pattern
    
    Returns:
        (is_double_bottom, support_level)
    """
    if len(close) < lookback:
        return False, None
    
    recent = close.iloc[-lookback:]
    
    # Find two significant lows
    lows = []
    for i in range(5, len(recent) - 5):
        if recent.iloc[i] == recent.iloc[i-5:i+6].min():
            lows.append((i, recent.iloc[i]))
    
    if len(lows) < 2:
        return False, None
    
    # Sort by price (lowest first)
    lows.sort(key=lambda x: x[1])
    
    # Check if two lowest are similar (within 3%)
    if len(lows) >= 2:
        lowest = lows[0][1]
        second_lowest = lows[1][1]
        
        if abs((lowest - second_lowest) / lowest) < 0.03:  # Within 3%
            # Check if second low came after first (double bottom pattern)
            if lows[1][0] > lows[0][0]:
                support_level = (lowest + second_lowest) / 2
                return True, support_level
    
    return False, None

def detect_inverse_head_shoulders(close: pd.Series, lookback: int = 60) -> Tuple[bool, Optional[float]]:
    """
    Detect inverse head and shoulders pattern
    
    Returns:
        (is_pattern, neckline_level)
    """
    if len(close) < lookback:
        return False, None
    
    recent = close.iloc[-lookback:]
    
    # Find three significant lows
    lows = []
    for i in range(5, len(recent) - 5):
        if recent.iloc[i] == recent.iloc[i-5:i+6].min():
            lows.append((i, recent.iloc[i]))
    
    if len(lows) < 3:
        return False, None
    
    # Sort by index (chronological)
    lows.sort(key=lambda x: x[0])
    
    # Check for inverse H&S: left shoulder, head (lowest), right shoulder
    if len(lows) >= 3:
        left_shoulder = lows[0][1]
        head = min(lows, key=lambda x: x[1])[1]
        head_idx = min(lows, key=lambda x: x[1])[0]
        
        # Find right shoulder (after head)
        right_shoulders = [l for l in lows if l[0] > head_idx]
        if len(right_shoulders) > 0:
            right_shoulder = min(right_shoulders, key=lambda x: x[1])[1]
            
            # Pattern: head lower than shoulders, shoulders similar height
            if head < left_shoulder and head < right_shoulder:
                shoulder_diff = abs((left_shoulder - right_shoulder) / left_shoulder)
                if shoulder_diff < 0.05:  # Shoulders within 5%
                    # Neckline is average of shoulder highs
                    neckline = (left_shoulder + right_shoulder) / 2
                    return True, neckline
    
    return False, None

def detect_ascending_triangle(close: pd.Series, high: pd.Series, lookback: int = 40) -> Tuple[bool, Optional[float]]:
    """
    Detect ascending triangle (bullish pattern)
    
    Returns:
        (is_pattern, breakout_level)
    """
    if len(close) < lookback:
        return False, None
    
    recent_close = close.iloc[-lookback:]
    recent_high = high.iloc[-lookback:]
    
    # Check for horizontal resistance
    resistance_level = recent_high.max()
    resistance_touches = sum(abs(recent_high - resistance_level) / resistance_level < 0.02)
    
    # Check for ascending support (rising lows)
    lows = [recent_close.iloc[i] for i in range(0, len(recent_close), 5)]
    if len(lows) >= 3:
        # Calculate slope of lows
        x = np.arange(len(lows))
        slope = np.polyfit(x, lows, 1)[0]
        
        # Ascending triangle: horizontal resistance, rising support
        if resistance_touches >= 2 and slope > 0:
            return True, resistance_level
    
    return False, None

def detect_falling_wedge(close: pd.Series, high: pd.Series, low: pd.Series, lookback: int = 40) -> Tuple[bool, Optional[float]]:
    """
    Detect falling wedge (bullish reversal pattern)
    
    Returns:
        (is_pattern, target_level)
    """
    if len(close) < lookback:
        return False, None
    
    recent_close = close.iloc[-lookback:]
    recent_high = high.iloc[-lookback:]
    recent_low = low.iloc[-lookback:]
    
    # Get swing highs and lows
    highs = []
    lows_list = []
    
    for i in range(5, len(recent_high) - 5):
        if recent_high.iloc[i] == recent_high.iloc[i-5:i+6].max():
            highs.append((i, recent_high.iloc[i]))
        if recent_low.iloc[i] == recent_low.iloc[i-5:i+6].min():
            lows_list.append((i, recent_low.iloc[i]))
    
    if len(highs) >= 2 and len(lows_list) >= 2:
        # Check if both are converging (falling wedge)
        high_slope = (highs[-1][1] - highs[0][1]) / (highs[-1][0] - highs[0][0]) if len(highs) >= 2 else 0
        low_slope = (lows_list[-1][1] - lows_list[0][1]) / (lows_list[-1][0] - lows_list[0][0]) if len(lows_list) >= 2 else 0
        
        # Falling wedge: both declining, but converging (high slope less negative than low slope)
        if high_slope < 0 and low_slope < 0 and high_slope > low_slope:
            # Target is where lines converge
            target = (highs[-1][1] + lows_list[-1][1]) / 2
            return True, target
    
    return False, None

def detect_complex_bottoming_structure(close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series, lookback: int = 60) -> Dict:
    """
    Comprehensive bottoming structure detection
    
    Returns:
        Dictionary with detected patterns and confidence
    """
    result = {
        'double_bottom': False,
        'inverse_hs': False,
        'ascending_triangle': False,
        'falling_wedge': False,
        'support_level': None,
        'target_level': None,
        'confidence': 0.0,
        'pattern_score': 0.0,
    }
    
    # Check each pattern
    double_bottom, db_support = detect_double_bottom(close, lookback)
    if double_bottom:
        result['double_bottom'] = True
        result['support_level'] = db_support
        result['pattern_score'] += 2.0
        result['confidence'] += 0.3
    
    inverse_hs, hs_neckline = detect_inverse_head_shoulders(close, lookback)
    if inverse_hs:
        result['inverse_hs'] = True
        result['support_level'] = hs_neckline
        result['pattern_score'] += 2.5
        result['confidence'] += 0.4
    
    ascending_triangle, at_breakout = detect_ascending_triangle(close, high, lookback)
    if ascending_triangle:
        result['ascending_triangle'] = True
        result['target_level'] = at_breakout
        result['pattern_score'] += 2.0
        result['confidence'] += 0.3
    
    falling_wedge, fw_target = detect_falling_wedge(close, high, low, lookback)
    if falling_wedge:
        result['falling_wedge'] = True
        result['target_level'] = fw_target
        result['pattern_score'] += 2.0
        result['confidence'] += 0.3
    
    # Volume confirmation
    if len(volume) >= 20:
        recent_volume = volume.iloc[-10:].mean()
        avg_volume = volume.iloc[-20:].mean()
        if recent_volume > avg_volume * 1.2:  # Volume building
            result['pattern_score'] += 0.5
            result['confidence'] += 0.1
    
    return result
