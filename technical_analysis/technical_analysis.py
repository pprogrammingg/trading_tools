import json
import time
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import pickle
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange
import numpy as np
from tradingview_indicators import RSI, ema, sma
from ta.trend import SMAIndicator

# Data source: yFinance only

# ======================================================
# CONFIG
# ======================================================
# NOTE: Both calculation methods use the same yFinance data source.
# Differences come from using different calculation libraries:
# - yfinance: uses 'ta' library (standard technical analysis)
# - tradingview: uses 'tradingview-indicators' library (matches TradingView formulas)
# ======================================================

# ======================================================
# SYMBOL CONFIGURATION - Organized by Category
# ======================================================

TECH_STOCKS = [
    # Quantum Computing (grouped together)
    "IONQ", "QTUM", "QBTS", "RGTI",
    # Crypto Mining/Blockchain (grouped together)
    "MNRS", "IREN", "BMNR", "HUT", "CIFR", "APLD", "WULF", "CORZ", "BITF", "CLSK", "WGMI",
    # Other Tech Stocks
    "NFLX", "TMUS", "ARM", "NOW",
]

CRYPTOCURRENCIES = [
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum
    "SOL-USD",  # Solana
]

PRECIOUS_METALS = [
    "GC=F",  # Gold Futures
    "SI=F",  # Silver Futures
    "PA=F",  # Palladium Futures
    "PL=F",  # Platinum Futures
]

# Combine all symbols
SYMBOLS = TECH_STOCKS + CRYPTOCURRENCIES + PRECIOUS_METALS

TIMEFRAMES = {
    "1W": "7D",      # 7 calendar days (not trading days)
    "2W": "14D",     # 14 calendar days
    "1M": "30D",     # 30 calendar days
    "2M": "60D",     # 60 calendar days
    "6M": "180D",    # 180 calendar days
}

INDICATOR_WINDOWS = {
    "rsi": 14,
    "stoch_rsi": 14,
    "atr": 14,
}

# Output directory for category-based results
RESULTS_DIR = Path("result_scores")
RESULTS_DIR.mkdir(exist_ok=True)

# Data cache directory
CACHE_DIR = Path("data_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Legacy support - keep old constants for backward compatibility
TECH_STOCKS = []
CRYPTOCURRENCIES = []
PRECIOUS_METALS = []
SYMBOLS = []

def load_symbols_config(config_path: str = "symbols_config.json") -> dict:
    """Load symbols configuration from JSON file."""
    config_file = Path(config_path)
    if not config_file.exists():
        # Try parent directory
        config_file = Path(__file__).parent.parent / config_path
        if not config_file.exists():
            raise FileNotFoundError(f"Symbols config not found: {config_path}")
    
    with open(config_file, 'r') as f:
        return json.load(f)

# ======================================================
# DATA HELPERS
# ======================================================

def should_refresh_cache(cache_file: Path, force_refresh: bool = False) -> bool:
    """
    Determine if cached data should be refreshed.
    Returns True if:
    - force_refresh is True (explicit refresh flag)
    - Cache doesn't exist
    - Cache was last updated before the most recent Sunday 4 PM UTC (to capture weekly closes)
    """
    if force_refresh:
        return True
    
    if not cache_file.exists():
        return True
    
    # Get cache file modification time
    cache_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    
    # Find the most recent Sunday 4 PM UTC that has already passed
    # This ensures weekly closes (Sunday 4 PM) are always captured
    current_weekday = now.weekday()  # 0=Monday, 6=Sunday
    current_hour = now.hour
    
    if current_weekday == 6:  # Today is Sunday
        if current_hour >= 16:  # After 4 PM - use today's 4 PM as cutoff
            last_sunday_4pm = now.replace(hour=16, minute=0, second=0, microsecond=0)
        else:  # Before 4 PM - use last week's Sunday 4 PM as cutoff
            last_sunday_4pm = (now - timedelta(days=7)).replace(hour=16, minute=0, second=0, microsecond=0)
    else:
        # Not Sunday - find the most recent Sunday 4 PM that has passed
        # Monday=0, so days since Sunday = 1
        # Tuesday=1, so days since Sunday = 2, etc.
        days_since_sunday = (current_weekday + 1) % 7
        if days_since_sunday == 0:  # This shouldn't happen, but handle it
            days_since_sunday = 1
        last_sunday_4pm = (now - timedelta(days=days_since_sunday)).replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Refresh if cache is older than the most recent Sunday 4 PM UTC
    # This ensures we always have data that includes the weekly close
    if cache_mtime < last_sunday_4pm:
        return True
    
    return False

def get_cache_path(category: str, symbol: str) -> Path:
    """Get cache file path for a symbol in a category."""
    category_dir = CACHE_DIR / category
    category_dir.mkdir(exist_ok=True)
    # Sanitize symbol for filename (replace special chars)
    safe_symbol = symbol.replace("=", "_").replace("-", "_")
    return category_dir / f"{safe_symbol}.pkl"

def load_cached_data(category: str, symbol: str, force_refresh: bool = False):
    """
    Load cached data if available and fresh.
    Returns (dataframe, is_cached)
    """
    cache_file = get_cache_path(category, symbol)
    
    if not should_refresh_cache(cache_file, force_refresh=force_refresh):
        try:
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                return df, True
        except Exception as e:
            # If cache read fails, continue to download
            pass
    
    return pd.DataFrame(), False

def save_cached_data(category: str, symbol: str, df: pd.DataFrame):
    """Save downloaded data to cache."""
    if len(df) == 0:
        return
    
    cache_file = get_cache_path(category, symbol)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
    except Exception as e:
        # If cache write fails, continue without caching
        pass

def download_data(symbol, period="5y", interval="1d", category: str = None, use_cache: bool = True, force_refresh: bool = False):
    """
    Download data from yFinance with optional caching.
    
    Args:
        symbol: Symbol to download
        period: Data period (default: "5y")
        interval: Data interval (default: "1d")
        category: Category name for caching (optional)
        use_cache: Whether to use cache (default: True)
        force_refresh: Force refresh even if cache exists (default: False)
    """
    # Try to load from cache if category provided and caching enabled
    if use_cache and category and not force_refresh:
        cached_df, is_cached = load_cached_data(category, symbol, force_refresh=force_refresh)
        if is_cached:
            return cached_df
    
    # Download fresh data
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        
        # Save to cache if category provided and caching enabled
        if use_cache and category and len(df) > 0:
            save_cached_data(category, symbol, df)
        
        return df
    except Exception as e:
        print(f"  yFinance error for {symbol}: {e}")
        return pd.DataFrame()

def resample_ohlcv(df, rule):
    return (
        df.resample(rule)
        .agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        })
        .dropna()
    )

