"""
Integration layer to use improved_scoring in main technical_analysis.py
Provides compatibility wrapper for existing code
"""

import pandas as pd
from typing import Dict, Optional

try:
    from .improved_scoring import improved_scoring, calculate_price_intensity
    IMPROVED_SCORING_AVAILABLE = True
except ImportError:
    try:
        from improved_scoring import improved_scoring, calculate_price_intensity
        IMPROVED_SCORING_AVAILABLE = True
    except ImportError:
        IMPROVED_SCORING_AVAILABLE = False


def apply_improved_scoring(result: Dict, df: pd.DataFrame, category: str, timeframe: str = "1W", market_context: dict = None) -> Dict:
    """
    Apply improved scoring logic to existing result dictionary
    This integrates explosive bottom detection into the main system
    
    Args:
        result: Existing result dictionary
        df: Price data DataFrame
        category: Asset category
        timeframe: Timeframe string (2D, 1W, 2W, 1M)
        market_context: Market context dict (SPX/Gold ratio, etc.)
    """
    if not IMPROVED_SCORING_AVAILABLE:
        return result
    
    try:
        # Calculate PI
        pi_value = calculate_price_intensity(df['Close'], df['Volume'])
        
        # Get improved score with timeframe and market context
        improved_result = improved_scoring(df, category, pi_value=pi_value, timeframe=timeframe, market_context=market_context)
        
        # Merge improved scoring into result
        result['score'] = improved_result['score']
        result['score_breakdown'].update(improved_result['breakdown'])
        
        # Update indicators if missing
        for key, value in improved_result['indicators'].items():
            if result.get(key) is None and value is not None:
                result[key] = value
        
        # Add PI to result
        if 'pi' in improved_result['indicators']:
            result['pi'] = improved_result['indicators']['pi']
        
        return result
    except Exception as e:
        # Fall back to original scoring if improved scoring fails
        return result
