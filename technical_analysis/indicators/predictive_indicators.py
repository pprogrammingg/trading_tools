"""
Predictive Technical Indicators
Functions to detect early signals before big moves
"""

import pandas as pd
import numpy as np


def detect_rsi_divergence(close, rsi_values, lookback=20):
    """
    Detect RSI divergence - early warning of trend exhaustion or reversal
    
    Returns:
        - 'bearish_divergence': Price higher high, RSI lower high (exhaustion)
        - 'bullish_divergence': Price lower low, RSI higher low (reversal)
        - None: No divergence detected
    """
    if len(close) < lookback or len(rsi_values) < lookback:
        return None
    
    # Get recent price and RSI peaks/troughs
    recent_close = close[-lookback:]
    recent_rsi = rsi_values[-lookback:]
    
    # Find peaks (local maxima) and troughs (local minima)
    # Simple approach: compare with neighbors
    price_peaks = []
    price_troughs = []
    rsi_peaks = []
    rsi_troughs = []
    
    for i in range(2, len(recent_close) - 2):
        # Price peak
        if (recent_close.iloc[i] > recent_close.iloc[i-1] and 
            recent_close.iloc[i] > recent_close.iloc[i-2] and
            recent_close.iloc[i] > recent_close.iloc[i+1] and
            recent_close.iloc[i] > recent_close.iloc[i+2]):
            price_peaks.append((i, recent_close.iloc[i]))
        
        # Price trough
        if (recent_close.iloc[i] < recent_close.iloc[i-1] and 
            recent_close.iloc[i] < recent_close.iloc[i-2] and
            recent_close.iloc[i] < recent_close.iloc[i+1] and
            recent_close.iloc[i] < recent_close.iloc[i+2]):
            price_troughs.append((i, recent_close.iloc[i]))
        
        # RSI peak
        if (recent_rsi.iloc[i] > recent_rsi.iloc[i-1] and 
            recent_rsi.iloc[i] > recent_rsi.iloc[i-2] and
            recent_rsi.iloc[i] > recent_rsi.iloc[i+1] and
            recent_rsi.iloc[i] > recent_rsi.iloc[i+2]):
            rsi_peaks.append((i, recent_rsi.iloc[i]))
        
        # RSI trough
        if (recent_rsi.iloc[i] < recent_rsi.iloc[i-1] and 
            recent_rsi.iloc[i] < recent_rsi.iloc[i-2] and
            recent_rsi.iloc[i] < recent_rsi.iloc[i+1] and
            recent_rsi.iloc[i] < recent_rsi.iloc[i+2]):
            rsi_troughs.append((i, recent_rsi.iloc[i]))
    
    # Check for bearish divergence (price higher high, RSI lower high)
    if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
        latest_price_peak = price_peaks[-1][1]
        prev_price_peak = price_peaks[-2][1]
        latest_rsi_peak = rsi_peaks[-1][1]
        prev_rsi_peak = rsi_peaks[-2][1]
        
        if (latest_price_peak > prev_price_peak and 
            latest_rsi_peak < prev_rsi_peak):
            return 'bearish_divergence'
    
    # Check for bullish divergence (price lower low, RSI higher low)
    if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
        latest_price_trough = price_troughs[-1][1]
        prev_price_trough = price_troughs[-2][1]
        latest_rsi_trough = rsi_troughs[-1][1]
        prev_rsi_trough = rsi_troughs[-2][1]
        
        if (latest_price_trough < prev_price_trough and 
            latest_rsi_trough > prev_rsi_trough):
            return 'bullish_divergence'
    
    return None


def detect_macd_divergence(close, macd_line, lookback=20):
    """
    Detect MACD divergence - early warning of momentum exhaustion
    
    Returns:
        - 'bearish_divergence': Price higher high, MACD lower high
        - 'bullish_divergence': Price lower low, MACD higher low
        - None: No divergence detected
    """
    if len(close) < lookback or len(macd_line) < lookback:
        return None
    
    recent_close = close[-lookback:]
    recent_macd = macd_line[-lookback:]
    
    # Find peaks and troughs
    price_peaks = []
    price_troughs = []
    macd_peaks = []
    macd_troughs = []
    
    for i in range(2, len(recent_close) - 2):
        # Price peak
        if (recent_close.iloc[i] > recent_close.iloc[i-1] and 
            recent_close.iloc[i] > recent_close.iloc[i-2] and
            recent_close.iloc[i] > recent_close.iloc[i+1] and
            recent_close.iloc[i] > recent_close.iloc[i+2]):
            price_peaks.append((i, recent_close.iloc[i]))
        
        # Price trough
        if (recent_close.iloc[i] < recent_close.iloc[i-1] and 
            recent_close.iloc[i] < recent_close.iloc[i-2] and
            recent_close.iloc[i] < recent_close.iloc[i+1] and
            recent_close.iloc[i] < recent_close.iloc[i+2]):
            price_troughs.append((i, recent_close.iloc[i]))
        
        # MACD peak
        if (recent_macd.iloc[i] > recent_macd.iloc[i-1] and 
            recent_macd.iloc[i] > recent_macd.iloc[i-2] and
            recent_macd.iloc[i] > recent_macd.iloc[i+1] and
            recent_macd.iloc[i] > recent_macd.iloc[i+2]):
            macd_peaks.append((i, recent_macd.iloc[i]))
        
        # MACD trough
        if (recent_macd.iloc[i] < recent_macd.iloc[i-1] and 
            recent_macd.iloc[i] < recent_macd.iloc[i-2] and
            recent_macd.iloc[i] < recent_macd.iloc[i+1] and
            recent_macd.iloc[i] < recent_macd.iloc[i+2]):
            macd_troughs.append((i, recent_macd.iloc[i]))
    
    # Check for bearish divergence
    if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
        latest_price_peak = price_peaks[-1][1]
        prev_price_peak = price_peaks[-2][1]
        latest_macd_peak = macd_peaks[-1][1]
        prev_macd_peak = macd_peaks[-2][1]
        
        if (latest_price_peak > prev_price_peak and 
            latest_macd_peak < prev_macd_peak):
            return 'bearish_divergence'
    
    # Check for bullish divergence
    if len(price_troughs) >= 2 and len(macd_troughs) >= 2:
        latest_price_trough = price_troughs[-1][1]
        prev_price_trough = price_troughs[-2][1]
        latest_macd_trough = macd_troughs[-1][1]
        prev_macd_trough = macd_troughs[-2][1]
        
        if (latest_price_trough < prev_price_trough and 
            latest_macd_trough > prev_macd_trough):
            return 'bullish_divergence'
    
    return None


