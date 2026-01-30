"""
Indicators module - Common indicator calculations
"""

from .indicators_common import (
    compute_gmma, compute_gmma_tv,
    calculate_moving_averages_tv, calculate_moving_averages_ta,
    calculate_adx, calculate_cci, calculate_obv, calculate_acc_dist,
    calculate_macd, calculate_atr, calculate_momentum, calculate_4w_low
)

from .advanced_indicators import (
    calculate_price_intensity, detect_explosive_move_setup,
    get_hash_ribbon_signal_for_stock, calculate_hash_ribbon
)

from .market_context import get_market_context
try:
    from .cme_sunday_open import get_cme_direction_for_symbol, get_cme_direction_all
except ImportError:
    get_cme_direction_for_symbol = None
    get_cme_direction_all = None
try:
    from .super_guppy import get_super_guppy_state
except ImportError:
    get_super_guppy_state = None
from .bottoming_structures import (
    detect_double_bottom, detect_inverse_head_shoulders,
    detect_ascending_triangle, detect_falling_wedge,
    detect_complex_bottoming_structure
)
from .elliott_wave import (
    identify_swing_points, calculate_fibonacci_levels,
    identify_elliott_wave_pattern, calculate_elliott_wave_targets
)

__all__ = [
    'get_cme_direction_for_symbol',
    'get_cme_direction_all',
    'get_super_guppy_state',
    'compute_gmma',
    'compute_gmma_tv',
    'calculate_moving_averages_tv',
    'calculate_moving_averages_ta',
    'calculate_adx',
    'calculate_cci',
    'calculate_obv',
    'calculate_acc_dist',
    'calculate_macd',
    'calculate_atr',
    'calculate_momentum',
    'calculate_4w_low',
    'calculate_price_intensity',
    'detect_explosive_move_setup',
    'get_hash_ribbon_signal_for_stock',
    'calculate_hash_ribbon',
    'get_market_context',
    'detect_double_bottom',
    'detect_inverse_head_shoulders',
    'detect_ascending_triangle',
    'detect_falling_wedge',
    'detect_complex_bottoming_structure',
    'identify_swing_points',
    'calculate_fibonacci_levels',
    'identify_elliott_wave_pattern',
    'calculate_elliott_wave_targets',
]
