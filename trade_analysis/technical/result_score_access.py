"""
Read composite scores / RSI from technical_analysis result JSON (*_results.json).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

TA_METHODS: Tuple[str, ...] = ("ta_library", "tradingview_library")
MISSING_AVG_SCORE = -9999.0


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


def collect_ta_metrics(
    symbol_data: dict,
    timeframes: Sequence[str],
    denom: str = "usd",
    *,
    stoch_prefix: str = "stoch",
) -> Dict[str, Optional[float]]:
    """Per-timeframe score, rsi, and optional empty stoch slots."""
    out: Dict[str, Optional[float]] = {}
    for tf in timeframes:
        ta = get_ta_block(symbol_data, tf, denom)
        out[f"{tf}_score"] = ta_float(ta, "score")
        out[f"{tf}_rsi"] = ta_float(ta, "rsi")
        out[f"{tf}_{stoch_prefix}"] = None
    return out


def avg_and_metrics(
    symbol_data: dict,
    timeframes: Sequence[str],
    denom: str = "usd",
    *,
    missing_sentinel: float = MISSING_AVG_SCORE,
    stoch_key: str = "stoch",
) -> Tuple[float, Dict[str, Optional[float]]]:
    metrics = collect_ta_metrics(symbol_data, timeframes, denom, stoch_prefix=stoch_key)
    scores = [metrics[f"{tf}_score"] for tf in timeframes if metrics.get(f"{tf}_score") is not None]
    avg = sum(scores) / len(scores) if scores else missing_sentinel
    return avg, metrics


def tech_score_to_display(avg: float, *, missing_threshold: float = -900.0) -> float:
    """Map avg composite (~ -5..15) to 0–10 for index tables."""
    if avg <= missing_threshold:
        return 0.0
    return min(max((avg + 2) * 0.55, 0.0), 10.0)
