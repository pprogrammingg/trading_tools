#!/usr/bin/env python3
"""
Would the recent drop in altcoins like SOL vs BTC have been predicted?
Analyzes SOL/BTC ratio history and applies framework indicators (RSI, Elliott Wave)
at points before known SOL/BTC declines to see if signals would have flagged risk.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

from technical_analysis import resample_ohlcv
from indicators.elliott_wave import identify_elliott_wave_pattern


def rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def run_sol_btc_analysis(period: str = "2y", forward_weeks: int = 6, drop_threshold_pct: float = -15.0):
    """
    Load SOL-USD and BTC-USD, resample to 1W, compute SOL/BTC ratio.
    Find weeks where SOL/BTC dropped >= drop_threshold_pct over next forward_weeks.
    At each such week T, report: SOL RSI, BTC RSI, Elliott wave position for both.
    Conclusion: would RSI overbought + wave position have predicted the drop?
    """
    if yf is None:
        return {"error": "yfinance not installed"}

    sol = yf.download("SOL-USD", period=period, interval="1d", progress=False, auto_adjust=False)
    btc = yf.download("BTC-USD", period=period, interval="1d", progress=False, auto_adjust=False)
    if sol is None or len(sol) < 100 or btc is None or len(btc) < 100:
        return {"error": "Insufficient data for SOL or BTC"}

    if isinstance(sol.columns, pd.MultiIndex):
        sol.columns = sol.columns.get_level_values(0)
    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = btc.columns.get_level_values(0)

    sol_w = resample_ohlcv(sol, "7D")
    btc_w = resample_ohlcv(btc, "7D")
    if sol_w is None or btc_w is None or len(sol_w) < 30 or len(btc_w) < 30:
        return {"error": "Insufficient weekly data after resample"}

    # Align indices (use common dates)
    common = sol_w.index.intersection(btc_w.index).sort_values()
    sol_w = sol_w.reindex(common).ffill().bfill()
    btc_w = btc_w.reindex(common).ffill().bfill()

    ratio = sol_w["Close"] / (btc_w["Close"] + 1e-12)
    lookback = 20
    max_fwd = forward_weeks
    if len(ratio) < lookback * 2 + max_fwd:
        return {"error": "Not enough bars for lookback + forward"}

    # Find weeks T where ratio dropped >= drop_threshold_pct by T+forward_weeks
    events = []
    for i in range(lookback * 2, len(ratio) - max_fwd):
        r0 = ratio.iloc[i]
        r1 = ratio.iloc[i + forward_weeks]
        pct = (r1 - r0) / r0 * 100
        if pct <= drop_threshold_pct:
            t_date = ratio.index[i]
            sol_close = sol_w["Close"].reindex(ratio.index[: i + 1]).ffill()
            btc_close = btc_w["Close"].reindex(ratio.index[: i + 1]).ffill()
            sol_hist = sol_close.iloc[-lookback * 2 :]
            btc_hist = btc_close.iloc[-lookback * 2 :]
            if len(sol_hist) < lookback * 2 or len(btc_hist) < lookback * 2:
                continue
            sol_rsi = rsi_series(sol_hist, 14)
            btc_rsi = rsi_series(btc_hist, 14)
            sol_rsi_val = sol_rsi.iloc[-1] if len(sol_rsi) and not pd.isna(sol_rsi.iloc[-1]) else None
            btc_rsi_val = btc_rsi.iloc[-1] if len(btc_rsi) and not pd.isna(btc_rsi.iloc[-1]) else None
            ew_sol = identify_elliott_wave_pattern(sol_hist, lookback=lookback)
            ew_btc = identify_elliott_wave_pattern(btc_hist, lookback=lookback)
            events.append({
                "date": str(t_date)[:10],
                "sol_btc_drop_pct": round(pct, 2),
                "sol_rsi": round(sol_rsi_val, 2) if sol_rsi_val is not None else None,
                "btc_rsi": round(btc_rsi_val, 2) if btc_rsi_val is not None else None,
                "sol_wave": ew_sol.get("wave_position") if ew_sol else None,
                "btc_wave": ew_btc.get("wave_position") if ew_btc else None,
            })
    # Sort by drop severity (most negative first)
    events.sort(key=lambda x: x["sol_btc_drop_pct"])

    # Conclusion: would framework have predicted? (SOL RSI > 70 or SOL in Wave 3/5 = risk flag)
    predicted = sum(
        1 for e in events
        if (e.get("sol_rsi") is not None and e["sol_rsi"] > 70)
        or (e.get("sol_wave") and "Wave 3 or 5" in e["sol_wave"])
    )
    conclusion = (
        f"Found {len(events)} periods where SOL/BTC dropped ≥{abs(drop_threshold_pct):.0f}% over {forward_weeks} weeks. "
        f"In {predicted} of those, framework would have flagged risk (SOL RSI > 70 or SOL in Wave 3/5). "
    )
    if len(events):
        conclusion += "Recent alt underperformance vs BTC could have been partially predicted when SOL was overbought or in extended wave."
    else:
        conclusion += "No such large drops in sample; extend period or lower threshold to test."

    return {
        "period": period,
        "forward_weeks": forward_weeks,
        "drop_threshold_pct": drop_threshold_pct,
        "events": events[:15],
        "total_events": len(events),
        "events_with_risk_signal": predicted,
        "conclusion": conclusion,
    }


if __name__ == "__main__":
    print("SOL vs BTC: would the drop have been predicted?\n")
    result = run_sol_btc_analysis(period="2y", forward_weeks=6, drop_threshold_pct=-15.0)
    if "error" in result:
        print(result["error"])
        sys.exit(1)
    print(f"Period: {result['period']}, forward: {result['forward_weeks']}w, threshold: {result['drop_threshold_pct']}%")
    print(f"Total SOL/BTC drop events: {result['total_events']}; events with risk signal (SOL RSI>70 or Wave 3/5): {result['events_with_risk_signal']}\n")
    print("Sample events (worst drops):")
    for e in result["events"][:8]:
        print(f"  {e['date']}: SOL/BTC drop {e['sol_btc_drop_pct']}% | SOL RSI={e['sol_rsi']} BTC RSI={e['btc_rsi']} | SOL wave={e['sol_wave']} BTC wave={e['btc_wave']}")
    print("\nConclusion:", result["conclusion"])
