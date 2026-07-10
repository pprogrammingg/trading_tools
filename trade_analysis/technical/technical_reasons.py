"""
Technical snapshot + verdict for the trade index TA column.

Five-tier call: Strong Accumulation | Accumulation | Neutral | Sell | Strong Sell (Get Out)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

Verdict = Literal[
    "Strong Accumulation",
    "Accumulation",
    "Neutral",
    "Sell",
    "Strong Sell (Get Out)",
]

TF_LABELS: Dict[str, str] = {"1W": "1W", "2W": "2W", "1M": "1M", "2M": "2M"}

# RSI: < 30 accumulation (lower = stronger), > 70 sell (higher = stronger).
RSI_ACCUM_BELOW = 30.0
RSI_SELL_ABOVE = 70.0
RSI_BIAS_MAX = 4.0
# Stoch RSI: < 20 accumulation (lower = stronger), > 80 sell (higher = stronger).
STOCH_ACCUM_BELOW = 20.0
STOCH_SELL_ABOVE = 80.0
STOCH_BIAS_MAX = 3.0
TF_RSI_WEIGHT: Dict[str, float] = {"1W": 2.0, "2W": 1.5, "1M": 1.0, "2M": 0.75}
OSC_RSI_WEIGHT = 0.65
OSC_STOCH_WEIGHT = 0.35

VERDICT_SORT_RANK: Dict[str, int] = {
    "Strong Accumulation": 0,
    "Accumulation": 1,
    "Neutral": 2,
    "Sell": 3,
    "Strong Sell (Get Out)": 4,
}


def verdict_sort_rank(verdict: str) -> int:
    return VERDICT_SORT_RANK.get(str(verdict).strip(), 2)


def rsi_verdict_bias(rsi: float) -> float:
    if rsi < RSI_ACCUM_BELOW:
        return RSI_BIAS_MAX * (RSI_ACCUM_BELOW - rsi) / RSI_ACCUM_BELOW
    if rsi > RSI_SELL_ABOVE:
        return -RSI_BIAS_MAX * min(rsi - RSI_SELL_ABOVE, 30.0) / 30.0
    return 0.0


def weighted_rsi_bias(metrics: Dict[str, Any], timeframes: Sequence[str]) -> float:
    total = 0.0
    wsum = 0.0
    for tf in timeframes:
        rsi = metrics.get(f"{tf}_rsi")
        if rsi is None:
            continue
        w = TF_RSI_WEIGHT.get(tf, 1.0)
        total += rsi_verdict_bias(float(rsi)) * w
        wsum += w
    return total / wsum if wsum else 0.0


def stoch_verdict_bias(k: float) -> float:
    if k < STOCH_ACCUM_BELOW:
        return STOCH_BIAS_MAX * (STOCH_ACCUM_BELOW - k) / STOCH_ACCUM_BELOW
    if k > STOCH_SELL_ABOVE:
        return -STOCH_BIAS_MAX * min(k - STOCH_SELL_ABOVE, 20.0) / 20.0
    return 0.0


def weighted_stoch_bias(metrics: Dict[str, Any], timeframes: Sequence[str]) -> float:
    total = 0.0
    wsum = 0.0
    for tf in timeframes:
        stoch = metrics.get(f"{tf}_stoch")
        if stoch is None:
            continue
        w = TF_RSI_WEIGHT.get(tf, 1.0)
        total += stoch_verdict_bias(float(stoch)) * w
        wsum += w
    return total / wsum if wsum else 0.0


def weighted_oscillator_bias(metrics: Dict[str, Any], timeframes: Sequence[str]) -> float:
    rsi_b = weighted_rsi_bias(metrics, timeframes)
    stoch_b = weighted_stoch_bias(metrics, timeframes)
    has_rsi = any(metrics.get(f"{tf}_rsi") is not None for tf in timeframes)
    has_stoch = any(metrics.get(f"{tf}_stoch") is not None for tf in timeframes)
    if has_rsi and has_stoch:
        if abs(rsi_b) < 0.25:
            return 0.2 * rsi_b + 0.8 * stoch_b
        return OSC_RSI_WEIGHT * rsi_b + OSC_STOCH_WEIGHT * stoch_b
    if has_stoch:
        return stoch_b
    return rsi_b


def _interpret_rsi(rsi: float) -> Tuple[str, float]:
    bias = rsi_verdict_bias(rsi)
    if rsi < 20:
        label = "very oversold"
    elif rsi < RSI_ACCUM_BELOW:
        label = "oversold"
    elif rsi <= RSI_SELL_ABOVE:
        label = "neutral"
    elif rsi <= 80:
        label = "overbought"
    else:
        label = "extreme OB"
    return label, bias


def _interpret_stoch(k: float, d: Optional[float]) -> Tuple[str, float]:
    bias = stoch_verdict_bias(k)
    if d is not None and k < STOCH_ACCUM_BELOW and d < STOCH_ACCUM_BELOW and k > d + 2:
        label = "bull x OS"
    elif d is not None and k > STOCH_SELL_ABOVE and d > STOCH_SELL_ABOVE and k < d - 2:
        label = "bear x OB"
    elif k < 10:
        label = "very oversold"
    elif k < STOCH_ACCUM_BELOW:
        label = "oversold"
    elif k <= STOCH_SELL_ABOVE:
        label = "neutral"
    elif k <= 90:
        label = "overbought"
    else:
        label = "extreme OB"
    return label, bias


def _macd_label(bullish: Optional[bool], positive: Optional[bool]) -> str:
    if bullish:
        return "bull" if positive else "cross↑"
    if positive:
        return "hist+"
    return "bear"


def _trend_label(close: Optional[float], ema50: Optional[float]) -> str:
    if close is None or ema50 is None or ema50 <= 0:
        return "—"
    return ">EMA50" if close >= ema50 else "<EMA50"


def _adx_label(adx: Optional[float], strong: Optional[bool]) -> str:
    if adx is None:
        return "—"
    tag = "strong" if (strong or adx >= 25) else ("weak" if adx < 15 else "ok")
    return f"{adx:.0f} {tag}"


def _mom_label(momentum: Optional[float]) -> str:
    if momentum is None:
        return "—"
    sign = "+" if momentum > 0 else ""
    return f"{sign}{momentum:.0f}%"


def _flow_label(obv_up: Optional[bool], acc_up: Optional[bool]) -> str:
    if obv_up and acc_up:
        return "obv+acc↑"
    if obv_up:
        return "obv↑"
    if acc_up:
        return "acc↑"
    if obv_up is False and acc_up is False:
        return "flow↓"
    return "—"


def _stoch_compact(k: Optional[float], d: Optional[float]) -> str:
    if k is None:
        return "—"
    if d is None:
        return f"{k:.0f}"
    return f"{k:.0f}/{d:.0f}"


def _other_tf_bias(metrics: Dict[str, Any], tf: str) -> float:
    b = 0.0
    if metrics.get(f"{tf}_macd_bullish"):
        b += 0.35
    elif metrics.get(f"{tf}_macd_positive"):
        b += 0.1
    else:
        b -= 0.35
    close, ema50 = metrics.get(f"{tf}_close"), metrics.get(f"{tf}_ema50")
    if close is not None and ema50 is not None and ema50 > 0:
        b += 0.35 if close >= ema50 else -0.35
    adx = metrics.get(f"{tf}_adx")
    if adx is not None and (adx >= 25 or metrics.get(f"{tf}_adx_strong_trend")):
        b += 0.25
    mom = metrics.get(f"{tf}_momentum")
    if mom is not None:
        if mom > 3:
            b += 0.25
        elif mom < -3:
            b -= 0.25
    if metrics.get(f"{tf}_obv_trending_up"):
        b += 0.2
    if metrics.get(f"{tf}_gmma_bullish"):
        b += 0.2
    return b


def format_tf_snapshot(
    tf: str,
    metrics: Dict[str, Any],
    label: str,
) -> Optional[str]:
    rsi = metrics.get(f"{tf}_rsi")
    score = metrics.get(f"{tf}_score")
    if rsi is None and score is None:
        return None

    parts: List[str] = []
    if rsi is not None:
        rsi_note, _ = _interpret_rsi(float(rsi))
        parts.append(f"rsi: {float(rsi):.0f} ({rsi_note})")
    parts.append(f"macd: {_macd_label(metrics.get(f'{tf}_macd_bullish'), metrics.get(f'{tf}_macd_positive'))}")
    sk = metrics.get(f"{tf}_stoch")
    if sk is not None:
        sd = metrics.get(f"{tf}_stoch_d")
        stoch_note, _ = _interpret_stoch(float(sk), float(sd) if sd is not None else None)
        parts.append(f"stoch: {_stoch_compact(sk, sd)} ({stoch_note})")
    else:
        parts.append("stoch: —")
    parts.append(f"adx: {_adx_label(metrics.get(f'{tf}_adx'), metrics.get(f'{tf}_adx_strong_trend'))}")
    parts.append(f"mom: {_mom_label(metrics.get(f'{tf}_momentum'))}")
    parts.append(f"trend: {_trend_label(metrics.get(f'{tf}_close'), metrics.get(f'{tf}_ema50'))}")
    flow = _flow_label(metrics.get(f"{tf}_obv_trending_up"), metrics.get(f"{tf}_acc_dist_trending_up"))
    if flow != "—":
        parts.append(flow)
    if metrics.get(f"{tf}_gmma_bullish"):
        parts.append("gmma↑")
    if metrics.get(f"{tf}_volume_above_avg"):
        parts.append("vol↑")
    if score is not None:
        parts.append(f"tech: {float(score):.1f}")

    return f"{label} | " + ", ".join(parts)


def _verdict_from_bias(total: float, n_tf: int) -> Verdict:
    if n_tf <= 0:
        return "Neutral"
    avg = total / max(n_tf, 1)
    if avg >= 2.0:
        return "Strong Accumulation"
    if avg >= 0.75:
        return "Accumulation"
    if avg <= -2.0:
        return "Strong Sell (Get Out)"
    if avg <= -0.75:
        return "Sell"
    return "Neutral"


def _compute_verdict_bias(metrics: Dict[str, Any], timeframes: Sequence[str], n_tf: int) -> float:
    osc_b = weighted_oscillator_bias(metrics, timeframes)
    if n_tf <= 0:
        return osc_b
    other = sum(_other_tf_bias(metrics, tf) for tf in timeframes) / n_tf
    if osc_b <= -0.5:
        other = min(other, 0.0)
    elif osc_b >= 0.5:
        other = max(other, 0.0)
    return osc_b + other * 0.35


def _rsi_values(metrics: Dict[str, Any], timeframes: Sequence[str]) -> List[float]:
    out: List[float] = []
    for tf in timeframes:
        rsi = metrics.get(f"{tf}_rsi")
        if rsi is not None:
            out.append(float(rsi))
    return out


def _stoch_values(metrics: Dict[str, Any], timeframes: Sequence[str]) -> List[float]:
    out: List[float] = []
    for tf in timeframes:
        stoch = metrics.get(f"{tf}_stoch")
        if stoch is not None:
            out.append(float(stoch))
    return out


def _verdict_summary(verdict: Verdict, metrics: Dict[str, Any], timeframes: Sequence[str]) -> str:
    w_rsi = metrics.get("1W_rsi")
    w_stoch = metrics.get("1W_stoch")
    all_rsi = _rsi_values(metrics, timeframes)
    all_stoch = _stoch_values(metrics, timeframes)
    max_rsi = max(all_rsi) if all_rsi else None
    min_rsi = min(all_rsi) if all_rsi else None
    max_stoch = max(all_stoch) if all_stoch else None
    min_stoch = min(all_stoch) if all_stoch else None

    if verdict in ("Strong Accumulation", "Accumulation"):
        parts: List[str] = []
        if min_rsi is not None and min_rsi < RSI_ACCUM_BELOW:
            parts.append(f"RSI < {RSI_ACCUM_BELOW:.0f} (weekly {float(w_rsi):.0f})" if w_rsi else f"RSI < {RSI_ACCUM_BELOW:.0f}")
        if min_stoch is not None and min_stoch < STOCH_ACCUM_BELOW:
            parts.append(
                f"Stoch < {STOCH_ACCUM_BELOW:.0f} (weekly {float(w_stoch):.0f})" if w_stoch else f"Stoch < {STOCH_ACCUM_BELOW:.0f}"
            )
        if parts:
            strength = " — deeply oversold." if verdict == "Strong Accumulation" else " — lower = stronger accumulation."
            return " · ".join(parts) + strength

    if verdict in ("Sell", "Strong Sell (Get Out)"):
        parts = []
        if max_rsi is not None and max_rsi > RSI_SELL_ABOVE:
            parts.append(f"RSI > {RSI_SELL_ABOVE:.0f} (peak {max_rsi:.0f})")
        if max_stoch is not None and max_stoch > STOCH_SELL_ABOVE:
            parts.append(f"Stoch > {STOCH_SELL_ABOVE:.0f} (peak {max_stoch:.0f})")
        if parts:
            strength = " — exit / reduce exposure." if verdict == "Strong Sell (Get Out)" else " — trim / take profit."
            return " · ".join(parts) + strength

    summaries = {
        "Strong Accumulation": "Deeply oversold RSI/Stoch with confirming signals.",
        "Accumulation": "RSI (< 30) and/or Stoch (< 20) in accumulation zone.",
        "Neutral": "RSI 30–70 and Stoch 20–80 — no extreme signal.",
        "Sell": "RSI and/or Stoch extended — consider trimming.",
        "Strong Sell (Get Out)": "RSI/Stoch very overbought — strong exit signal.",
    }
    return summaries[verdict]


def build_technical_reasons(
    metrics: Dict[str, Any],
    timeframes: Sequence[str] = ("1W", "2W", "1M", "2M"),
    tf_labels: Optional[Dict[str, str]] = None,
) -> Tuple[Verdict, str]:
    labels = tf_labels or TF_LABELS
    lines: List[str] = []
    used = 0

    for tf in timeframes:
        line = format_tf_snapshot(tf, metrics, labels.get(tf, tf))
        if line is None:
            continue
        used += 1
        lines.append(line)

    combined = _compute_verdict_bias(metrics, timeframes, used)
    verdict = _verdict_from_bias(combined, 1)
    if not lines:
        return "Neutral", "No TA data — run technical_analysis.py for this symbol."

    body = _verdict_summary(verdict, metrics, timeframes) + "\n" + "\n".join(lines)
    return verdict, body


def verdict_display_label(verdict: Verdict) -> str:
    if verdict == "Strong Accumulation":
        return "**Strong Accumulation**"
    if verdict == "Accumulation":
        return "**Accumulation**"
    return verdict


def verdict_color(verdict: Verdict) -> str:
    return {
        "Strong Accumulation": "#14532d",
        "Accumulation": "#15803d",
        "Neutral": "#64748b",
        "Sell": "#b45309",
        "Strong Sell (Get Out)": "#b91c1c",
    }.get(verdict, "#64748b")
