"""
Read composite scores / indicators from technical_analysis result JSON (*_results.json).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from technical_reasons import weighted_oscillator_bias  # noqa: E402

TA_METHODS: Tuple[str, ...] = ("ta_library", "tradingview_library")
MISSING_AVG_SCORE = -9999.0

# Pulled from ta_library blocks into index metrics (no extra table columns).
TA_BOOL_FIELDS: Tuple[str, ...] = (
    "macd_bullish",
    "macd_positive",
    "adx_strong_trend",
    "obv_trending_up",
    "acc_dist_trending_up",
    "gmma_bullish",
    "volume_above_avg",
)
TA_FLOAT_FIELDS: Tuple[str, ...] = (
    "score",
    "rsi",
    "adx",
    "momentum",
    "close",
    "ema50",
)


def get_ta_block(
    symbol_data: dict,
    timeframe: str,
    denom: str = "usd",
    methods: Sequence[str] = TA_METHODS,
) -> Optional[dict]:
    """Return ta_library or tradingview_library block for one timeframe × denom."""
    try:
        yf_tf = symbol_data[timeframe]["yfinance"][denom]
    except (KeyError, TypeError):
        return None
    for method in methods:
        try:
            block = yf_tf[method]
            if isinstance(block, dict):
                return block
        except (KeyError, TypeError):
            continue
    return None


def ta_float(ta_block: Optional[dict], field: str) -> Optional[float]:
    if not ta_block:
        return None
    raw = ta_block.get(field)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def ta_bool(ta_block: Optional[dict], field: str) -> Optional[bool]:
    if not ta_block:
        return None
    raw = ta_block.get(field)
    if raw is None:
        return None
    return bool(raw)


def avg_ta_score(
    symbol_data: dict,
    timeframes: Sequence[str],
    denom: str = "usd",
    *,
    missing_sentinel: float = MISSING_AVG_SCORE,
) -> float:
    scores: List[float] = []
    for tf in timeframes:
        sc = ta_float(get_ta_block(symbol_data, tf, denom), "score")
        if sc is not None:
            scores.append(sc)
    if not scores:
        return missing_sentinel
    return sum(scores) / len(scores)


def _store_ta_fields(metrics: Dict[str, Any], tf: str, ta: Optional[dict], *, stoch_prefix: str) -> None:
    for field in TA_FLOAT_FIELDS:
        metrics[f"{tf}_{field}"] = ta_float(ta, field)
    for field in TA_BOOL_FIELDS:
        val = ta_bool(ta, field)
        metrics[f"{tf}_{field}"] = val
    metrics[f"{tf}_{stoch_prefix}"] = None
    metrics[f"{tf}_{stoch_prefix}_d"] = None


def collect_ta_metrics(
    symbol_data: dict,
    timeframes: Sequence[str],
    denom: str = "usd",
    *,
    stoch_prefix: str = "stoch",
) -> Dict[str, Any]:
    """Per-timeframe score, oscillators, MACD/ADX/momentum/volume flags."""
    out: Dict[str, Any] = {}
    for tf in timeframes:
        _store_ta_fields(out, tf, get_ta_block(symbol_data, tf, denom), stoch_prefix=stoch_prefix)
    return out


def indicator_consensus_bias(metrics: Dict[str, Any], timeframes: Sequence[str]) -> float:
    """
    -1..+1 alignment of MACD, trend (price vs EMA50), ADX, OBV, momentum across TFs.
    Used to refine the displayed Tech score (small weight vs composite score).
    """
    biases: List[float] = []
    for tf in timeframes:
        if metrics.get(f"{tf}_score") is None and metrics.get(f"{tf}_rsi") is None:
            continue
        b = 0.0
        if metrics.get(f"{tf}_macd_bullish"):
            b += 0.35
        elif metrics.get(f"{tf}_macd_positive"):
            b += 0.15
        else:
            b -= 0.2
        close = metrics.get(f"{tf}_close")
        ema50 = metrics.get(f"{tf}_ema50")
        if close is not None and ema50 is not None and ema50 > 0:
            b += 0.25 if close >= ema50 else -0.2
        adx = metrics.get(f"{tf}_adx")
        if adx is not None:
            if adx >= 25 or metrics.get(f"{tf}_adx_strong_trend"):
                b += 0.15
            elif adx < 15:
                b -= 0.1
        mom = metrics.get(f"{tf}_momentum")
        if mom is not None:
            if mom > 3:
                b += 0.2
            elif mom < -3:
                b -= 0.2
        if metrics.get(f"{tf}_obv_trending_up"):
            b += 0.15
        if metrics.get(f"{tf}_gmma_bullish"):
            b += 0.15
        if metrics.get(f"{tf}_volume_above_avg"):
            b += 0.05
        biases.append(max(min(b, 1.0), -1.0))
    if not biases:
        return 0.0
    return sum(biases) / len(biases)


def avg_and_metrics(
    symbol_data: dict,
    timeframes: Sequence[str],
    denom: str = "usd",
    *,
    missing_sentinel: float = MISSING_AVG_SCORE,
    stoch_key: str = "stoch",
) -> Tuple[float, Dict[str, Any]]:
    metrics = collect_ta_metrics(symbol_data, timeframes, denom, stoch_prefix=stoch_key)
    scores = [metrics[f"{tf}_score"] for tf in timeframes if metrics.get(f"{tf}_score") is not None]
    avg = sum(scores) / len(scores) if scores else missing_sentinel
    return avg, metrics


def tech_score_to_display(avg: float, *, missing_threshold: float = -900.0) -> float:
    """Map avg composite (~ -5..15) to 0–10 for index tables."""
    if avg <= missing_threshold:
        return 0.0
    return min(max((avg + 2) * 0.55, 0.0), 10.0)


def rsi_score_adjustment(metrics: Dict[str, Any], timeframes: Sequence[str]) -> float:
    """Map weighted RSI + Stoch bias to ±2.5 adjustment on the 0–10 Tech score."""
    return weighted_oscillator_bias(metrics, timeframes) * 0.65


def index_tech_score(
    avg: float,
    metrics: Dict[str, Any],
    timeframes: Sequence[str],
    *,
    missing_threshold: float = -900.0,
) -> float:
    """
    Blend composite TA score with indicator consensus and RSI rule.
    RSI < 30 lifts score (lower = more); RSI > 70 lowers score (higher = more).
    Stoch < 20 lifts; Stoch > 80 lowers (blended 65/35 with RSI when both present).
    """
    base = tech_score_to_display(avg, missing_threshold=missing_threshold)
    if avg <= missing_threshold:
        return base
    consensus = indicator_consensus_bias(metrics, timeframes)
    rsi_adj = rsi_score_adjustment(metrics, timeframes)
    adjusted = base + consensus * 0.8 + rsi_adj
    return round(min(max(adjusted, 0.0), 10.0), 1)
