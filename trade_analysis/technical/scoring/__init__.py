"""
Scoring module - Improved scoring system with explosive bottom detection
"""

from .improved_scoring import improved_scoring, calculate_price_intensity, calculate_adx
from .category_optimization import get_category_params, CATEGORY_PARAMS
from .scoring_common import (
    get_category_flags, score_rsi, score_adx, score_overextension,
    score_volume_surge, score_base_patterns, score_volatility_compression,
    score_cci, score_obv, score_acc_dist, score_momentum,
    score_moving_averages, score_gmma, score_4w_low, score_macd,
    score_rsi_divergence, score_multiple_overbought, score_52w_high_proximity,
    create_result_dict
)

__all__ = [
    'improved_scoring',
    'calculate_price_intensity',
    'calculate_adx',
    'get_category_params',
    'CATEGORY_PARAMS',
    'get_category_flags',
    'score_rsi',
    'score_adx',
    'score_overextension',
    'score_volume_surge',
    'score_base_patterns',
    'score_volatility_compression',
    'score_cci',
    'score_obv',
    'score_acc_dist',
    'score_momentum',
    'score_moving_averages',
    'score_gmma',
    'score_4w_low',
    'score_macd',
    'score_rsi_divergence',
    'score_multiple_overbought',
    'score_52w_high_proximity',
    'create_result_dict',
]