def detect_volume_surge(volume, lookback=20, surge_threshold=1.5):
    """
    Detect volume surge in consolidation - accumulation before breakout
    
    Returns:
        - True if volume surge detected without corresponding price move
        - False otherwise
    """
    if len(volume) < lookback:
        return False
    
    recent_volume = volume[-lookback:]
    volume_avg = recent_volume.mean()
    current_volume = volume.iloc[-1]
    
    # Check if current volume is significantly above average
    if current_volume > volume_avg * surge_threshold:
        # Check if this is a surge (not just high volume day)
        # Compare with previous days
        if len(volume) >= lookback + 5:
            prev_volume_avg = volume[-(lookback+5):-5].mean()
            if current_volume > prev_volume_avg * surge_threshold:
                return True
    
    return False


def detect_consolidation_base(close, lookback=20, tightness_threshold=0.05):
    """
    Detect consolidation/base formation - setup for breakout
    
    Returns:
        - 'tight_base': Price consolidating in tight range
        - 'ascending_base': Price making higher lows
        - 'flat_base': Price moving sideways
        - None: No clear base
    """
    if len(close) < lookback:
        return None
    
    recent_close = close[-lookback:]
    price_range = recent_close.max() - recent_close.min()
    avg_price = recent_close.mean()
    range_pct = (price_range / avg_price) * 100
    
    # Tight base: price range < 5% of average
    if range_pct < tightness_threshold * 100:
        # Check if making higher lows (ascending base)
        lows = []
        for i in range(2, len(recent_close) - 2):
            if (recent_close.iloc[i] < recent_close.iloc[i-1] and 
                recent_close.iloc[i] < recent_close.iloc[i-2] and
                recent_close.iloc[i] < recent_close.iloc[i+1] and
                recent_close.iloc[i] < recent_close.iloc[i+2]):
                lows.append(recent_close.iloc[i])
        
        if len(lows) >= 2:
            if lows[-1] > lows[-2]:
                return 'ascending_base'
        
        return 'tight_base'
    
    # Flat base: price moving sideways with low volatility
    if range_pct < 0.15 * 100:  # Range < 15%
        return 'flat_base'
    
    return None


def detect_volatility_compression(atr_values, lookback=20, compression_threshold=0.7):
    """
    Detect volatility compression (Bollinger Band Squeeze) - setup for explosive move
    
    Returns:
        - True if volatility is compressing (ATR declining)
        - False otherwise
    """
    if len(atr_values) < lookback:
        return False
    
    recent_atr = atr_values[-lookback:]
    current_atr = atr_values.iloc[-1]
    avg_atr = recent_atr.mean()
    
    # Check if current ATR is significantly below average (compression)
    if current_atr < avg_atr * compression_threshold:
        return True
    
    return False


def calculate_price_extension(current_price, ema50):
    """
    Calculate how extended price is above EMA50
    
    Returns:
        - Percentage extension above EMA50
        - None if EMA50 not available
    """
    if ema50 is None or ema50 <= 0:
        return None
    
    if current_price > ema50:
        return ((current_price / ema50) - 1) * 100
    else:
        return ((ema50 / current_price) - 1) * -100  # Negative if below


def detect_adx_trend(adx_series, periods=5):
    """
    Detect if ADX is rising or falling
    
    Returns:
        - 'rising': ADX increasing (trend strengthening)
        - 'falling': ADX decreasing (trend weakening)
        - 'stable': ADX relatively stable
        - None: Not enough data
    """
    if adx_series is None or len(adx_series) < periods + 1:
        return None
    
    current_adx = adx_series.iloc[-1]
    past_adx = adx_series.iloc[-(periods+1)]
    
    if pd.isna(current_adx) or pd.isna(past_adx):
        return None
    
    change_pct = ((current_adx / past_adx) - 1) * 100
    
    if change_pct > 10:  # Rising by 10%+
        return 'rising'
    elif change_pct < -10:  # Falling by 10%+
        return 'falling'
    else:
        return 'stable'
