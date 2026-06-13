"""
ISM (Institute for Supply Management) Business Cycle Indicator
Tracks manufacturing and services PMI to identify business cycle phases
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
import yfinance as yf

def get_ism_data() -> Optional[Dict]:
    """
    Fetch ISM Manufacturing PMI data
    Uses economic indicators available via yfinance or FRED
    
    Returns:
        Dictionary with ISM PMI value and business cycle phase
    """
    try:
        # Try to get ISM Manufacturing PMI from FRED via yfinance
        # Note: This is a placeholder - actual ISM data may need different source
        # ISM Manufacturing PMI ticker: NAPMPI (FRED)
        
        # Alternative: Use SPY as proxy for business cycle (correlated with ISM)
        # Or use economic indicators available via yfinance
        
        # For now, we'll use a combination approach:
        # 1. Try to get actual economic data if available
        # 2. Use market indicators as proxy
        
        # ISM Manufacturing PMI typically ranges 30-70
        # Above 50 = expansion, below 50 = contraction
        # Above 60 = strong expansion, below 40 = strong contraction
        
        # Try FRED data (if available via yfinance or other source)
        try:
            # Attempt to get ISM data - this may need adjustment based on data source
            # For demonstration, we'll use market-based proxies
            pass
        except:
            pass
        
        # Market-based proxy: Use SPY momentum and volatility as ISM proxy
        # Strong market = strong economy (correlated with ISM)
        spy = yf.Ticker("SPY")
        spy_df = spy.history(period="3mo", interval="1d")
        
        if len(spy_df) < 20:
            return None
        
        # Calculate market momentum (proxy for economic strength)
        spy_returns = spy_df['Close'].pct_change()
        recent_momentum = spy_returns.tail(20).mean() * 252  # Annualized
        
        # Calculate volatility (lower volatility = more stable economy)
        volatility = spy_returns.tail(20).std() * np.sqrt(252)  # Annualized
        
        # Convert to ISM-like scale (30-70 range, centered around 50)
        # Strong positive momentum + low volatility = high ISM (expansion)
        # Negative momentum + high volatility = low ISM (contraction)
        
        # Normalize momentum to 0-1 scale
        momentum_normalized = np.clip((recent_momentum + 0.2) / 0.4, 0, 1)  # -20% to +20% range
        
        # Normalize volatility (inverse - lower vol = higher score)
        vol_normalized = np.clip(1 - (volatility - 0.1) / 0.2, 0, 1)  # 10% to 30% vol range
        
        # Combine into ISM-like score (30-70 range)
        ism_pmi = 30 + (momentum_normalized * 0.6 + vol_normalized * 0.4) * 40
        
        # Determine business cycle phase
        if ism_pmi >= 60:
            phase = "strong_expansion"
            phase_score = 1.0
        elif ism_pmi >= 50:
            phase = "expansion"
            phase_score = 0.5
        elif ism_pmi >= 40:
            phase = "contraction"
            phase_score = -0.5
        else:
            phase = "strong_contraction"
            phase_score = -1.0
        
        # Calculate trend (improving or deteriorating)
        spy_short = spy_returns.tail(10).mean() * 252
        spy_long = spy_returns.tail(20).mean() * 252
        
        if spy_short > spy_long:
            trend = "improving"
            trend_score = 0.3
        elif spy_short < spy_long:
            trend = "deteriorating"
            trend_score = -0.3
        else:
            trend = "stable"
            trend_score = 0.0
        
        return {
            'ism_pmi': round(ism_pmi, 1),
            'phase': phase,
            'phase_score': phase_score,
            'trend': trend,
            'trend_score': trend_score,
            'momentum': round(recent_momentum * 100, 2),
            'volatility': round(volatility * 100, 2),
            'data_source': 'market_proxy',
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback: return neutral values
        return {
            'ism_pmi': 50.0,
            'phase': 'unknown',
            'phase_score': 0.0,
            'trend': 'unknown',
            'trend_score': 0.0,
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }


def get_ism_adjustment_for_timeframe(timeframe: str, ism_data: Optional[Dict] = None) -> float:
    """
    Get ISM-based score adjustment for specific timeframe
    
    Args:
        timeframe: Timeframe string (4H, 1D, 2D, 1W, 2W, 1M, 2M, 3M)
        ism_data: ISM data dictionary (if None, will fetch)
        
    Returns:
        Score adjustment value
    """
    if ism_data is None:
        ism_data = get_ism_data()
    
    if ism_data is None or ism_data.get('phase') == 'unknown':
        return 0.0
    
    # Base adjustment from phase
    phase_score = ism_data.get('phase_score', 0.0)
    trend_score = ism_data.get('trend_score', 0.0)
    
    # Combine phase and trend
    base_adjustment = phase_score + trend_score
    
    # Timeframe multipliers
    # Longer timeframes get more weight (business cycle is longer-term)
    timeframe_multipliers = {
        "4H": 0.2,   # Very small for intraday
        "1D": 0.3,   # Small for daily
        "2D": 0.4,   # Small-medium
        "1W": 0.6,   # Medium
        "2W": 0.8,   # Medium-large
        "1M": 1.0,   # Full weight
        "2M": 1.2,   # Above full weight
        "3M": 1.2,   # Above full weight
    }
    
    multiplier = timeframe_multipliers.get(timeframe, 0.5)
    adjustment = base_adjustment * multiplier
    
    return round(adjustment, 2)
