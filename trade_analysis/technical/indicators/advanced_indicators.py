"""
Advanced Indicators: Hash Ribbon and Price Intensity (PI) Indicator
"""

import pandas as pd
import numpy as np
import yfinance as yf


def calculate_hash_ribbon(btc_ticker="BTC-USD", period="2y"):
    """
    Calculate Hash Ribbon indicator for Bitcoin
    Note: This requires hash rate data, which we'll approximate using price volatility
    and volume patterns. For true Hash Ribbon, you'd need actual hash rate data.
    
    For stocks/other assets, we'll use a similar concept with volume/volatility.
    """
    try:
        ticker = yf.Ticker(btc_ticker)
        df = ticker.history(period=period)
        if len(df) < 60:
            return None, None
        
        # Approximate hash rate using price volatility and volume
        # In real Hash Ribbon, this would be actual network hash rate
        # We'll use a proxy: rolling volatility * volume as a stress indicator
        df['volatility'] = df['Close'].rolling(window=30).std()
        df['volume_ma'] = df['Volume'].rolling(window=30).mean()
        df['stress_proxy'] = df['volatility'] * df['volume_ma']
        
        # Calculate 30-day and 60-day MAs of stress proxy
        ma30 = df['stress_proxy'].rolling(window=30).mean()
        ma60 = df['stress_proxy'].rolling(window=60).mean()
        
        # Hash Ribbon signal: when 30-day crosses above 60-day (recovery signal)
        signal = (ma30 > ma60) & (ma30.shift(1) <= ma60.shift(1))
        
        return signal, df
    except Exception as e:
        print(f"Error calculating Hash Ribbon: {e}")
        return None, None


def calculate_price_intensity(close, volume, period=14):
    """
    Price Intensity (PI) Indicator
    Combines price momentum, volume, and volatility to identify explosive move potential
    
    Formula:
    PI = (Price Momentum * Volume Strength * Volatility Compression) / Price Extension
    
    Higher PI = Higher potential for explosive move
    """
    if len(close) < period * 2:
        return None
    
    # Price momentum (rate of change)
    momentum = close.pct_change(period)
    
    # Volume strength (current volume vs average)
    volume_ma = volume.rolling(window=period).mean()
    volume_strength = volume / volume_ma
    
    # Volatility compression (low volatility = potential explosion)
    volatility = close.rolling(window=period).std()
    volatility_ma = volatility.rolling(window=period * 2).mean()
    volatility_compression = volatility_ma / (volatility + 0.0001)  # Inverse: low vol = high compression
    
    # Price extension (how far from moving average)
    price_ma = close.rolling(window=period * 2).mean()
    price_extension = abs((close - price_ma) / price_ma) + 0.01  # Avoid division by zero
    
    # Combine into PI
    pi = (momentum.abs() * volume_strength * volatility_compression) / price_extension
    
    # Normalize to 0-100 scale
    pi_normalized = (pi - pi.rolling(window=period * 4).min()) / (
        pi.rolling(window=period * 4).max() - pi.rolling(window=period * 4).min() + 0.0001
    ) * 100
    
    return pi_normalized


def detect_explosive_move_setup(close, volume, pi_value=None):
    """
    Detect setup for explosive moves using multiple factors
    Returns True if conditions suggest potential explosive move
    """
    if len(close) < 50:
        return False
    
    conditions_met = 0
    
    # Condition 1: Price consolidation (low volatility)
    volatility = close.rolling(window=20).std()
    volatility_ma = volatility.rolling(window=40).mean()
    if volatility.iloc[-1] < volatility_ma.iloc[-1] * 0.7:  # Volatility compression
        conditions_met += 1
    
    # Condition 2: Volume building (increasing volume trend)
    volume_ma_short = volume.rolling(window=10).mean()
    volume_ma_long = volume.rolling(window=30).mean()
    if volume_ma_short.iloc[-1] > volume_ma_long.iloc[-1] * 1.1:  # Volume building
        conditions_met += 1
    
    # Condition 3: Price near support (within 5% of recent low)
    recent_low = close.rolling(window=20).min()
    if close.iloc[-1] <= recent_low.iloc[-1] * 1.05:
        conditions_met += 1
    
    # Condition 4: PI indicator high (if available)
    if pi_value is not None and not pd.isna(pi_value):
        if pi_value > 70:  # High PI score
            conditions_met += 1
    
    # Condition 5: Positive momentum building
    momentum_short = close.pct_change(5)
    momentum_long = close.pct_change(20)
    if momentum_short.iloc[-1] > 0 and momentum_long.iloc[-1] > -0.1:  # Building momentum
        conditions_met += 1
    
    # Need at least 3 conditions for explosive move setup
    return conditions_met >= 3


def get_hash_ribbon_signal_for_stock(symbol, period="2y"):
    """
    Adapt Hash Ribbon concept for stocks using volume/volatility proxy
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if len(df) < 60:
            return None, None
        
        # Use volume * volatility as stress proxy (similar to hash rate stress)
        df['volatility'] = df['Close'].rolling(window=30).std()
        df['volume_ma'] = df['Volume'].rolling(window=30).mean()
        df['stress_proxy'] = df['volatility'] * df['volume_ma']
        
        # Calculate 30-day and 60-day MAs
        ma30 = df['stress_proxy'].rolling(window=30).mean()
        ma60 = df['stress_proxy'].rolling(window=60).mean()
        
        # Signal: when 30-day crosses above 60-day (recovery from stress)
        signal = (ma30 > ma60) & (ma30.shift(1) <= ma60.shift(1))
        
        return signal, df
    except Exception as e:
        return None, None