def convert_to_gold_terms(df, gold_df):
    """Convert price data to gold terms (price / gold_price)"""
    if len(gold_df) == 0 or len(df) == 0:
        return pd.DataFrame()
    
    # Create a combined index with all dates from both dataframes
    all_dates = df.index.union(gold_df.index).sort_values()
    
    # Reindex both dataframes to the combined index and forward fill
    df_reindexed = df.reindex(all_dates).ffill()
    gold_reindexed = gold_df[["Close"]].reindex(all_dates).ffill()
    
    # Now align to symbol dates only
    aligned_dates = df.index
    df_aligned = df_reindexed.loc[aligned_dates]
    gold_aligned = gold_reindexed.loc[aligned_dates]
    
    # Check if we have gold prices for all dates
    if gold_aligned["Close"].isna().any():
        # Try backward fill for any remaining NaN
        gold_aligned = gold_aligned.bfill()
        if gold_aligned["Close"].isna().any():
            return pd.DataFrame()  # Can't convert if we don't have gold prices
    
    gold_prices = gold_aligned["Close"]
    
    # Convert OHLC to gold terms
    gold_terms = pd.DataFrame({
        "Open": df_aligned["Open"] / gold_prices,
        "High": df_aligned["High"] / gold_prices,
        "Low": df_aligned["Low"] / gold_prices,
        "Close": df_aligned["Close"] / gold_prices,
        "Volume": df_aligned["Volume"],  # Volume stays the same
    }, index=aligned_dates)
    
    return gold_terms.dropna()

# ======================================================
# GMMA
# ======================================================

def compute_gmma(close):
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]

    short_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in short_periods})
    long_emas = pd.DataFrame({f"ema_{p}": close.ewm(span=p, adjust=False).mean() for p in long_periods})

    return short_emas, long_emas

# ======================================================
# TRADINGVIEW INDICATORS (using tradingview-indicators library)
# NOTE: Using same yFinance data source, but different calculation methods
# to match TradingView's indicator formulas
# ======================================================

def compute_stochrsi_tv(rsi_values, k_period=3, d_period=3, stoch_period=14):
    """
    Compute StochRSI using TradingView method:
    1. Calculate RSI
    2. Apply Stochastic to RSI values
    3. Smooth %K and %D
    """
    if len(rsi_values) < stoch_period + k_period + d_period:
        return None, None
    
    # Calculate Stochastic of RSI
    stoch_values = []
    for i in range(stoch_period - 1, len(rsi_values)):
        rsi_window = rsi_values[i - stoch_period + 1:i + 1]
        rsi_low = rsi_window.min()
        rsi_high = rsi_window.max()
        rsi_current = rsi_values.iloc[i]
        
        if rsi_high - rsi_low == 0:
            stoch_value = 0
        else:
            stoch_value = (rsi_current - rsi_low) / (rsi_high - rsi_low)
        stoch_values.append(stoch_value)
    
    stoch_series = pd.Series(stoch_values, index=rsi_values.index[stoch_period - 1:])
    
    # Smooth %K (K-period SMA of StochRSI)
    stoch_k = stoch_series.rolling(window=k_period).mean()
    
    # Smooth %D (D-period SMA of %K)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    
    return stoch_k, stoch_d

