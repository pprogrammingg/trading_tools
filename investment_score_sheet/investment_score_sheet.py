import json
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange
import numpy as np
from tradingview_indicators import RSI, ema, sma

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

OUTPUT_FILE = "../all_results.json"  # Save in parent directory

# ======================================================
# DATA HELPERS
# ======================================================

def download_data(symbol, period="5y", interval="1d"):
    """Download data from yFinance"""
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
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

def compute_indicators_tv(df):
    """Compute indicators using tradingview-indicators library (TradingView-style calculations)"""
    result = {
        "rsi": None,
        "stoch_rsi_fast": None,
        "stoch_rsi_slow": None,
        "atr": None,
        "atr_pct": None,
        "close": None,
        "ema50": None,
        "4w_low": None,
        "gmma_bullish": None,
        "gmma_compressed": None,
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
    
    # === EMA50 ===
    if len(close) >= 50:
        ema50_values = ema(close, 50)
        result["ema50"] = round(ema50_values.iloc[-1], 4)
    
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
        result["gmma_compressed"] = bool(short_spread / close.iloc[-1] < 0.015)
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
            result["score"] -= 1
            result["score_breakdown"]["rsi_overbought"] = -1
    
    # === StochRSI ===
    if len(close) >= INDICATOR_WINDOWS["stoch_rsi"] + 3 + 3:  # Need RSI period + K + D
        rsi_values = RSI(close, INDICATOR_WINDOWS["stoch_rsi"])
        stoch_k, stoch_d = compute_stochrsi_tv(rsi_values, k_period=3, d_period=3, stoch_period=INDICATOR_WINDOWS["stoch_rsi"])
        if stoch_k is not None and stoch_d is not None:
            fast_value = stoch_k.iloc[-1] * 100
            result["stoch_rsi_fast"] = round(fast_value, 2)
            result["stoch_rsi_slow"] = round(stoch_d.iloc[-1] * 100, 2)
            if fast_value < 20:
                result["score"] += 1
                result["score_breakdown"]["stochrsi_oversold"] = 1
            elif fast_value > 80:
                result["score"] -= 1
                result["score_breakdown"]["stochrsi_overbought"] = -1
    
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
        if atr_pct > 20:
            result["score"] -= 2
            result["score_breakdown"]["atr_very_high"] = -2
        elif atr_pct > 15:
            result["score"] -= 1
            result["score_breakdown"]["atr_high"] = -1
    
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
    if len(close) >= 10:
        momentum = ((close.iloc[-1] / close.iloc[-10]) - 1) * 100
        result["momentum"] = round(momentum, 2)
        if momentum > 5:
            result["score"] += 1
            result["score_breakdown"]["strong_momentum"] = 1
        elif momentum > 2:
            result["score"] += 1  # Give full point for moderate momentum
            result["score_breakdown"]["moderate_momentum"] = 1
        elif momentum < -5:
            result["score"] -= 1
            result["score_breakdown"]["negative_momentum"] = -1

    # === Score additions from price vs EMA50 / GMMA conditions ===
    if result["ema50"] is not None and close.iloc[-1] > result["ema50"]:
        result["score"] += 1
        result["score_breakdown"]["price_above_ema50"] = 1
    if result["gmma_bullish"]:
        result["score"] += 2
        result["score_breakdown"]["gmma_bullish"] = 2
    if result["gmma_early_expansion"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_early_expansion"] = 1
    if result["gmma_compressed"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_compressed"] = 1
    if result["4w_low"] is not None and close.iloc[-1] <= result["4w_low"]:
        result["score"] += 1
        result["score_breakdown"]["at_4w_low"] = 1
    
    return result

# ======================================================
# YFINANCE INDICATORS (using ta library)
# NOTE: Using yFinance data with ta library calculations
# ======================================================

def compute_indicators_with_score(df):
    result = {
        "rsi": None,
        "stoch_rsi_fast": None,
        "stoch_rsi_slow": None,
        "atr": None,
        "atr_pct": None,  # ATR as percentage of price
        "close": None,
        "ema50": None,
        "4w_low": None,
        "gmma_bullish": None,
        "gmma_compressed": None,
        "gmma_early_expansion": None,
        "macd_bullish": None,  # MACD line above signal
        "macd_positive": None,  # MACD histogram positive
        "volume_above_avg": None,  # Volume above 20-day average
        "momentum": None,  # 10-day rate of change
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

    # === EMA50 ===
    if len(close) >= 50:
        ema50 = close.ewm(span=50, adjust=False).mean()
        result["ema50"] = round(ema50.iloc[-1], 4)

    # === GMMA ===
    short_emas, long_emas = compute_gmma(close)
    try:
        short_last = short_emas.iloc[-1]
        long_last = long_emas.iloc[-1]
        result["gmma_bullish"] = short_last.min() > long_last.max()

        short_spread = short_last.max() - short_last.min()
        result["gmma_compressed"] = short_spread / close.iloc[-1] < 0.015
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
            result["score"] -= 1  # Penalize overbought
            result["score_breakdown"]["rsi_overbought"] = -1

    # === StochRSI ===
    if len(close) >= INDICATOR_WINDOWS["stoch_rsi"]:
        stoch = StochRSIIndicator(close, INDICATOR_WINDOWS["stoch_rsi"])
        fast = stoch.stochrsi_k().iloc[-1] * 100  # %K (StochRSI smoothed by K=3)
        slow = stoch.stochrsi_d().iloc[-1] * 100  # %D (%K smoothed by D=3)
        result["stoch_rsi_fast"] = round(fast, 2)
        result["stoch_rsi_slow"] = round(slow, 2)
        if fast < 20:
            result["score"] += 1
            result["score_breakdown"]["stochrsi_oversold"] = 1
        elif fast > 80:
            result["score"] -= 1  # Penalize overbought
            result["score_breakdown"]["stochrsi_overbought"] = -1

    # === ATR ===
    if len(close) >= INDICATOR_WINDOWS["atr"]:
        atr = AverageTrueRange(high, low, close, INDICATOR_WINDOWS["atr"]).average_true_range()
        atr_value = atr.iloc[-1]
        result["atr"] = round(atr_value, 4)
        atr_pct = (atr_value / close.iloc[-1]) * 100
        result["atr_pct"] = round(atr_pct, 2)
        # More nuanced ATR scoring: penalize only extremely high volatility
        # Adjusted thresholds to account for crypto's naturally higher volatility
        # Crypto typically has 15-30% ATR, stocks typically 5-15%
        if atr_pct > 40:
            result["score"] -= 2  # Extremely high volatility - significant risk
            result["score_breakdown"]["atr_very_high"] = -2
        elif atr_pct > 30:
            result["score"] -= 1  # Very high volatility - moderate risk
            result["score_breakdown"]["atr_high"] = -1

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
    if len(close) >= 10:
        momentum = ((close.iloc[-1] / close.iloc[-10]) - 1) * 100
        result["momentum"] = round(momentum, 2)
        if momentum > 5:  # Strong positive momentum (>5% in 10 periods)
            result["score"] += 1
            result["score_breakdown"]["strong_momentum"] = 1
        elif momentum > 2:  # Moderate positive momentum
            result["score"] += 0.5
            result["score_breakdown"]["moderate_momentum"] = 0.5
        elif momentum < -5:  # Strong negative momentum
            result["score"] -= 1
            result["score_breakdown"]["negative_momentum"] = -1

    # === Score additions from price vs EMA50 / GMMA conditions ===
    if result["ema50"] is not None and close.iloc[-1] > result["ema50"]:
        result["score"] += 1
        result["score_breakdown"]["price_above_ema50"] = 1
    if result["gmma_bullish"]:
        result["score"] += 2
        result["score_breakdown"]["gmma_bullish"] = 2
    if result["gmma_early_expansion"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_early_expansion"] = 1
    if result["gmma_compressed"]:
        result["score"] += 1
        result["score_breakdown"]["gmma_compressed"] = 1
    if result["4w_low"] is not None and close.iloc[-1] <= result["4w_low"]:
        result["score"] += 1
        result["score_breakdown"]["at_4w_low"] = 1

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

def main():
    results = {}
    
    print("Using data source: yFinance\n")
    
    # Download gold prices for gold-denominated calculations
    print("Downloading gold prices (GC=F) for gold-denominated analysis...")
    gold_df = download_data("GC=F")
    if len(gold_df) == 0:
        print("  Warning: Could not fetch gold prices. Gold-denominated analysis will be skipped.")
        gold_df = None
    else:
        print(f"  ✓ Gold prices downloaded ({len(gold_df)} rows)")

    # Determine category for each symbol (for relative comparisons)
    symbol_to_category = {}
    for symbol in SYMBOLS:
        if symbol in TECH_STOCKS:
            symbol_to_category[symbol] = TECH_STOCKS
        elif symbol in CRYPTOCURRENCIES:
            symbol_to_category[symbol] = CRYPTOCURRENCIES
        elif symbol in PRECIOUS_METALS:
            symbol_to_category[symbol] = PRECIOUS_METALS

    for symbol in SYMBOLS:
        print(f"Processing {symbol}...")
        results[symbol] = {}
        
        # Fetch data from yFinance
        print(f"  Fetching data...", end=" ")
        base_df = download_data(symbol)
        if len(base_df) == 0:
            print("✗ (no data)")
            print(f"  Warning: No data available for {symbol}")
            continue
        print(f"✓ ({len(base_df)} rows)")
        
        # Calculate relative potential using full dataset (not resampled)
        category_symbols = symbol_to_category.get(symbol, [symbol])
        relative_potential = calculate_relative_potential(symbol, base_df, category_symbols)

        for label, rule in TIMEFRAMES.items():
            results[symbol][label] = {}
            
            df_usd = resample_ohlcv(base_df, rule)
            
            if len(df_usd) == 0:
                results[symbol][label]["yfinance"] = {"error": "No data after resampling"}
                continue
            
            # Calculate indicators for USD-denominated prices
            indicators_ta_usd = compute_indicators_with_score(df_usd)
            indicators_tv_usd = compute_indicators_tv(df_usd)
            
            # Add relative potential to indicators (same for all timeframes, calculated from full data)
            indicators_ta_usd["relative_potential"] = relative_potential
            indicators_tv_usd["relative_potential"] = relative_potential
            
            # Calculate indicators for Gold-denominated prices (if gold data available)
            indicators_ta_gold = None
            indicators_tv_gold = None
            
            if gold_df is not None and symbol != "GC=F":  # Skip gold for itself
                gold_resampled = resample_ohlcv(gold_df, rule)
                df_gold = convert_to_gold_terms(df_usd, gold_resampled)
                
                if len(df_gold) > 0:
                    indicators_ta_gold = compute_indicators_with_score(df_gold)
                    indicators_tv_gold = compute_indicators_tv(df_gold)
                    # Calculate relative potential for gold terms too
                    gold_potential = calculate_relative_potential(symbol, df_gold, category_symbols)
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

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2, default=json_safe)

    print(f"\nSaved results to {OUTPUT_FILE}")
    print(f"\nNote: Results use yFinance data with two calculation methods:")
    print(f"      - ta_library: Standard technical analysis library")
    print(f"      - tradingview_library: TradingView-style calculations")

if __name__ == "__main__":
    main()
