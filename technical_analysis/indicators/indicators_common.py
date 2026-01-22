"""
Common indicator calculation functions
Shared between compute_indicators_tv and compute_indicators_with_score
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, AccDistIndexIndicator
from tradingview_indicators import RSI, ema, sma


def compute_gmma(close):
    """Compute GMMA (Guppy Multiple Moving Average)"""
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]
    
    short_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in short_periods})
    long_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in long_periods})
    
    return short_emas, long_emas


def compute_gmma_tv(close):
    """Compute GMMA using TradingView-style calculations"""
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]
    
    short_emas = pd.DataFrame({f"ema_{p}": ema(close, p) for p in short_periods})
    long_emas = pd.DataFrame({f"ema_{p}": ema(close, p) for p in long_periods})
    
    return short_emas, long_emas


def calculate_moving_averages_tv(close):
    """Calculate moving averages using TradingView library"""
    result = {}
    
    if len(close) >= 50:
        ema50_values = ema(close, 50)
        result["ema50"] = round(ema50_values.iloc[-1], 4)
    
    if len(close) >= 200:
        ema200_values = ema(close, 200)
        result["ema200"] = round(ema200_values.iloc[-1], 4)
    
    if len(close) >= 50:
        sma50_values = sma(close, 50)
        result["sma50"] = round(sma50_values.iloc[-1], 4)
    
    if len(close) >= 200:
        sma200_values = sma(close, 200)
        result["sma200"] = round(sma200_values.iloc[-1], 4)
    
    return result


def calculate_moving_averages_ta(close):
    """Calculate moving averages using ta library"""
    result = {}
    
    if len(close) >= 50:
        ema50 = close.ewm(span=50, adjust=False).mean()
        result["ema50"] = round(ema50.iloc[-1], 4)
    
    if len(close) >= 200:
        ema200 = close.ewm(span=200, adjust=False).mean()
        result["ema200"] = round(ema200.iloc[-1], 4)
    
    if len(close) >= 50:
        sma50 = close.rolling(window=50).mean()
        result["sma50"] = round(sma50.iloc[-1], 4)
    
    if len(close) >= 200:
        sma200 = close.rolling(window=200).mean()
        result["sma200"] = round(sma200.iloc[-1], 4)
    
    return result


def calculate_adx(high, low, close, window=14):
    """Calculate ADX using ta library"""
    try:
        if len(close) < window:
            return None, None
        
        adx_indicator = ADXIndicator(high, low, close, window=window)
        adx_series = adx_indicator.adx()
        
        if len(adx_series) > 0 and not pd.isna(adx_series.iloc[-1]):
            adx_value = adx_series.iloc[-1]
            return round(adx_value, 2), adx_series
    except:
        pass
    
    return None, None


def calculate_cci(high, low, close, window=20):
    """Calculate CCI using ta library"""
    try:
        if len(close) < window:
            return None
        
        cci_indicator = CCIIndicator(high, low, close, window=window)
        cci_series = cci_indicator.cci()
        
        if len(cci_series) > 0 and not pd.isna(cci_series.iloc[-1]):
            return round(cci_series.iloc[-1], 2)
    except:
        pass
    
    return None


def calculate_obv(close, volume):
    """Calculate OBV and trend using ta library"""
    try:
        if len(close) < 2:
            return None, None
        
        obv_indicator = OnBalanceVolumeIndicator(close, volume)
        obv_series = obv_indicator.on_balance_volume()
        
        if len(obv_series) < 2:
            return None, None
        
        obv_value = obv_series.iloc[-1]
        obv_trending_up = obv_series.iloc[-1] > obv_series.iloc[-2]
        
        return round(obv_value, 2), obv_trending_up
    except:
        pass
    
    return None, None


def calculate_acc_dist(high, low, close, volume):
    """Calculate Accumulation/Distribution and trend using ta library"""
    try:
        if len(close) < 2:
            return None, None
        
        acc_dist_indicator = AccDistIndexIndicator(high, low, close, volume)
        acc_dist_series = acc_dist_indicator.acc_dist_index()
        
        if len(acc_dist_series) < 2:
            return None, None
        
        acc_dist_value = acc_dist_series.iloc[-1]
        acc_dist_trending_up = acc_dist_series.iloc[-1] > acc_dist_series.iloc[-2]
        
        return round(acc_dist_value, 2), acc_dist_trending_up
    except:
        pass
    
    return None, None


def calculate_macd(close, fast=12, slow=26, signal=9):
    """Calculate MACD using ta library"""
    try:
        if len(close) < slow:
            return None, None, None, None
        
        macd_indicator = MACD(close, window_fast=fast, window_slow=slow, window_sign=signal)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        histogram = macd_indicator.macd_diff()
        
        if len(macd_line) > 0 and not pd.isna(macd_line.iloc[-1]):
            macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
            macd_positive = histogram.iloc[-1] > 0
            return macd_line, signal_line, macd_bullish, macd_positive
    except:
        pass
    
    return None, None, None, None


def calculate_atr(high, low, close, window=14):
    """Calculate ATR using ta library"""
    try:
        if len(close) < window:
            return None, None, None
        
        atr_indicator = AverageTrueRange(high, low, close, window=window)
        atr_series = atr_indicator.average_true_range()
        
        if len(atr_series) > 0 and not pd.isna(atr_series.iloc[-1]):
            atr_value = atr_series.iloc[-1]
            current_price = close.iloc[-1]
            atr_pct = (atr_value / current_price) * 100 if current_price > 0 else None
            return round(atr_value, 4), round(atr_pct, 2) if atr_pct else None, atr_series
    except:
        pass
    
    return None, None, None


def calculate_momentum(close, lookback=14):
    """Calculate momentum (rate of change)"""
    if len(close) < lookback + 1:
        return None
    
    lookback = min(lookback, len(close) - 1)
    momentum = ((close.iloc[-1] / close.iloc[-lookback]) - 1) * 100
    
    # Cap extreme values
    if abs(momentum) > 50:
        momentum = 50 if momentum > 0 else -50
    
    return round(momentum, 2)


def calculate_4w_low(close):
    """Calculate 4-week low"""
    if len(close) >= 4:
        return round(close[-4:].min(), 4)
    return None
