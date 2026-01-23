"""
Improved Scoring System with Explosive Bottom Detection
Category-aware scoring optimized through backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

try:
    from .category_optimization import get_category_params
except ImportError:
    try:
        from category_optimization import get_category_params
    except ImportError:
        def get_category_params(category):
            return {
                "rsi_oversold_threshold": 40,
                "rsi_overbought_threshold": 70,
                "adx_multiplier": 1.0,
                "volume_multiplier": 1.0,
                "overextension_multiplier": 1.0,
                "explosive_bottom_bonus": 1.0,
                "capitulation_threshold": -20,
            }


def calculate_price_intensity(close: pd.Series, volume: pd.Series, period: int = 14) -> Optional[float]:
    """Price Intensity Indicator - Fixed normalization"""
    if len(close) < period * 4:
        return None
    
    try:
        # Price momentum
        momentum = close.pct_change(period).abs()
        
        # Volume strength
        volume_ma = volume.rolling(window=period).mean()
        volume_strength = volume / (volume_ma + 0.0001)
        
        # Volatility compression
        volatility = close.rolling(window=period).std()
        volatility_ma = volatility.rolling(window=period * 2).mean()
        volatility_compression = volatility_ma / (volatility + 0.0001)
        
        # Price extension
        price_ma = close.rolling(window=period * 2).mean()
        price_extension = abs((close - price_ma) / (price_ma + 0.0001)) + 0.01
        
        # Combine
        pi = (momentum * volume_strength * volatility_compression) / price_extension
        
        # Normalize to 0-100 using percentile-based approach
        if len(pi) >= period * 4:
            pi_series = pi.dropna()
            if len(pi_series) > 0:
                # Use percentile normalization for better distribution
                pi_min = pi_series.quantile(0.05)  # 5th percentile
                pi_max = pi_series.quantile(0.95)  # 95th percentile
                pi_range = pi_max - pi_min + 0.0001
                
                pi_normalized = ((pi - pi_min) / pi_range) * 100
                pi_normalized = pi_normalized.clip(0, 100)  # Clip to 0-100
                
                return float(pi_normalized.iloc[-1]) if not pd.isna(pi_normalized.iloc[-1]) else None
        
        return None
    except Exception:
        return None


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> Tuple[Optional[float], Optional[pd.Series]]:
    """Calculate ADX and return value + series"""
    try:
        if len(close) < window * 2:
            return None, None
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_di = 100 * (plus_dm.rolling(window=window).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=window).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        adx = dx.rolling(window=window).mean()
        
        adx_value = adx.iloc[-1] if len(adx) > 0 and not pd.isna(adx.iloc[-1]) else None
        return round(adx_value, 2) if adx_value else None, adx
    except Exception:
        return None, None


def improved_scoring(df: pd.DataFrame, category: str, pi_value: Optional[float] = None, timeframe: str = "1W", market_context: Optional[Dict] = None) -> Dict:
    """
    Improved scoring system with explosive bottom detection
    Category-aware, timeframe-specific, and market-context aware
    
    Args:
        df: Price data DataFrame
        category: Asset category
        pi_value: Pre-calculated PI value (optional)
        timeframe: Timeframe string (2D, 1W, 2W, 1M) - affects scoring strictness
        market_context: Market context dict (SPX/Gold ratio, etc.)
    """
    if len(df) < 50:
        return {'score': 0, 'indicators': {}, 'breakdown': {}}
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    score = 0.0
    indicators = {}
    breakdown = {}
    
    current_price = close.iloc[-1]
    
    # Category flags and parameters
    is_crypto = category == "cryptocurrencies"
    is_tech = category in ["tech_stocks", "faang_hot_stocks", "semiconductors"]
    is_mining = category in ["miner_hpc", "silver_miners_esg"]
    use_mean_reversion = is_crypto or is_tech
    
    # Get category-specific parameters
    params = get_category_params(category)
    
    # Get timeframe-specific multipliers (shorter timeframes = stricter scoring)
    timeframe_multipliers = {
        "2D": 0.7,   # Stricter for 2D (reduce scores by 30%)
        "1W": 0.85,  # Slightly stricter for 1W (reduce by 15%)
        "2W": 1.0,   # Standard for 2W
        "1M": 1.1,   # Slightly more lenient for 1M (increase by 10%)
    }
    timeframe_mult = timeframe_multipliers.get(timeframe, 1.0)
    
    # Market context adjustment (SPX/Gold ratio)
    market_adjustment = 0.0
    vix_adjustment = 0.0
    if market_context:
        market_adjustment = market_context.get('market_adjustment', 0.0)
        vix_adjustment = market_context.get('vix_adjustment', 0.0)
        
        if market_context.get('market_bearish', False):
            # In bear markets, be even more strict
            timeframe_mult *= 0.9  # Additional 10% reduction
        
        # VIX-based adjustments
        vix_level = market_context.get('vix_level', 'unknown')
        vix_trend = market_context.get('vix_trend', 'unknown')
        
        # High VIX (>29) = meaningful risk increase
        if vix_level == 'high':
            timeframe_mult *= 0.85  # Additional 15% reduction for high VIX
        
        # Rising VIX = increasing risk
        if vix_trend == 'rising' and vix_level in ['moderate', 'high']:
            timeframe_mult *= 0.95  # Additional 5% reduction for rising VIX
    
    # Calculate PI if not provided
    if pi_value is None:
        pi_value = calculate_price_intensity(close, volume)
    
    indicators['pi'] = pi_value
    
    # RSI calculation
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 0.0001)
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    indicators['rsi'] = round(rsi_value, 2)
    
    # Moving averages
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    sma50 = close.rolling(window=50).mean()
    sma200 = close.rolling(window=200).mean()
    
    indicators['ema50'] = round(ema50.iloc[-1], 2) if len(ema50) > 0 else None
    indicators['ema200'] = round(ema200.iloc[-1], 2) if len(ema200) > 0 else None
    
    # ADX calculation
    adx_value, adx_series = calculate_adx(high, low, close)
    indicators['adx'] = adx_value
    
    # ADX rising detection
    adx_rising = False
    if adx_value and adx_series is not None and len(adx_series) >= 5:
        try:
            adx_current = adx_series.iloc[-1]
            adx_5_ago = adx_series.iloc[-5]
            adx_rising = (adx_current > adx_5_ago * 1.05) and (adx_current >= 20)
        except:
            pass
    
    # Momentum
    momentum = None
    if len(close) >= 14:
        momentum = ((close.iloc[-1] / close.iloc[-14]) - 1) * 100
        if abs(momentum) > 50:
            momentum = 50 if momentum > 0 else -50
        indicators['momentum'] = round(momentum, 2)
    
    # Volatility compression
    volatility = close.rolling(window=20).std()
    volatility_ma = volatility.rolling(window=40).mean()
    volatility_compressed = False
    if len(volatility) > 0 and len(volatility_ma) > 0:
        volatility_compressed = volatility.iloc[-1] < volatility_ma.iloc[-1] * 0.7
    
    # Volume building
    volume_ma_short = volume.rolling(window=10).mean()
    volume_ma_long = volume.rolling(window=30).mean()
    volume_building = False
    if len(volume_ma_short) > 0 and len(volume_ma_long) > 0:
        volume_building = volume_ma_short.iloc[-1] > volume_ma_long.iloc[-1] * 1.1
    
    # Price near support
    recent_low = close.rolling(window=20).min()
    near_support = False
    if len(recent_low) > 0:
        near_support = current_price <= recent_low.iloc[-1] * 1.05
    
    # ===== EXPLOSIVE BOTTOM DETECTION =====
    # This is the key improvement - detect bottoms before explosive moves
    explosive_bottom = False
    
    # Condition 1: Oversold RSI (category-specific threshold)
    oversold_threshold = params.get("rsi_oversold_threshold", 40)
    oversold = rsi_value < oversold_threshold
    
    # Condition 2: Strong ADX (category-specific threshold) - trend starting
    adx_threshold = params.get("adx_threshold", 25)  # Default 25, but 20 for crypto
    strong_adx = adx_value and adx_value > adx_threshold
    
    # Condition 3: Very negative momentum (category-specific threshold) - capitulation
    capitulation_threshold = params.get("capitulation_threshold", -20)
    capitulation = momentum and momentum < capitulation_threshold
    
    # Condition 4: Price near support (4-week low)
    near_support = False
    if indicators.get('4w_low'):
        support_distance = ((current_price / indicators['4w_low']) - 1) * 100
        near_support = support_distance < 5  # Within 5% of 4-week low
    
    # Condition 5: Volatility compressed OR volume building
    volatility_compressed = False
    volume_building = False
    
    if len(close) >= 20:
        # Volatility compression (Bollinger Band squeeze)
        volatility = close.rolling(window=20).std()
        volatility_ma = volatility.rolling(window=40).mean()
        if len(volatility) > 0 and len(volatility_ma) > 0 and not pd.isna(volatility.iloc[-1]) and not pd.isna(volatility_ma.iloc[-1]):
            volatility_compressed = volatility.iloc[-1] < volatility_ma.iloc[-1] * 0.8
        
        # Volume building
        volume_ma = volume.rolling(window=20).mean()
        if len(volume) > 0 and len(volume_ma) > 0 and not pd.isna(volume.iloc[-1]) and not pd.isna(volume_ma.iloc[-1]):
            volume_building = volume.iloc[-1] > volume_ma.iloc[-1] * 1.2
    
    if oversold and strong_adx:
        # Base explosive bottom setup
        explosive_bottom = True
        base_bonus = 4.0 * params.get("explosive_bottom_bonus", 1.0)
        score += base_bonus
        breakdown['explosive_bottom_base'] = round(base_bonus, 1)
        
        # Additional bonuses
        if capitulation:
            capitulation_bonus = 2.0 * params.get("explosive_bottom_bonus", 1.0)
            score += capitulation_bonus
            breakdown['explosive_bottom_capitulation'] = round(capitulation_bonus, 1)
        
        if near_support:
            score += 1.5
            breakdown['explosive_bottom_support'] = 1.5
        
        if volatility_compressed:
            score += 1.0
            breakdown['explosive_bottom_volatility'] = 1.0
        
        if volume_building:
            volume_bonus = 1.0 * params.get("volume_multiplier", 1.0)
            score += volume_bonus
            breakdown['explosive_bottom_volume'] = round(volume_bonus, 1)
        
        if adx_rising:
            adx_bonus = 1.5 * params.get("adx_multiplier", 1.0)
            score += adx_bonus
            breakdown['explosive_bottom_adx_rising'] = round(adx_bonus, 1)
    
    # ===== EXTREME OVERSOLD EMA BONUS (for crypto) =====
    # When price is >20% below EMA50, it's extreme oversold (like Nov 2022 BTC)
    if indicators['ema50'] and current_price < indicators['ema50']:
        price_below_ema_pct = ((current_price / indicators['ema50']) - 1) * 100
        
        if params.get("extreme_oversold_ema_bonus", False):
            if price_below_ema_pct < -30:  # Price >30% below EMA50
                score += 3.0
                breakdown['extreme_oversold_ema_30pct'] = 3.0
            elif price_below_ema_pct < -20:  # Price >20% below EMA50
                score += 2.0
                breakdown['extreme_oversold_ema_20pct'] = 2.0
    
    # ===== TREND CONTINUATION SIGNALS (for established trends) =====
    # When price is above EMAs and ADX is strong, it's a continuation setup
    # This catches moves like BTC from $26K to $104K (4x move)
    # Works for ALL categories with category-specific bonuses
    if not explosive_bottom and indicators['ema50'] and indicators['ema200']:
        price_above_ema50 = current_price > indicators['ema50']
        price_above_ema200 = current_price > indicators['ema200']
        
        # Category-specific ADX threshold for continuation (lower for crypto/volatile assets)
        continuation_adx_threshold = params.get("continuation_adx_threshold", 20)  # Lower default (was 25)
        moderate_adx_threshold = params.get("moderate_adx_threshold", 15)  # New: moderate ADX threshold
        
        # Strong continuation: Price above EMAs + ADX > threshold
        if price_above_ema50 and price_above_ema200 and adx_value and adx_value > continuation_adx_threshold:
            # Strong trend continuation (category-specific bonus)
            continuation_bonus_base = params.get("trend_continuation_bonus", 2.0)
            continuation_bonus = continuation_bonus_base
            score += continuation_bonus
            breakdown['trend_continuation_strong'] = round(continuation_bonus, 1)
            
            # Additional bonus if ADX is very strong (category-specific threshold)
            very_strong_adx_threshold = params.get("very_strong_adx_threshold", 40)
            if adx_value > very_strong_adx_threshold:
                very_strong_bonus = 1.5 * params.get("adx_multiplier", 1.0)
                score += very_strong_bonus
                breakdown['trend_continuation_very_strong'] = round(very_strong_bonus, 1)
            
            # Bonus if momentum is positive (trend accelerating)
            if momentum and momentum > 5:
                momentum_bonus = 1.0
                score += momentum_bonus
                breakdown['trend_continuation_momentum'] = momentum_bonus
            
            # Bonus if RSI is in healthy range (40-60) during strong trend
            # For mean-reversion categories, RSI 50-70 is also healthy
            if use_mean_reversion:
                if 50 <= rsi_value <= 70:
                    healthy_rsi_bonus = 1.0
                    score += healthy_rsi_bonus
                    breakdown['trend_continuation_healthy_rsi'] = healthy_rsi_bonus
            else:
                if 40 <= rsi_value <= 60:
                    healthy_rsi_bonus = 1.0
                    score += healthy_rsi_bonus
                    breakdown['trend_continuation_healthy_rsi'] = healthy_rsi_bonus
            
            # Bonus if Golden Cross is present
            if len(sma50) > 0 and len(sma200) > 0:
                if sma50.iloc[-1] > sma200.iloc[-1]:
                    golden_cross_bonus = 0.5
                    score += golden_cross_bonus
                    breakdown['trend_continuation_golden_cross'] = golden_cross_bonus
        
        # Moderate continuation: Price above EMAs + moderate ADX (15-25)
        # This catches moves when trend is established but ADX hasn't spiked yet
        elif price_above_ema50 and price_above_ema200 and adx_value and moderate_adx_threshold <= adx_value <= continuation_adx_threshold:
            moderate_continuation_bonus = params.get("trend_continuation_bonus", 2.0) * 0.5  # Half bonus
            score += moderate_continuation_bonus
            breakdown['trend_continuation_moderate'] = round(moderate_continuation_bonus, 1)
            
            # Additional bonus if momentum is positive
            if momentum and momentum > 0:
                momentum_bonus = 0.5
                score += momentum_bonus
                breakdown['trend_continuation_moderate_momentum'] = momentum_bonus
    
    # ===== STANDARD SCORING (if not explosive bottom) =====
    if not explosive_bottom:
        # RSI scoring (category-specific thresholds)
        overbought_threshold = params.get("rsi_overbought_threshold", 70)
        
        if use_mean_reversion:
            if rsi_value > overbought_threshold:
                score += 1.0
                breakdown['rsi_overbought_mean_reversion'] = 1.0
            elif oversold_threshold - 10 <= rsi_value <= oversold_threshold:
                if strong_adx:  # Oversold + strong trend = opportunity
                    score += 1.5
                    breakdown['oversold_strong_trend'] = 1.5
                else:
                    score -= 0.5
                    breakdown['oversold_weak_trend'] = -0.5
            elif rsi_value < oversold_threshold - 10:
                if strong_adx:
                    score += 1.0  # Very oversold + strong trend
                    breakdown['very_oversold_strong_trend'] = 1.0
                else:
                    score -= 1.5
                    breakdown['rsi_oversold_avoid'] = -1.5
        else:
            if rsi_value < oversold_threshold:
                score += 2.0
                breakdown['rsi_oversold'] = 2.0
            elif rsi_value > overbought_threshold:
                score -= 2.0
                breakdown['rsi_overbought'] = -2.0
        
        # Price above EMAs
        if indicators['ema50'] and current_price > indicators['ema50']:
            score += 0.5
            breakdown['price_above_ema50'] = 0.5
        if indicators['ema200'] and current_price > indicators['ema200']:
            score += 1.0
            breakdown['price_above_ema200'] = 1.0
        
        # Golden Cross
        if len(sma50) > 0 and len(sma200) > 0:
            if sma50.iloc[-1] > sma200.iloc[-1]:
                score += 1.5
                breakdown['golden_cross'] = 1.5
    
    # ===== ADX SCORING =====
    if adx_value:
        adx_multiplier = params.get("adx_multiplier", 0.5 if use_mean_reversion else 1.0)
        
        if adx_rising:
            if 20 <= adx_value <= 25:
                score += 3.0 * adx_multiplier  # ADX rising from low = very bullish
                breakdown['adx_rising_from_low'] = round(3.0 * adx_multiplier, 1)
            elif 25 < adx_value <= 30:
                score += 2.5 * adx_multiplier
                breakdown['adx_rising_strong'] = round(2.5 * adx_multiplier, 1)
            elif adx_value > 30:
                score += 2.5 * adx_multiplier
                breakdown['adx_rising_very_strong'] = round(2.5 * adx_multiplier, 1)
        elif adx_value > 30:
            score += 2.0 * adx_multiplier
            breakdown['adx_very_strong'] = round(2.0 * adx_multiplier, 1)
        elif adx_value > 25:
            score += 1.5 * adx_multiplier
            breakdown['adx_strong'] = round(1.5 * adx_multiplier, 1)
    
    # ===== MOMENTUM SCORING =====
    if momentum:
        if momentum > 15:
            score += 1.0
            breakdown['very_strong_momentum'] = 1.0
        elif momentum > 8:
            score += 0.5
            breakdown['strong_momentum'] = 0.5
        # Don't penalize negative momentum if in explosive bottom setup
    
    # ===== VOLUME SCORING =====
    if volume_building:
        volume_mult = params.get("volume_multiplier", 2.0 if is_crypto else 1.5)
        volume_bonus = 1.5 * volume_mult
        score += volume_bonus
        breakdown['volume_building'] = round(volume_bonus, 1)
    
    if len(volume) >= 20:
        avg_volume = volume.rolling(window=20).mean()
        if volume.iloc[-1] > avg_volume.iloc[-1] * 1.5 and volatility_compressed:
            score += 1.5
            breakdown['volume_surge_consolidation'] = 1.5
    
    # ===== PI INDICATOR =====
    if pi_value is not None:
        if pi_value > 70:
            score += 2.0
            breakdown['pi_high'] = 2.0
        elif pi_value > 50:
            score += 1.0
            breakdown['pi_moderate'] = 1.0
    
    # ===== OVEREXTENSION PENALTY (only if not explosive bottom) =====
    if not explosive_bottom and indicators['ema50'] and current_price > indicators['ema50']:
        extension_pct = ((current_price / indicators['ema50']) - 1) * 100
        if extension_pct > 30:
            ext_mult = params.get("overextension_multiplier", 0.5 if is_crypto else 0.75 if is_tech else 1.0)
            penalty = -1 * ext_mult
            score += penalty
            breakdown['overextension'] = round(penalty, 1)
    
    # ===== SUPPORT LEVEL =====
    if near_support and not explosive_bottom:
        score += 1.0
        breakdown['near_support'] = 1.0
    
    # ===== BOTTOMING STRUCTURE DETECTION =====
    try:
        from ..indicators.bottoming_structures import detect_complex_bottoming_structure
        bottoming_structure = detect_complex_bottoming_structure(close, high, low, volume, lookback=60)
        
        if bottoming_structure['pattern_score'] > 0:
            pattern_bonus = bottoming_structure['pattern_score'] * timeframe_mult
            score += pattern_bonus
            breakdown['bottoming_pattern'] = round(pattern_bonus, 1)
            
            if bottoming_structure['confidence'] > 0.5:
                confidence_bonus = 1.0 * timeframe_mult
                score += confidence_bonus
                breakdown['high_confidence_pattern'] = round(confidence_bonus, 1)
            
            indicators['bottoming_pattern'] = {
                'double_bottom': bottoming_structure['double_bottom'],
                'inverse_hs': bottoming_structure['inverse_hs'],
                'ascending_triangle': bottoming_structure['ascending_triangle'],
                'falling_wedge': bottoming_structure['falling_wedge'],
                'support_level': bottoming_structure['support_level'],
                'target_level': bottoming_structure['target_level'],
                'confidence': round(bottoming_structure['confidence'], 2),
            }
    except ImportError:
        pass
    
    # ===== ELLIOTT WAVE ANALYSIS =====
    try:
        from ..indicators.elliott_wave import calculate_elliott_wave_targets
        wave_analysis = calculate_elliott_wave_targets(close, high, low)
        
        if wave_analysis:
            indicators['elliott_wave'] = {
                'trend': wave_analysis['trend'],
                'wave_position': wave_analysis['wave_position'],
                'price_targets': wave_analysis['price_targets'],
                'support_resistance': wave_analysis['support_resistance'],
            }
            
            # Add bonus if in wave 2 or 4 (correction = buying opportunity)
            if "Wave 2 or 4" in wave_analysis['wave_position']:
                wave_bonus = 1.5 * timeframe_mult
                score += wave_bonus
                breakdown['elliott_wave_correction'] = round(wave_bonus, 1)
    except ImportError:
        pass
    
    # ===== APPLY TIMEFRAME MULTIPLIER =====
    # Shorter timeframes get stricter scoring
    score = score * timeframe_mult
    
    # ===== APPLY MARKET CONTEXT ADJUSTMENT =====
    # In bear markets (SPX/Gold crashing), reduce scores
    score += market_adjustment
    if market_adjustment < 0:
        breakdown['market_bearish_adjustment'] = round(market_adjustment, 1)
    
    # Apply VIX adjustment (volatility-based risk adjustment)
    score += vix_adjustment
    if vix_adjustment < 0:
        breakdown['vix_adjustment'] = round(vix_adjustment, 1)
    
    # Add VIX info to indicators
    if market_context and market_context.get('vix') is not None:
        indicators['vix'] = round(market_context.get('vix'), 2)
        indicators['vix_level'] = market_context.get('vix_level', 'unknown')
        indicators['vix_trend'] = market_context.get('vix_trend', 'unknown')
    
    # ===== FINAL SCORE CAP =====
    # Cap very high scores (likely over-optimistic)
    if score > 20:
        score = 20
        breakdown['score_capped'] = True
    
    return {
        'score': round(score, 1),
        'indicators': indicators,
        'breakdown': breakdown
    }
