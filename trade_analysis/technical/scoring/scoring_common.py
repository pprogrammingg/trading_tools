"""
Common scoring logic shared between compute_indicators_tv and compute_indicators_with_score
Eliminates code duplication and makes maintenance easier
"""

import pandas as pd
import numpy as np

# Import predictive indicators
try:
    from predictive_indicators import (
        detect_rsi_divergence, detect_macd_divergence,
        detect_volume_surge, detect_consolidation_base,
        detect_volatility_compression, detect_adx_trend
    )
    PREDICTIVE_INDICATORS_AVAILABLE = True
except ImportError:
    PREDICTIVE_INDICATORS_AVAILABLE = False


def get_category_flags(category):
    """Determine category-specific flags for scoring adjustments"""
    is_crypto = category == "cryptocurrencies"
    is_tech_stock = category in ["tech_stocks", "faang_hot_stocks", "semiconductors"]
    use_mean_reversion = is_crypto or is_tech_stock
    return is_crypto, is_tech_stock, use_mean_reversion


def score_rsi(rsi_value, adx_value, category, result):
    """
    Score RSI with category-specific logic.
    Crypto/Tech: Mean-reversion (overbought = good)
    Others: Trend-following (oversold = good)
    """
    is_crypto, is_tech_stock, use_mean_reversion = get_category_flags(category)
    
    # If ADX shows strong trend, RSI signals are less reliable (trend-following > mean-reverting)
    # BUT: For crypto/tech, mean-reversion works better, so don't reduce weight
    rsi_multiplier = 0.5 if (adx_value is not None and adx_value > 25 and not use_mean_reversion) else 1.0
    
    if use_mean_reversion:
        # MEAN REVERSION LOGIC (Crypto/Tech): Overbought = good entry, Oversold = bad
        if rsi_value > 75:  # Very overbought = mean reversion opportunity
            score_add = 1.5 * rsi_multiplier
            result["score"] += score_add
            result["score_breakdown"]["rsi_overbought_mean_reversion"] = round(score_add, 1)
        elif rsi_value > 70:  # Overbought = potential entry
            score_add = 1 * rsi_multiplier
            result["score"] += score_add
            result["score_breakdown"]["rsi_overbought_mean_reversion"] = round(score_add, 1)
        elif rsi_value < 30:  # Oversold = avoid (may continue down)
            score_sub = 1.5 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_oversold_avoid"] = round(-score_sub, 1)
        elif rsi_value < 40:  # Slightly oversold = caution
            score_sub = 0.5 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_slightly_oversold_avoid"] = round(-score_sub, 1)
    else:
        # TREND-FOLLOWING LOGIC (Commodities/ETFs): Standard RSI interpretation
        if rsi_value < 30:
            score_add = 2 * rsi_multiplier
            result["score"] += score_add
            result["score_breakdown"]["rsi_oversold"] = round(score_add, 1)
        elif rsi_value < 40:
            score_add = 1 * rsi_multiplier
            result["score"] += score_add
            result["score_breakdown"]["rsi_slightly_oversold"] = round(score_add, 1)
        elif rsi_value > 80:  # Extreme overbought
            score_sub = 3 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_extreme_overbought"] = round(-score_sub, 1)
        elif rsi_value > 75:  # Very overbought
            score_sub = 2.5 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_very_overbought"] = round(-score_sub, 1)
        elif rsi_value > 70:  # Overbought
            score_sub = 2 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_overbought"] = round(-score_sub, 1)
        elif rsi_value > 65:  # Approaching overbought
            score_sub = 1 * rsi_multiplier
            result["score"] -= score_sub
            result["score_breakdown"]["rsi_approaching_overbought"] = round(-score_sub, 1)


def score_adx(adx_value, adx_series_stored, category, result):
    """Score ADX with category-specific weight reduction for crypto/tech"""
    is_crypto, is_tech_stock, use_mean_reversion = get_category_flags(category)
    
    if adx_value is None:
        return
    
    adx_trend = None
    if PREDICTIVE_INDICATORS_AVAILABLE and adx_series_stored is not None:
        adx_trend = detect_adx_trend(adx_series_stored, periods=5)
    
    # Reduce ADX weight for crypto/tech (mean-reversion works better)
    adx_multiplier = 0.5 if use_mean_reversion else 1.0
    
    if adx_value > 30:  # Very strong trend
        if adx_trend == 'rising':
            score_add = 2.5 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_very_strong_trend_rising"] = round(score_add, 1)
        elif adx_trend == 'falling':
            score_add = 1 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_very_strong_trend_falling"] = round(score_add, 1)
        else:
            score_add = 2 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_very_strong_trend"] = round(score_add, 1)
    elif adx_value > 25:  # Strong trend
        if adx_trend == 'rising':
            score_add = 2 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_strong_trend_rising"] = round(score_add, 1)
        elif adx_trend == 'falling':
            score_add = 0.5 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_strong_trend_falling"] = round(score_add, 1)
        else:
            score_add = 1.5 * adx_multiplier
            result["score"] += score_add
            result["score_breakdown"]["adx_strong_trend"] = round(score_add, 1)
    elif adx_value >= 20 and adx_trend == 'rising':  # ADX rising from low (20-25) = early trend
        score_add = 1.5 * adx_multiplier
        result["score"] += score_add
        result["score_breakdown"]["adx_rising_from_low"] = round(score_add, 1)


