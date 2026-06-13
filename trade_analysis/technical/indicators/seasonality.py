"""
Seasonality Indicator for Cryptocurrencies
Analyzes historical seasonal patterns to adjust scoring
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

def calculate_crypto_seasonality(df: pd.DataFrame, min_years: int = 2) -> Dict:
    """
    Calculate seasonal patterns for cryptocurrency
    
    Args:
        df: DataFrame with datetime index and Close prices
        min_years: Minimum years of data required
        
    Returns:
        Dictionary with seasonality metrics
    """
    if len(df) == 0:
        return {
            'seasonality_score': 0.0,
            'monthly_returns': {},
            'quarterly_returns': {},
            'seasonal_adjustment': 0.0,
            'current_month': None,
            'current_quarter': None,
            'data_years': 0
        }
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Calculate years of data
    date_range = df.index[-1] - df.index[0]
    data_years = date_range.days / 365.25
    
    if data_years < min_years:
        return {
            'seasonality_score': 0.0,
            'monthly_returns': {},
            'quarterly_returns': {},
            'seasonal_adjustment': 0.0,
            'current_month': None,
            'current_quarter': None,
            'data_years': data_years
        }
    
    # Extract month and quarter
    df['month'] = df.index.month
    df['quarter'] = df.index.quarter
    df['year'] = df.index.year
    
    # Calculate monthly returns
    monthly_returns = {}
    for month in range(1, 13):
        month_data = df[df['month'] == month]
        if len(month_data) > 0:
            # Calculate average return for this month across all years
            month_returns = []
            for year in month_data['year'].unique():
                year_month_data = month_data[month_data['year'] == year]
                if len(year_month_data) > 1:
                    month_return = ((year_month_data['Close'].iloc[-1] / year_month_data['Close'].iloc[0]) - 1) * 100
                    month_returns.append(month_return)
            
            if month_returns:
                monthly_returns[month] = {
                    'avg_return': np.mean(month_returns),
                    'median_return': np.median(month_returns),
                    'positive_years': sum(1 for r in month_returns if r > 0),
                    'total_years': len(month_returns),
                    'win_rate': sum(1 for r in month_returns if r > 0) / len(month_returns) * 100 if month_returns else 0
                }
    
    # Calculate quarterly returns
    quarterly_returns = {}
    for quarter in range(1, 5):
        quarter_data = df[df['quarter'] == quarter]
        if len(quarter_data) > 0:
            quarter_ret = []
            for year in quarter_data['year'].unique():
                year_quarter_data = quarter_data[quarter_data['year'] == year]
                if len(year_quarter_data) > 1:
                    quarter_return = ((year_quarter_data['Close'].iloc[-1] / year_quarter_data['Close'].iloc[0]) - 1) * 100
                    quarter_ret.append(quarter_return)
            
            if quarter_ret:
                quarterly_returns[quarter] = {
                    'avg_return': np.mean(quarter_ret),
                    'median_return': np.median(quarter_ret),
                    'positive_years': sum(1 for r in quarter_ret if r > 0),
                    'total_years': len(quarter_ret),
                    'win_rate': sum(1 for r in quarter_ret if r > 0) / len(quarter_ret) * 100 if quarter_ret else 0
                }
    
    # Get current month and quarter
    current_date = df.index[-1]
    current_month = current_date.month
    current_quarter = current_date.quarter
    
    # Calculate seasonal adjustment based on current period
    seasonal_adjustment = 0.0
    seasonality_score = 0.0
    
    if current_month in monthly_returns:
        month_stats = monthly_returns[current_month]
        avg_return = month_stats['avg_return']
        win_rate = month_stats['win_rate']
        
        # Calculate adjustment based on historical performance
        # Strong positive months get bonus, negative months get penalty
        if avg_return > 5:  # Very strong month (>5% avg return)
            seasonal_adjustment = 1.5
            seasonality_score = 75
        elif avg_return > 2:  # Strong month (>2% avg return)
            seasonal_adjustment = 1.0
            seasonality_score = 60
        elif avg_return > 0:  # Positive month
            seasonal_adjustment = 0.5
            seasonality_score = 50
        elif avg_return > -2:  # Slightly negative
            seasonal_adjustment = -0.5
            seasonality_score = 40
        elif avg_return > -5:  # Negative month
            seasonal_adjustment = -1.0
            seasonality_score = 25
        else:  # Very negative month (<-5% avg return)
            seasonal_adjustment = -1.5
            seasonality_score = 10
        
        # Adjust based on win rate
        if win_rate >= 80:
            seasonal_adjustment += 0.5
            seasonality_score += 10
        elif win_rate >= 60:
            seasonal_adjustment += 0.25
            seasonality_score += 5
        elif win_rate < 40:
            seasonal_adjustment -= 0.25
            seasonality_score -= 5
    
    if current_quarter in quarterly_returns:
        quarter_stats = quarterly_returns[current_quarter]
        avg_return = quarter_stats['avg_return']
        
        # Quarterly adjustment (smaller impact)
        if avg_return > 10:  # Very strong quarter
            seasonal_adjustment += 0.5
            seasonality_score += 5
        elif avg_return > 5:  # Strong quarter
            seasonal_adjustment += 0.25
            seasonality_score += 3
        elif avg_return < -10:  # Very weak quarter
            seasonal_adjustment -= 0.5
            seasonality_score -= 5
        elif avg_return < -5:  # Weak quarter
            seasonal_adjustment -= 0.25
            seasonality_score -= 3
    
    return {
        'seasonality_score': min(100, max(0, seasonality_score)),
        'monthly_returns': monthly_returns,
        'quarterly_returns': quarterly_returns,
        'seasonal_adjustment': seasonal_adjustment,
        'current_month': current_month,
        'current_quarter': current_quarter,
        'data_years': data_years,
        'current_month_stats': monthly_returns.get(current_month, {}),
        'current_quarter_stats': quarterly_returns.get(current_quarter, {})
    }


def get_seasonal_adjustment_for_timeframe(
    df: pd.DataFrame, 
    timeframe: str,
    min_years: int = 2
) -> Tuple[float, Dict]:
    """
    Get seasonal adjustment for specific timeframe
    
    Args:
        df: DataFrame with price data
        timeframe: Timeframe string (1M, 2M, 3M, 1W, 2W, etc.)
        min_years: Minimum years of data required
        
    Returns:
        Tuple of (adjustment_value, seasonality_dict)
    """
    # Only apply to appropriate timeframes
    appropriate_timeframes = ['1M', '2M', '3M', '1W', '2W', '2D', '1D']
    
    if timeframe not in appropriate_timeframes:
        return 0.0, {}
    
    # Calculate seasonality
    seasonality = calculate_crypto_seasonality(df, min_years=min_years)
    
    # Adjust based on timeframe
    # Longer timeframes get more weight
    timeframe_multipliers = {
        '1D': 0.3,   # Small adjustment for daily
        '2D': 0.4,   # Small-medium
        '1W': 0.5,   # Medium
        '2W': 0.6,   # Medium-large
        '1M': 0.8,   # Large
        '2M': 1.0,   # Full weight
        '3M': 1.0,   # Full weight
    }
    
    multiplier = timeframe_multipliers.get(timeframe, 0.0)
    adjusted_adjustment = seasonality['seasonal_adjustment'] * multiplier
    
    return adjusted_adjustment, seasonality
