"""
Market Context Analysis
Analyzes SPX/Gold ratio, VIX, and overall market conditions to adjust scoring
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta

def get_market_context() -> Dict:
    """
    Get overall market context including SPX/Gold ratio and VIX
    
    Returns:
        Dictionary with market context indicators including:
        - spx_gold_ratio: Current SPX/Gold ratio
        - spx_gold_trend: Trend of ratio (crashing, declining, neutral, rising, near_low)
        - market_bearish: Boolean indicating bear market conditions
        - market_adjustment: Score adjustment based on SPX/Gold
        - vix: Current VIX level
        - vix_level: VIX level category (low, moderate, high, very_high)
        - vix_trend: VIX trend (rising, falling, stable)
        - vix_adjustment: Score adjustment based on VIX
    """
    try:
        # Get SPX data
        spx = yf.Ticker("^GSPC")
        spx_df = spx.history(period="1y")
        
        # Get Gold data
        gold = yf.Ticker("GC=F")
        gold_df = gold.history(period="1y")
        
        # Get VIX data
        vix = yf.Ticker("^VIX")
        vix_df = vix.history(period="1y")
        
        if len(spx_df) == 0 or len(gold_df) == 0:
            return {
                'spx_gold_ratio': None,
                'spx_gold_trend': 'unknown',
                'market_bearish': False,
                'market_adjustment': 0.0,
                'vix': None,
                'vix_level': 'unknown',
                'vix_trend': 'unknown',
                'vix_adjustment': 0.0,
            }
        
        # Align dates
        common_dates = spx_df.index.intersection(gold_df.index)
        if len(common_dates) == 0:
            return {
                'spx_gold_ratio': None,
                'spx_gold_trend': 'unknown',
                'market_bearish': False,
                'market_adjustment': 0.0,
                'vix': None,
                'vix_level': 'unknown',
                'vix_trend': 'unknown',
                'vix_adjustment': 0.0,
            }
        
        # Process VIX data
        vix_value = None
        vix_level = 'unknown'
        vix_trend = 'unknown'
        vix_adjustment = 0.0
        
        if len(vix_df) > 0:
            vix_close = vix_df['Close']
            vix_value = float(vix_close.iloc[-1])
            
            # Determine VIX level
            # Low VIX (< 20): Calmer markets, steady upside, risk-on
            # Moderate VIX (20-29): Faster moves, higher risk, potential drawdowns, risk-off
            # High VIX (> 29): Risk rises meaningfully
            if vix_value < 20:
                vix_level = 'low'
                vix_adjustment = 0.0  # No adjustment for low VIX (constructive)
            elif vix_value < 29:
                vix_level = 'moderate'
                vix_adjustment = -0.5  # Slight reduction for moderate VIX (risk-off)
            else:
                vix_level = 'high'
                vix_adjustment = -1.5  # Significant reduction for high VIX (high risk)
            
            # Determine VIX trend (rising = more risk)
            if len(vix_close) >= 10:
                vix_ma5 = vix_close.rolling(5).mean()
                vix_ma20 = vix_close.rolling(min(20, len(vix_close))).mean()
                
                current_ma5 = vix_ma5.iloc[-1]
                current_ma20 = vix_ma20.iloc[-1]
                
                if current_ma5 > current_ma20 * 1.1:  # Rising >10%
                    vix_trend = 'rising'
                    vix_adjustment -= 0.5  # Additional penalty for rising VIX
                elif current_ma5 < current_ma20 * 0.9:  # Falling >10%
                    vix_trend = 'falling'
                    # No additional adjustment for falling VIX
                else:
                    vix_trend = 'stable'
        
        spx_aligned = spx_df.loc[common_dates]['Close']
        gold_aligned = gold_df.loc[common_dates]['Close']
        
        # Calculate ratio
        ratio = spx_aligned / gold_aligned
        current_ratio = ratio.iloc[-1]
        
        # Calculate trend (20-day moving average)
        if len(ratio) >= 20:
            ratio_ma20 = ratio.rolling(20).mean()
            ratio_slope = (ratio_ma20.iloc[-1] - ratio_ma20.iloc[-20]) / ratio_ma20.iloc[-20] * 100
            
            # Determine trend
            if ratio_slope < -5:  # Falling >5% in 20 days
                trend = 'crashing'
                market_bearish = True
                market_adjustment = -2.0  # Reduce scores by 2 points
            elif ratio_slope < -2:  # Falling 2-5%
                trend = 'declining'
                market_bearish = True
                market_adjustment = -1.0  # Reduce scores by 1 point
            elif ratio_slope < 2:  # Flat
                trend = 'neutral'
                market_bearish = False
                market_adjustment = 0.0
            else:  # Rising
                trend = 'rising'
                market_bearish = False
                market_adjustment = 0.0
        else:
            trend = 'unknown'
            market_bearish = False
            market_adjustment = 0.0
        
        # Check if ratio is near recent lows (potential crash)
        if len(ratio) >= 60:
            recent_low = ratio.iloc[-60:].min()
            distance_from_low = ((current_ratio / recent_low) - 1) * 100
            
            if distance_from_low < 5:  # Within 5% of recent low
                market_adjustment -= 1.0  # Additional penalty
                trend = 'near_low'
        
        return {
            'spx_gold_ratio': float(current_ratio),
            'spx_gold_trend': trend,
            'market_bearish': market_bearish,
            'market_adjustment': market_adjustment,
            'ratio_slope_pct': float(ratio_slope) if len(ratio) >= 20 else None,
            'vix': vix_value,
            'vix_level': vix_level,
            'vix_trend': vix_trend,
            'vix_adjustment': vix_adjustment,
        }
    except Exception as e:
        return {
            'spx_gold_ratio': None,
            'spx_gold_trend': 'unknown',
            'market_bearish': False,
            'market_adjustment': 0.0,
            'vix': None,
            'vix_level': 'unknown',
            'vix_trend': 'unknown',
            'vix_adjustment': 0.0,
            'error': str(e),
        }