def score_overextension(current_price, ema50, category, result):
    """Score overextension penalty with category-specific multipliers"""
    if ema50 is None or current_price <= ema50:
        return
    
    is_crypto, is_tech_stock, _ = get_category_flags(category)
    
    price_extension_pct = ((current_price / ema50) - 1) * 100
    
    # Crypto: Reduce overextension penalty (crypto can stay extended)
    if is_crypto:
        extension_multiplier = 0.5  # 50% reduction
    elif is_tech_stock:
        extension_multiplier = 0.75  # 25% reduction
    else:
        extension_multiplier = 1.0  # Full penalty
    
    if price_extension_pct > 100:  # Price > 100% above EMA50 (doubled)
        penalty = -3 * extension_multiplier
        result["score"] += penalty
        result["score_breakdown"]["price_extreme_overextension"] = round(penalty, 1)
    elif price_extension_pct > 50:  # Price > 50% above EMA50
        penalty = -2 * extension_multiplier
        result["score"] += penalty
        result["score_breakdown"]["price_major_overextension"] = round(penalty, 1)
    elif price_extension_pct > 30:  # Price > 30% above EMA50
        penalty = -1 * extension_multiplier
        result["score"] += penalty
        result["score_breakdown"]["price_moderate_overextension"] = round(penalty, 1)


def score_volume_surge(volume, category, result):
    """Score volume surge with category-specific weight (2x for crypto)"""
    if len(volume) < 20:
        return
    
    is_crypto, _, _ = get_category_flags(category)
    
    try:
        volume_surge = detect_volume_surge(volume, lookback=20, surge_threshold=1.5)
        if volume_surge:
            volume_bonus = 2.0 if is_crypto else 1.0  # Double weight for crypto
            result["score"] += volume_bonus
            result["score_breakdown"]["volume_surge_accumulation"] = volume_bonus
    except:
        pass


def score_base_patterns(close, result):
    """Score consolidation base patterns"""
    if len(close) < 20:
        return
    
    try:
        base_pattern = detect_consolidation_base(close, lookback=20, tightness_threshold=0.05)
        if base_pattern == 'tight_base':
            result["score"] += 1
            result["score_breakdown"]["tight_base_formation"] = 1
        elif base_pattern == 'ascending_base':
            result["score"] += 1.5
            result["score_breakdown"]["ascending_base_formation"] = 1.5
        elif base_pattern == 'flat_base':
            result["score"] += 0.5
            result["score_breakdown"]["flat_base_formation"] = 0.5
    except:
        pass


def score_volatility_compression(high, low, close, atr_value, result):
    """Score volatility compression (Bollinger Band Squeeze)"""
    if atr_value is None or len(close) < 20:
        return
    
    try:
        # Calculate ATR series for compression detection
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_values = tr.rolling(window=14).mean()
        if len(atr_values) >= 20:
            volatility_compression = detect_volatility_compression(atr_values, lookback=20)
            if volatility_compression:
                result["score"] += 1
                result["score_breakdown"]["volatility_compression"] = 1
    except:
        pass


def score_cci(cci_value, result):
    """Score CCI (Commodity Channel Index)"""
    if cci_value is None:
        return
    
    if cci_value < -100:  # Oversold
        result["score"] += 1.5
        result["score_breakdown"]["cci_oversold"] = 1.5
    elif cci_value < -50:  # Slightly oversold
        result["score"] += 0.5
        result["score_breakdown"]["cci_slightly_oversold"] = 0.5
    elif cci_value > 200:  # Extreme overbought
        result["score"] -= 3
        result["score_breakdown"]["cci_extreme_overbought"] = -3
    elif cci_value > 150:  # Very overbought
        result["score"] -= 2.5
        result["score_breakdown"]["cci_very_overbought"] = -2.5
    elif cci_value > 100:  # Overbought
        result["score"] -= 1.5
        result["score_breakdown"]["cci_overbought"] = -1.5


def score_obv(obv_trending_up, result):
    """Score On-Balance Volume trend"""
    if obv_trending_up:
        result["score"] += 1
        result["score_breakdown"]["obv_trending_up"] = 1


