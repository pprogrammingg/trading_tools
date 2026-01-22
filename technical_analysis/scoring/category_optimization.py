"""
Category-Specific Scoring Optimizations
Different categories require different parameter tuning
"""

# Category-specific parameter adjustments based on backtesting
CATEGORY_PARAMS = {
    "cryptocurrencies": {
        "rsi_oversold_threshold": 35,  # More sensitive (mean-reversion)
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 0.5,  # Reduce ADX weight
        "volume_multiplier": 2.0,  # Double volume importance
        "overextension_multiplier": 0.5,  # Reduce overextension penalty
        "explosive_bottom_bonus": 1.5,  # Extra bonus for crypto bottoms
        "adx_threshold": 20,  # Lower ADX threshold for crypto (was 25)
        "capitulation_threshold": -20,  # Lower capitulation threshold for crypto (was -30)
        "extreme_oversold_ema_bonus": True,  # Bonus for price >20% below EMA50
        "trend_continuation_bonus": 2.0,  # Bonus for established trends
        "continuation_adx_threshold": 20,  # ADX threshold for continuation signals (lowered for crypto)
        "moderate_adx_threshold": 15,  # ADX threshold for moderate continuation
        "very_strong_adx_threshold": 40,  # ADX threshold for very strong continuation
    },
    "tech_stocks": {
        "rsi_oversold_threshold": 35,
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 0.5,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.75,
        "explosive_bottom_bonus": 1.0,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 40,
    },
    "faang_hot_stocks": {
        "rsi_oversold_threshold": 35,
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 0.5,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.75,
        "explosive_bottom_bonus": 1.0,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 40,
    },
    "miner_hpc": {
        "rsi_oversold_threshold": 40,  # More sensitive to oversold
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 1.0,  # Full ADX weight
        "volume_multiplier": 1.5,
        "overextension_multiplier": 1.0,
        "explosive_bottom_bonus": 2.0,  # Big bonus for mining bottoms
        "capitulation_threshold": -30,  # Lower threshold for capitulation
        "trend_continuation_bonus": 2.5,  # Higher bonus for mining trends
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,  # Lower threshold for mining (more volatile)
    },
    "silver_miners_esg": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 1.0,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 1.0,
        "explosive_bottom_bonus": 2.0,
        "trend_continuation_bonus": 2.5,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
    "precious_metals": {
        "rsi_oversold_threshold": 30,  # Standard thresholds
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 1.0,
        "volume_multiplier": 1.0,
        "overextension_multiplier": 1.0,
        "explosive_bottom_bonus": 1.0,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 40,
    },
    "index_etfs": {
        "rsi_oversold_threshold": 30,
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 1.0,
        "volume_multiplier": 1.0,
        "overextension_multiplier": 1.0,
        "explosive_bottom_bonus": 1.0,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 40,
    },
    "quantum": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 0.75,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.9,
        "explosive_bottom_bonus": 1.5,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
    "battery_storage": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 0.75,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.9,
        "explosive_bottom_bonus": 1.5,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
    "clean_energy_materials": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 0.75,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.9,
        "explosive_bottom_bonus": 1.5,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
    "renewable_energy": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 0.75,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.9,
        "explosive_bottom_bonus": 1.5,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
    "next_gen_automotive": {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 75,
        "adx_multiplier": 0.75,
        "volume_multiplier": 1.5,
        "overextension_multiplier": 0.9,
        "explosive_bottom_bonus": 1.5,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 35,
    },
}


def get_category_params(category: str) -> dict:
    """Get category-specific parameters"""
    return CATEGORY_PARAMS.get(category, {
        "rsi_oversold_threshold": 40,
        "rsi_overbought_threshold": 70,
        "adx_multiplier": 1.0,
        "volume_multiplier": 1.0,
        "overextension_multiplier": 1.0,
        "explosive_bottom_bonus": 1.0,
        "capitulation_threshold": -20,
        "trend_continuation_bonus": 2.0,
        "continuation_adx_threshold": 25,
        "very_strong_adx_threshold": 40,
    })