def compute_indicators_tv(df, category: str = None, is_gold_denominated: bool = False):
    """
    Compute indicators using tradingview-indicators library (TradingView-style calculations)
    
    Args:
        df: DataFrame with OHLCV data
        category: Category name (e.g., 'cryptocurrencies') for asset-class aware scoring
        is_gold_denominated: Whether this is gold-denominated analysis (less harsh ATR penalties)
    """
    result = {
        "rsi": None,
        "atr": None,
        "atr_pct": None,
        "close": None,
        "ema50": None,
        "ema200": None,
        "sma50": None,
        "sma200": None,
        "4w_low": None,
        "gmma_bullish": None,
        "gmma_early_expansion": None,
        "macd_bullish": None,
        "macd_positive": None,
        "volume_above_avg": None,
        "momentum": None,
        "score": 0,
        "score_breakdown": {}
    }
    
    if len(df) == 0:
        return result
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    
    result["close"] = round(close.iloc[-1], 4)
    
    # === Key Moving Averages (simplified - only 50 and 200) ===
    # EMA50
    if len(close) >= 50:
        ema50_values = ema(close, 50)
        result["ema50"] = round(ema50_values.iloc[-1], 4)
    
    # EMA200
    if len(close) >= 200:
        ema200_values = ema(close, 200)
        result["ema200"] = round(ema200_values.iloc[-1], 4)
    
    # SMA50
    if len(close) >= 50:
        sma50_values = sma(close, 50)
        result["sma50"] = round(sma50_values.iloc[-1], 4)
    
    # SMA200
    if len(close) >= 200:
        sma200_values = sma(close, 200)
        result["sma200"] = round(sma200_values.iloc[-1], 4)
    
    # === GMMA ===
    short_periods = [3, 5, 8, 10, 12, 15]
    long_periods = [30, 35, 40, 45, 50, 60]
    
    try:
        short_emas = pd.DataFrame({f"ema_{p}": ema(close, p) for p in short_periods})
        long_emas = pd.DataFrame({f"ema_{p}": ema(close, p) for p in long_periods})
        
        short_last = short_emas.iloc[-1]
        long_last = long_emas.iloc[-1]
        result["gmma_bullish"] = bool(short_last.min() > long_last.max())
        
        short_spread = short_last.max() - short_last.min()
        result["gmma_early_expansion"] = bool((short_last.mean() > long_last.mean()) and (short_spread / close.iloc[-1] < 0.03))
    except:
        pass
    
    # === Recent low (4 weeks) ===
    if len(close) >= 4:
        result["4w_low"] = round(close[-4:].min(), 4)
    
    # === RSI ===
    if len(close) >= INDICATOR_WINDOWS["rsi"]:
        rsi_values = RSI(close, INDICATOR_WINDOWS["rsi"])
        rsi_value = rsi_values.iloc[-1]
        result["rsi"] = round(rsi_value, 2)
        if rsi_value < 30:
            result["score"] += 2
            result["score_breakdown"]["rsi_oversold"] = 2
        elif rsi_value < 40:
            result["score"] += 1  # Slightly oversold - mild bullish signal
            result["score_breakdown"]["rsi_slightly_oversold"] = 1
        elif rsi_value > 70:
            result["score"] -= 2  # Stronger penalty for overbought
            result["score_breakdown"]["rsi_overbought"] = -2
        elif rsi_value > 65:
            result["score"] -= 1  # Moderate penalty for approaching overbought
            result["score_breakdown"]["rsi_approaching_overbought"] = -1
    
    # StochRSI removed - redundant with RSI for momentum/overbought-oversold signals
    
    # === ATR (simplified calculation) ===
    if len(close) >= INDICATOR_WINDOWS["atr"]:
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_values = tr.rolling(window=INDICATOR_WINDOWS["atr"]).mean()
        atr_value = atr_values.iloc[-1]
        result["atr"] = round(atr_value, 4)
        atr_pct = (atr_value / close.iloc[-1]) * 100
        result["atr_pct"] = round(atr_pct, 2)
        
        # ATR is kept as data but NOT used for scoring
        # Volatility is a risk metric, not a buy/sell signal
        # High volatility can mean opportunity (crypto, growth stocks, small caps)
        # Volatility is already reflected in momentum and price action indicators
        # No penalties or bonuses for ATR - focus on directional signals instead
    
    # === MACD (simplified - using EMA difference) ===
    if len(close) >= 26:
        ema12 = ema(close, 12)
        ema26 = ema(close, 26)
        macd_line = ema12 - ema26
        signal_line = ema(macd_line, 9)
        macd_diff = macd_line - signal_line
        
        if len(macd_line) > 0 and len(signal_line) > 0:
            result["macd_bullish"] = bool(macd_line.iloc[-1] > signal_line.iloc[-1])
            result["macd_positive"] = bool(macd_diff.iloc[-1] > 0)
            if result["macd_bullish"] and result["macd_positive"]:
                result["score"] += 1
                result["score_breakdown"]["macd_bullish"] = 1

    # === Volume Analysis ===
    if len(volume) >= 20:
        volume_avg = volume.rolling(window=20).mean()
        if len(volume_avg) > 0 and volume_avg.iloc[-1] > 0:
            volume_ratio = volume.iloc[-1] / volume_avg.iloc[-1]
            result["volume_above_avg"] = bool(volume_ratio > 1.2)
            if result["volume_above_avg"]:
                result["score"] += 1
                result["score_breakdown"]["volume_confirmation"] = 1

    # === Momentum (Rate of Change) ===
    # Use approximately 10-14 periods for momentum calculation
    # For resampled data, this represents different calendar days per timeframe
    # Cap lookback to reasonable value to avoid extreme calculations
    lookback = min(14, max(2, len(close) - 1))
    if lookback >= 2 and len(close) > lookback:
        momentum = ((close.iloc[-1] / close.iloc[-lookback]) - 1) * 100
        result["momentum"] = round(momentum, 2)
        # Cap extreme values (likely data issues, gaps, or very short timeframes)
        if abs(momentum) > 50:
            momentum = 50 if momentum > 0 else -50
            result["momentum"] = round(momentum, 2)
        
        # More conservative momentum scoring
        if momentum > 15:  # Very strong momentum (>15%)
            result["score"] += 1
            result["score_breakdown"]["very_strong_momentum"] = 1
        elif momentum > 8:  # Strong momentum (8-15%)
            result["score"] += 0.5
            result["score_breakdown"]["strong_momentum"] = 0.5
        elif momentum > 3:  # Moderate momentum (3-8%)
            result["score"] += 0.5
            result["score_breakdown"]["moderate_momentum"] = 0.5
        elif momentum < -15:  # Very strong negative momentum
            result["score"] -= 1.5
            result["score_breakdown"]["very_negative_momentum"] = -1.5
        elif momentum < -8:  # Strong negative momentum
            result["score"] -= 1
            result["score_breakdown"]["negative_momentum"] = -1

    # === Score additions from price vs Moving Averages / GMMA conditions ===
    # NOTE: Using only EMAs for scoring to avoid double-counting with SMAs
    # SMAs are still calculated and stored for reference, but not used in scoring
    current_price = close.iloc[-1]
    
    # Price above key EMAs (bullish) - more conservative scoring
    # Only count EMA50 and EMA200 as they're more significant
    if result["ema50"] is not None and current_price > result["ema50"]:
        result["score"] += 0.5
        result["score_breakdown"]["price_above_ema50"] = 0.5
    if result["ema200"] is not None and current_price > result["ema200"]:
        result["score"] += 1
        result["score_breakdown"]["price_above_ema200"] = 1
    
    # Golden Cross / Death Cross detection (SMA50 vs SMA200) - major signal
    if result["sma50"] is not None and result["sma200"] is not None:
        if result["sma50"] > result["sma200"]:
            result["score"] += 1.5
            result["score_breakdown"]["golden_cross"] = 1.5
        else:
            result["score"] -= 1.5
            result["score_breakdown"]["death_cross"] = -1.5
    
    # GMMA conditions (simplified - removed compressed as it's less reliable)
    if result["gmma_bullish"]:
        result["score"] += 2
        result["score_breakdown"]["gmma_bullish"] = 2
    if result["gmma_early_expansion"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_early_expansion"] = 1
    if result["4w_low"] is not None and close.iloc[-1] <= result["4w_low"]:
        result["score"] += 1
        result["score_breakdown"]["at_4w_low"] = 1

    return result

# ======================================================
# YFINANCE INDICATORS (using ta library)
# NOTE: Using yFinance data with ta library calculations
# ======================================================

def compute_indicators_with_score(df, category: str = None, is_gold_denominated: bool = False):
    """
    Compute indicators using ta library with scoring.
    
    Args:
        df: DataFrame with OHLCV data
        category: Category name (e.g., 'cryptocurrencies') for asset-class aware scoring
        is_gold_denominated: Whether this is gold-denominated analysis (less harsh ATR penalties)
    """
    result = {
        "rsi": None,
        "atr": None,
        "atr_pct": None,  # ATR as percentage of price
        "close": None,
        "ema50": None,
        "ema200": None,
        "sma50": None,
        "sma200": None,
        "4w_low": None,
        "gmma_bullish": None,
        "gmma_early_expansion": None,
        "macd_bullish": None,  # MACD line above signal
        "macd_positive": None,  # MACD histogram positive
        "volume_above_avg": None,  # Volume above 20-day average
        "momentum": None,  # Rate of change
        "score": 0,
        "score_breakdown": {}  # Track what contributed to score
    }

    if len(df) == 0:
        return result

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    result["close"] = round(close.iloc[-1], 4)

    # === Key Moving Averages (simplified - only 50 and 200) ===
    # EMA50
    if len(close) >= 50:
        ema50 = close.ewm(span=50, adjust=False).mean()
        result["ema50"] = round(ema50.iloc[-1], 4)
    
    # EMA200
    if len(close) >= 200:
        ema200 = close.ewm(span=200, adjust=False).mean()
        result["ema200"] = round(ema200.iloc[-1], 4)
    
    # SMA50
    if len(close) >= 50:
        sma50 = SMAIndicator(close, window=50).sma_indicator()
        result["sma50"] = round(sma50.iloc[-1], 4)
    
    # SMA200
    if len(close) >= 200:
        sma200 = SMAIndicator(close, window=200).sma_indicator()
        result["sma200"] = round(sma200.iloc[-1], 4)

    # === GMMA ===
    short_emas, long_emas = compute_gmma(close)
    try:
        short_last = short_emas.iloc[-1]
        long_last = long_emas.iloc[-1]
        result["gmma_bullish"] = short_last.min() > long_last.max()

        short_spread = short_last.max() - short_last.min()
        result["gmma_early_expansion"] = (short_last.mean() > long_last.mean()) and (short_spread / close.iloc[-1] < 0.03)
    except IndexError:
        # Not enough data for GMMA
        pass

    # === Recent low (4 weeks) ===
    if len(close) >= 4:
        result["4w_low"] = round(close[-4:].min(), 4)

    # === RSI ===
    if len(close) >= INDICATOR_WINDOWS["rsi"]:
        rsi = RSIIndicator(close, INDICATOR_WINDOWS["rsi"]).rsi()
        rsi_value = rsi.iloc[-1]
        result["rsi"] = round(rsi_value, 2)
        if rsi_value < 30:
            result["score"] += 2
            result["score_breakdown"]["rsi_oversold"] = 2
        elif rsi_value < 40:
            result["score"] += 1  # Slightly oversold - mild bullish signal
            result["score_breakdown"]["rsi_slightly_oversold"] = 1
        elif rsi_value > 70:
            result["score"] -= 2  # Stronger penalty for overbought
            result["score_breakdown"]["rsi_overbought"] = -2
        elif rsi_value > 65:
            result["score"] -= 1  # Moderate penalty for approaching overbought
            result["score_breakdown"]["rsi_approaching_overbought"] = -1

    # StochRSI removed - redundant with RSI for momentum/overbought-oversold signals

    # === ATR ===
    if len(close) >= INDICATOR_WINDOWS["atr"]:
        atr = AverageTrueRange(high, low, close, INDICATOR_WINDOWS["atr"]).average_true_range()
        atr_value = atr.iloc[-1]
        result["atr"] = round(atr_value, 4)
        atr_pct = (atr_value / close.iloc[-1]) * 100
        result["atr_pct"] = round(atr_pct, 2)
        
        # ATR is kept as data but NOT used for scoring
        # Volatility is a risk metric, not a buy/sell signal
        # High volatility can mean opportunity (crypto, growth stocks, small caps)
        # Volatility is already reflected in momentum and price action indicators
        # No penalties or bonuses for ATR - focus on directional signals instead

    # === MACD ===
    if len(close) >= 26:  # MACD needs at least 26 periods
        macd = MACD(close)
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()
        macd_diff = macd.macd_diff()
        
        if len(macd_line) > 0 and len(macd_signal) > 0:
            result["macd_bullish"] = bool(macd_line.iloc[-1] > macd_signal.iloc[-1])
            result["macd_positive"] = bool(macd_diff.iloc[-1] > 0)
            if result["macd_bullish"] and result["macd_positive"]:
                result["score"] += 1
                result["score_breakdown"]["macd_bullish"] = 1

    # === Volume Analysis ===
    if len(volume) >= 20:
        volume_avg = volume.rolling(window=20).mean()
        if len(volume_avg) > 0 and volume_avg.iloc[-1] > 0:
            volume_ratio = volume.iloc[-1] / volume_avg.iloc[-1]
            result["volume_above_avg"] = bool(volume_ratio > 1.2)  # 20% above average
            if result["volume_above_avg"]:
                result["score"] += 1  # Volume confirmation
                result["score_breakdown"]["volume_confirmation"] = 1

    # === Momentum (Rate of Change) ===
    # Use approximately 10-14 periods for momentum calculation
    # For resampled data, this represents different calendar days per timeframe
    # Cap lookback to reasonable value to avoid extreme calculations
    lookback = min(14, max(2, len(close) - 1))
    if lookback >= 2 and len(close) > lookback:
        momentum = ((close.iloc[-1] / close.iloc[-lookback]) - 1) * 100
        result["momentum"] = round(momentum, 2)
        # Cap extreme values (likely data issues, gaps, or very short timeframes)
        if abs(momentum) > 50:
            momentum = 50 if momentum > 0 else -50
            result["momentum"] = round(momentum, 2)
        
        # More conservative momentum scoring
        if momentum > 15:  # Very strong momentum (>15%)
            result["score"] += 1
            result["score_breakdown"]["very_strong_momentum"] = 1
        elif momentum > 8:  # Strong momentum (8-15%)
            result["score"] += 0.5
            result["score_breakdown"]["strong_momentum"] = 0.5
        elif momentum > 3:  # Moderate momentum (3-8%)
            result["score"] += 0.5
            result["score_breakdown"]["moderate_momentum"] = 0.5
        elif momentum < -15:  # Very strong negative momentum
            result["score"] -= 1.5
            result["score_breakdown"]["very_negative_momentum"] = -1.5
        elif momentum < -8:  # Strong negative momentum
            result["score"] -= 1
            result["score_breakdown"]["negative_momentum"] = -1

    # === Score additions from price vs Moving Averages / GMMA conditions ===
    # NOTE: Using only EMAs for scoring to avoid double-counting with SMAs
    # SMAs are still calculated and stored for reference, but not used in scoring
    current_price = close.iloc[-1]
    
    # Price above key EMAs (bullish) - more conservative scoring
    # Only count EMA50 and EMA200 as they're more significant
    if result["ema50"] is not None and current_price > result["ema50"]:
        result["score"] += 0.5
        result["score_breakdown"]["price_above_ema50"] = 0.5
    if result["ema200"] is not None and current_price > result["ema200"]:
        result["score"] += 1
        result["score_breakdown"]["price_above_ema200"] = 1
    
    # Golden Cross / Death Cross detection (SMA50 vs SMA200) - major signal
    if result["sma50"] is not None and result["sma200"] is not None:
        if result["sma50"] > result["sma200"]:
            result["score"] += 1.5
            result["score_breakdown"]["golden_cross"] = 1.5
        else:
            result["score"] -= 1.5
            result["score_breakdown"]["death_cross"] = -1.5
    
    # GMMA conditions (simplified - removed compressed as it's less reliable)
    if result["gmma_bullish"]:
        result["score"] += 2
        result["score_breakdown"]["gmma_bullish"] = 2
    if result["gmma_early_expansion"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_early_expansion"] = 1
    if result["4w_low"] is not None and close.iloc[-1] <= result["4w_low"]:
        result["score"] += 1
        result["score_breakdown"]["at_4w_low"] = 1
    
    # === Conflict Detection ===
    # Penalize conflicting signals (e.g., overbought RSI with strong momentum)
    if result.get("rsi") is not None and result.get("momentum") is not None:
        if result["rsi"] > 70 and result["momentum"] > 15:
            result["score"] -= 1  # Overbought + extreme momentum = warning
            result["score_breakdown"]["overbought_momentum_conflict"] = -1
        elif result["rsi"] < 30 and result["momentum"] < -15:
            result["score"] += 0.5  # Oversold + extreme negative momentum = potential reversal
            result["score_breakdown"]["oversold_reversal_potential"] = 0.5

    return result

# ======================================================
# RELATIVE UPSIDE/DOWNSIDE POTENTIAL
# ======================================================

def calculate_relative_potential(symbol, df, category_symbols):
    """
    Calculate relative upside/downside potential based on:
    1. Technical levels (recent highs/lows, support/resistance)
    2. Market cap comparison within category (for stocks)
    3. Price position relative to historical range
    """
    if len(df) == 0:
        return {
            "upside_potential_pct": None,
            "downside_potential_pct": None,
            "relative_to_category": None,
            "price_vs_52w_range": None
        }
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    current_price = close.iloc[-1]
    
    result = {}
    
    # 1. Technical levels: Calculate distance to recent highs/lows
    # For daily data, 52 weeks = ~252 trading days (52 * 5 trading days/week)
    # Use 252 periods for daily data, or adjust based on data frequency
    lookback_periods = min(252, len(close))  # 52 weeks (~252 trading days) or available data
    recent_high = high[-lookback_periods:].max()
    recent_low = low[-lookback_periods:].min()
    
    # Upside potential: distance to recent high
    if recent_high > current_price:
        upside_pct = ((recent_high / current_price) - 1) * 100
        result["upside_potential_pct"] = round(upside_pct, 2)
    else:
        result["upside_potential_pct"] = 0  # Already at or above recent high
    
    # Downside potential: distance to recent low
    if recent_low < current_price:
        downside_pct = ((current_price / recent_low) - 1) * 100
        result["downside_potential_pct"] = round(downside_pct, 2)
    else:
        result["downside_potential_pct"] = 0  # Already at or below recent low
    
    # 2. Price position in 52-week range (0 = at low, 100 = at high)
    if recent_high > recent_low:
        price_position = ((current_price - recent_low) / (recent_high - recent_low)) * 100
        result["price_vs_52w_range"] = round(price_position, 1)
    else:
        result["price_vs_52w_range"] = 50  # Neutral if no range
    
    # 3. Market cap comparison (for stocks only, not crypto/futures)
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        market_cap = info.get('marketCap') or info.get('totalAssets')
        
        if market_cap and len(category_symbols) > 1:
            # Get market caps for category peers
            peer_caps = {}
            for peer_symbol in category_symbols:
                if peer_symbol != symbol:
                    try:
                        peer_ticker = yf.Ticker(peer_symbol)
                        peer_info = peer_ticker.info
                        peer_cap = peer_info.get('marketCap') or peer_info.get('totalAssets')
                        if peer_cap:
                            peer_caps[peer_symbol] = peer_cap
                    except:
                        continue
            
            if peer_caps:
                avg_peer_cap = sum(peer_caps.values()) / len(peer_caps)
                if avg_peer_cap > 0:
                    # Relative market cap (1.0 = average, >1 = larger, <1 = smaller)
                    relative_cap = market_cap / avg_peer_cap
                    result["relative_to_category"] = {
                        "market_cap_ratio": round(relative_cap, 2),
                        "market_cap": market_cap,
                        "avg_peer_cap": round(avg_peer_cap, 0),
                        "peer_count": len(peer_caps)
                    }
        else:
            result["relative_to_category"] = None
    except:
        result["relative_to_category"] = None
    
    return result

# ======================================================
# UTIL
# ======================================================

def json_safe(obj):
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if hasattr(obj, "item"):
        return obj.item()
    return obj

# ======================================================
# MAIN
# ======================================================

def process_category(category_name: str, symbols: list, gold_df=None, calculate_potential: bool = False, force_refresh: bool = False):
    """
    Process a single category of symbols.
    
    Args:
        category_name: Name of the category
        symbols: List of symbols to process
        gold_df: Pre-downloaded gold data (optional)
        calculate_potential: Whether to calculate relative potential (slower, requires API calls)
        
    Returns:
        Tuple of (results_dict, timings_dict)
    """
    # Benchmarking
    start_time = time.time()
    timings = {
        'gold_download': 0,
        'symbols': {},
        'json_write': 0,
    }
    
    results = {}
    
    print(f"\n{'=' * 60}")
    print(f"Processing category: {category_name.upper()}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"{'=' * 60}")
    
    # Download gold prices if not provided
    if gold_df is None:
        print("\nDownloading gold prices (GC=F) for gold-denominated analysis...")
        gold_start = time.time()
        gold_df = download_data("GC=F", category="gold", use_cache=True, force_refresh=force_refresh)
        timings['gold_download'] = time.time() - gold_start
        if len(gold_df) == 0:
            print("  Warning: Could not fetch gold prices. Gold-denominated analysis will be skipped.")
            gold_df = None
        else:
            cache_file = get_cache_path("gold", "GC=F")
            cache_status = " (cached)" if cache_file.exists() and not should_refresh_cache(cache_file, force_refresh=False) else ""
            print(f"  ✓ Gold prices downloaded ({len(gold_df)} rows){cache_status} [{timings['gold_download']:.2f}s]")
    
    # All symbols in this category share the same category list for relative comparisons
    category_symbols = symbols

    for symbol in symbols:
        symbol_start = time.time()
        print(f"\nProcessing {symbol}...")
        results[symbol] = {}
        
        # Initialize timing for this symbol
        if symbol not in timings['symbols']:
            timings['symbols'][symbol] = {
                'download': 0,
                'relative_potential': 0,
                'timeframes': {},
            }
        
        # Fetch data from yFinance (with caching)
        print(f"  Fetching data...", end=" ")
        download_start = time.time()
        base_df = download_data(symbol, category=category_name, use_cache=True, force_refresh=force_refresh)
        timings['symbols'][symbol]['download'] = time.time() - download_start
        if len(base_df) == 0:
            print("✗ (no data)")
            print(f"  Warning: No data available for {symbol}")
            continue
        
        # Check if data was from cache
        cache_file = get_cache_path(category_name, symbol)
        cache_status = " (cached)" if cache_file.exists() and not should_refresh_cache(cache_file, force_refresh=force_refresh) else ""
        print(f"✓ ({len(base_df)} rows){cache_status} [{timings['symbols'][symbol]['download']:.2f}s]")
        
        # Calculate relative potential using full dataset (not resampled)
        if calculate_potential:
            potential_start = time.time()
            relative_potential = calculate_relative_potential(symbol, base_df, category_symbols)
            timings['symbols'][symbol]['relative_potential'] = time.time() - potential_start
        else:
            relative_potential = {
                "upside_potential_pct": None,
                "downside_potential_pct": None,
                "relative_to_category": None,
                "price_vs_52w_range": None
            }
            timings['symbols'][symbol]['relative_potential'] = 0

        for label, rule in TIMEFRAMES.items():
            results[symbol][label] = {}
            
            # Initialize timing for this timeframe
            if label not in timings['symbols'][symbol]['timeframes']:
                timings['symbols'][symbol]['timeframes'][label] = {
                    'resample': 0,
                    'indicators_usd': 0,
                    'indicators_gold': 0,
                    'gold_conversion': 0,
                }
            
            # Resample
            resample_start = time.time()
            df_usd = resample_ohlcv(base_df, rule)
            timings['symbols'][symbol]['timeframes'][label]['resample'] = time.time() - resample_start
            
            if len(df_usd) == 0:
                results[symbol][label]["yfinance"] = {"error": "No data after resampling"}
                continue
            
            # Calculate indicators for USD-denominated prices
            indicators_start = time.time()
            indicators_ta_usd = compute_indicators_with_score(df_usd, category=category_name, is_gold_denominated=False)
            indicators_tv_usd = compute_indicators_tv(df_usd, category=category_name, is_gold_denominated=False)
            timings['symbols'][symbol]['timeframes'][label]['indicators_usd'] = time.time() - indicators_start
            
            # Add relative potential to indicators (same for all timeframes, calculated from full data)
            indicators_ta_usd["relative_potential"] = relative_potential
            indicators_tv_usd["relative_potential"] = relative_potential
            
            # Calculate indicators for Gold-denominated prices (if gold data available)
            indicators_ta_gold = None
            indicators_tv_gold = None
            
            if gold_df is not None and symbol != "GC=F":  # Skip gold for itself
                gold_conv_start = time.time()
                gold_resampled = resample_ohlcv(gold_df, rule)
                df_gold = convert_to_gold_terms(df_usd, gold_resampled)
                timings['symbols'][symbol]['timeframes'][label]['gold_conversion'] = time.time() - gold_conv_start
                
                if len(df_gold) > 0:
                    gold_indicators_start = time.time()
                    indicators_ta_gold = compute_indicators_with_score(df_gold, category=category_name, is_gold_denominated=True)
                    indicators_tv_gold = compute_indicators_tv(df_gold, category=category_name, is_gold_denominated=True)
                    timings['symbols'][symbol]['timeframes'][label]['indicators_gold'] = time.time() - gold_indicators_start
                    # Calculate relative potential for gold terms too (if enabled)
                    if calculate_potential:
                        gold_potential = calculate_relative_potential(symbol, df_gold, category_symbols)
                    else:
                        gold_potential = {
                            "upside_potential_pct": None,
                            "downside_potential_pct": None,
                            "relative_to_category": None,
                            "price_vs_52w_range": None
                        }
                    indicators_ta_gold["relative_potential"] = gold_potential
                    indicators_tv_gold["relative_potential"] = gold_potential
            
            results[symbol][label]["yfinance"] = {
                "usd": {
                    "ta_library": indicators_ta_usd,
                    "tradingview_library": indicators_tv_usd
                }
            }
            
            # Add gold-denominated results if available
            if indicators_ta_gold is not None:
                results[symbol][label]["yfinance"]["gold"] = {
                    "ta_library": indicators_ta_gold,
                    "tradingview_library": indicators_tv_gold
                }

    # Write JSON
    output_file = RESULTS_DIR / f"{category_name}_results.json"
    json_start = time.time()
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=json_safe)
    timings['json_write'] = time.time() - json_start

    total_time = time.time() - start_time
    
    # Print summary
    print(f"\n{'=' * 60}")
    print(f"BENCHMARK SUMMARY - {category_name.upper()}")
    print(f"{'=' * 60}")
    print(f"Total execution time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    print(f"\nBreakdown:")
    print(f"  Gold download: {timings['gold_download']:.2f}s ({timings['gold_download']/total_time*100:.1f}%)")
    
    # Per-symbol breakdown
    total_download = sum(t['download'] for t in timings['symbols'].values())
    total_potential = sum(t['relative_potential'] for t in timings['symbols'].values())
    total_indicators_usd = sum(
        sum(tf['indicators_usd'] for tf in s['timeframes'].values())
        for s in timings['symbols'].values()
    )
    total_indicators_gold = sum(
        sum(tf.get('indicators_gold', 0) for tf in s['timeframes'].values())
        for s in timings['symbols'].values()
    )
    total_gold_conv = sum(
        sum(tf.get('gold_conversion', 0) for tf in s['timeframes'].values())
        for s in timings['symbols'].values()
    )
    
    print(f"  Data downloads: {total_download:.2f}s ({total_download/total_time*100:.1f}%)")
    print(f"  Relative potential: {total_potential:.2f}s ({total_potential/total_time*100:.1f}%)")
    print(f"  USD indicators: {total_indicators_usd:.2f}s ({total_indicators_usd/total_time*100:.1f}%)")
    print(f"  Gold conversion: {total_gold_conv:.2f}s ({total_gold_conv/total_time*100:.1f}%)")
    print(f"  Gold indicators: {total_indicators_gold:.2f}s ({total_indicators_gold/total_time*100:.1f}%)")
    print(f"  JSON write: {timings['json_write']:.2f}s ({timings['json_write']/total_time*100:.1f}%)")
    
    # Slowest symbols
    symbol_times = {
        sym: sum([
            t['download'],
            t['relative_potential'],
            sum(tf['indicators_usd'] + tf.get('indicators_gold', 0) for tf in t['timeframes'].values())
        ])
        for sym, t in timings['symbols'].items()
    }
    if symbol_times:
        print(f"\nSlowest symbols (top 3):")
        for sym, t in sorted(symbol_times.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"  {sym}: {t:.2f}s")
    
    print(f"\n✓ Saved results to {output_file}")
    print(f"\nNote: Results use yFinance data with two calculation methods:")
    print(f"      - ta_library: Standard technical analysis library")
    print(f"      - tradingview_library: TradingView-style calculations")
    
    return results, timings


def main():
    """Main function - processes all categories or a specific category."""
    parser = argparse.ArgumentParser(description='Generate investment score sheets')
    parser.add_argument('--category', type=str, help='Process only this category (e.g., quantum, miner_hpc)')
    parser.add_argument('--config', type=str, default='symbols_config.json', help='Path to symbols config JSON')
    parser.add_argument('--calculate-potential', action='store_true', 
                       help='Calculate relative potential (slower, requires market cap API calls). '
                            'Saves ~30-45%% time when disabled.')
    parser.add_argument('--refresh', action='store_true',
                       help='Force refresh all data (ignore cache, re-download everything)')
    args = parser.parse_args()
    
    # Load symbols configuration
    try:
        symbols_config = load_symbols_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please create symbols_config.json with category structure.")
        sys.exit(1)
    
    # Download gold once (shared across all categories)
    print("=" * 60)
    print("BENCHMARKING MODE ENABLED")
    if not args.calculate_potential:
        print("⚠️  Relative potential calculation DISABLED (use --calculate-potential to enable)")
        print("   This saves ~30-45% execution time")
    print("=" * 60)
    print("\nDownloading gold prices (GC=F) for gold-denominated analysis...")
    gold_start = time.time()
    gold_df = download_data("GC=F", category="gold", use_cache=True, force_refresh=args.refresh)
    gold_download_time = time.time() - gold_start
    if len(gold_df) == 0:
        print("  Warning: Could not fetch gold prices. Gold-denominated analysis will be skipped.")
        gold_df = None
    else:
        cache_file = get_cache_path("gold", "GC=F")
        cache_status = " (cached)" if cache_file.exists() and not should_refresh_cache(cache_file, force_refresh=args.refresh) else ""
        print(f"  ✓ Gold prices downloaded ({len(gold_df)} rows){cache_status} [{gold_download_time:.2f}s]")
    
    # Process categories
    categories_to_process = [args.category] if args.category else list(symbols_config.keys())
    
    overall_start = time.time()
    all_results = {}
    all_timings = {}
    
    for category_name in categories_to_process:
        if category_name not in symbols_config:
            print(f"Warning: Category '{category_name}' not found in config. Skipping.")
            continue
        
        symbols = symbols_config[category_name]
        if not symbols:
            print(f"Warning: Category '{category_name}' has no symbols. Skipping.")
            continue
        
        results, timings = process_category(category_name, symbols, gold_df, args.calculate_potential, args.refresh)
        all_results[category_name] = results
        all_timings[category_name] = timings
    
    overall_time = time.time() - overall_start
    
    # Overall summary
    if len(categories_to_process) > 1:
        print(f"\n{'=' * 60}")
        print("OVERALL SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total time for all categories: {overall_time:.2f}s ({overall_time/60:.2f} minutes)")
        print(f"Categories processed: {len(categories_to_process)}")
        for cat in categories_to_process:
            if cat in all_timings:
                cat_time = sum([
                    all_timings[cat]['gold_download'],
                    sum(t['download'] + t['relative_potential'] + 
                        sum(sum(tf.values()) for tf in t['timeframes'].values())
                        for t in all_timings[cat]['symbols'].values()),
                    all_timings[cat]['json_write']
                ])
                print(f"  {cat}: {cat_time:.2f}s")

if __name__ == "__main__":
    main()