def score_acc_dist(acc_dist_trending_up, result):
    """Score Accumulation/Distribution trend"""
    if acc_dist_trending_up:
        result["score"] += 1
        result["score_breakdown"]["acc_dist_trending_up"] = 1


def score_momentum(momentum, result):
    """Score momentum (rate of change)"""
    if momentum is None:
        return
    
    # Cap extreme values
    if abs(momentum) > 50:
        momentum = 50 if momentum > 0 else -50
    
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


def score_moving_averages(current_price, ema50, ema200, sma50, sma200, result):
    """Score price position relative to moving averages"""
    # Price above key EMAs (bullish)
    if ema50 is not None and current_price > ema50:
        result["score"] += 0.5
        result["score_breakdown"]["price_above_ema50"] = 0.5
    if ema200 is not None and current_price > ema200:
        result["score"] += 1
        result["score_breakdown"]["price_above_ema200"] = 1
    
    # Golden Cross / Death Cross detection (SMA50 vs SMA200) - major signal
    if sma50 is not None and sma200 is not None:
        if sma50 > sma200:
            result["score"] += 1.5
            result["score_breakdown"]["golden_cross"] = 1.5
        else:
            result["score"] -= 1.5
            result["score_breakdown"]["death_cross"] = -1.5


def score_gmma(gmma_bullish, gmma_early_expansion, result):
    """Score GMMA (Guppy Multiple Moving Average) conditions"""
    if gmma_bullish:
        result["score"] += 2
        result["score_breakdown"]["gmma_bullish"] = 2
    if gmma_early_expansion:
        result["score"] += 1
        result["score_breakdown"]["gmma_early_expansion"] = 1


def score_4w_low(current_price, four_w_low, result):
    """Score proximity to 4-week low"""
    if four_w_low is not None and current_price <= four_w_low:
        result["score"] += 1
        result["score_breakdown"]["at_4w_low"] = 1


def score_macd(macd_bullish, macd_positive, close, macd_line, result):
    """Score MACD signals and divergences"""
    if macd_bullish:
        result["score"] += 1
        result["score_breakdown"]["macd_bullish"] = 1
    if macd_positive:
        result["score"] += 0.5
        result["score_breakdown"]["macd_positive"] = 0.5
    
    # MACD Divergence Detection
    if PREDICTIVE_INDICATORS_AVAILABLE and len(close) >= 26 and len(macd_line) >= 5:
        try:
            macd_divergence = detect_macd_divergence(close, macd_line)
            if macd_divergence == 'bearish_divergence':
                result["score"] -= 1.5
                result["score_breakdown"]["macd_bearish_divergence"] = -1.5
            elif macd_divergence == 'bullish_divergence':
                result["score"] += 1.5
                result["score_breakdown"]["macd_bullish_divergence"] = 1.5
        except:
            pass


def score_rsi_divergence(close, rsi_values, result):
    """Score RSI divergence"""
    if PREDICTIVE_INDICATORS_AVAILABLE and len(close) >= 5 and len(rsi_values) >= 5:
        try:
            rsi_divergence = detect_rsi_divergence(close, rsi_values)
            if rsi_divergence == 'bearish_divergence':
                result["score"] -= 1.5
                result["score_breakdown"]["rsi_bearish_divergence"] = -1.5
            elif rsi_divergence == 'bullish_divergence':
                result["score"] += 1.5
                result["score_breakdown"]["rsi_bullish_divergence"] = 1.5
        except:
            pass


def score_multiple_overbought(rsi_value, cci_value, result):
    """Penalty if both RSI and CCI are overbought"""
    overbought_count = 0
    if rsi_value is not None and rsi_value > 70:
        overbought_count += 1
    if cci_value is not None and cci_value > 100:
        overbought_count += 1
    if overbought_count >= 2:
        result["score"] -= 1
        result["score_breakdown"]["multiple_overbought_penalty"] = -1


def score_52w_high_proximity(close, result):
    """Penalty if price is near 52-week high"""
    if len(close) >= 252:
        year_high = close[-252:].max()
        current_price = close.iloc[-1]
        distance_from_high_pct = ((year_high - current_price) / year_high) * 100
        if distance_from_high_pct < 2:
            result["score"] -= 1.5
            result["score_breakdown"]["near_52w_high_resistance"] = -1.5
        elif distance_from_high_pct < 5:
            result["score"] -= 1
            result["score_breakdown"]["close_to_52w_high"] = -1


def create_result_dict():
    """Create a standardized result dictionary"""
    return {
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
        "adx": None,
        "adx_strong_trend": None,
        "cci": None,
        "obv": None,
        "obv_trending_up": None,
        "acc_dist": None,
        "acc_dist_trending_up": None,
        "score": 0,
        "score_breakdown": {}
    }
