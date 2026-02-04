#!/usr/bin/env python3
"""
Gold & Silver vs USD — refresh data, run full analysis, and print sell/buy recommendation
based on indicators (especially monthly RSI). Use: sell when monthly RSI very overbought,
buy back when RSI returns to averages (e.g. 40–50).
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Allow running from scripts/ or technical_analysis/
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

RESULTS_FILE = ROOT / "result_scores" / "precious_metals_results.json"
TIMEFRAMES_ORDER = ["2D", "1W", "2W", "1M", "2M", "6M"]
EW_TIMEFRAMES = {"1W": "7D", "2W": "14D", "1M": "30D"}

try:
    from config_loader import get_display_name_symbol, get_gold_silver_tickers, get_download_category_for_ticker
except ImportError:
    from technical_analysis.config_loader import get_display_name_symbol, get_gold_silver_tickers, get_download_category_for_ticker


def run_refresh_and_analysis():
    """Run technical_analysis.py --category precious_metals --refresh."""
    cmd = [sys.executable, "technical_analysis.py", "--category", "precious_metals", "--refresh"]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print("Warning: analysis exited with code", result.returncode)
        return False
    return True


def load_results():
    """Load precious_metals_results.json."""
    if not RESULTS_FILE.exists():
        return None
    with open(RESULTS_FILE, "r") as f:
        return json.load(f)


def get_usd_ta(symbol_data, tf):
    """Get USD ta_library block for a timeframe."""
    if tf not in symbol_data:
        return None
    yf = symbol_data[tf].get("yfinance", {})
    usd = yf.get("usd", {})
    return usd.get("ta_library") or usd.get("tradingview_library")


def get_ohlcv_and_elliott_wave_targets():
    """
    Load Gold and Silver OHLCV (from cache or download), resample to 1W, 2W, 1M,
    compute Elliott Wave price targets, and return a dict: symbol -> tf -> wave_analysis.
    """
    try:
        from technical_analysis import download_data, resample_ohlcv
    except ImportError:
        try:
            import technical_analysis
            download_data = technical_analysis.download_data
            resample_ohlcv = technical_analysis.resample_ohlcv
        except ImportError:
            return None
    try:
        from indicators.elliott_wave import calculate_elliott_wave_targets
    except ImportError:
        from technical_analysis.indicators.elliott_wave import calculate_elliott_wave_targets

    out = {}
    for symbol in get_gold_silver_tickers():
        category = get_download_category_for_ticker(symbol)
        df = download_data(symbol, period="5y", category=category, use_cache=True, force_refresh=False)
        if df is None or len(df) < 50:
            continue
        # resample_ohlcv expects Open, High, Low, Close, Volume (yfinance default)
        out[symbol] = {}
        for tf_label, rule in EW_TIMEFRAMES.items():
            resampled = resample_ohlcv(df, rule)
            if resampled is None or len(resampled) < 50:
                continue
            close = resampled["Close"]
            high = resampled["High"] if "High" in resampled.columns else close
            low = resampled["Low"] if "Low" in resampled.columns else close
            wave = calculate_elliott_wave_targets(close, high, low)
            if wave:
                out[symbol][tf_label] = wave
    return out if out else None


def print_elliott_wave_levels(ew_data):
    """Print Elliott Wave price targets and support/resistance for Gold and Silver."""
    if not ew_data:
        print("  (Elliott Wave: no data — run from technical_analysis with cache or network)")
        return
    print("=" * 72)
    print("  ELLIOTT WAVE — Weekly, 2W & Monthly price targets (Gold & Silver)")
    print("=" * 72)
    for symbol in get_gold_silver_tickers():
        if symbol not in ew_data or not ew_data[symbol]:
            continue
        name = get_display_name_symbol(symbol)
        print()
        print("-" * 72)
        print(f"  {name} ({symbol})")
        print("-" * 72)
        for tf in ["1W", "2W", "1M"]:
            w = ew_data[symbol].get(tf)
            if not w:
                continue
            pt = w.get("price_targets") or {}
            sr = w.get("support_resistance") or {}
            trend = w.get("trend", "—")
            pos = w.get("wave_position", "—")
            current = w.get("current_price")
            extreme = w.get("recent_extreme")
            wave_3 = pt.get("wave_3")
            wave_5 = pt.get("wave_5")
            fib_382 = sr.get("fib_382")
            fib_500 = sr.get("fib_500")
            fib_618 = sr.get("fib_618")
            print(f"  {tf} (monthly-style bars):")
            print(f"    Trend: {trend}  |  Wave: {pos}  |  Close: {current}  |  Recent extreme: {extreme}")
            w3_str = f"{wave_3:.2f}" if wave_3 is not None else "—"
            w5_str = f"{wave_5:.2f}" if wave_5 is not None else "—"
            print(f"    Price targets:  Wave 3 = {w3_str}   Wave 5 = {w5_str}")
            f382 = f"{fib_382:.2f}" if fib_382 is not None else "—"
            f500 = f"{fib_500:.2f}" if fib_500 is not None else "—"
            f618 = f"{fib_618:.2f}" if fib_618 is not None else "—"
            print(f"    Support/Resistance (Fib):  38.2% = {f382}  50% = {f500}  61.8% = {f618}")
            print()
    print("=" * 72)


def rsi_verdict(rsi):
    if rsi is None:
        return "N/A", ""
    if rsi >= 80:
        return "Extreme overbought", "Strong sell signal (mean reversion)"
    if rsi >= 70:
        return "Overbought", "Consider reducing / sell into strength"
    if 65 <= rsi < 70:
        return "Approaching overbought", "Caution; consider trimming"
    if 50 <= rsi < 65:
        return "Neutral–bullish", "Hold or add on dips"
    if 40 <= rsi < 50:
        return "Neutral", "Average zone — good for adding"
    if 30 <= rsi < 40:
        return "Oversold", "Potential buy zone"
    return "Extreme oversold", "Strong buy zone (mean reversion)"


def main():
    parser = argparse.ArgumentParser(description="Gold & Silver vs USD analysis (monthly RSI, sell/buy)")
    parser.add_argument("--refresh", action="store_true", help="Force refresh data and re-run full analysis")
    args = parser.parse_args()

    if args.refresh:
        if not run_refresh_and_analysis():
            print("Proceeding with existing results file if present.")
        print()

    data = load_results()
    if not data:
        print("No results found. Run with --refresh or run:")
        print("  python technical_analysis.py --category precious_metals --refresh")
        sys.exit(1)

    print("=" * 72)
    print("  GOLD & SILVER vs USD — Indicator summary & recommendation")
    print("=" * 72)
    print(f"  Data source: {RESULTS_FILE.name}")
    print(f"  Time: {datetime.now().isoformat()}")
    print()

    for symbol in get_gold_silver_tickers():
        if symbol not in data:
            continue
        name = get_display_name_symbol(symbol)
        symbol_data = data[symbol]

        # Get 1M (monthly) first
        ta_1m = get_usd_ta(symbol_data, "1M")
        if not ta_1m:
            continue
        close = ta_1m.get("close")
        rsi_1m = ta_1m.get("rsi")
        cci_1m = ta_1m.get("cci")
        score_1m = ta_1m.get("score")
        rsi_label, rsi_comment = rsi_verdict(rsi_1m)

        print("-" * 72)
        print(f"  {name} ({symbol})")
        print("-" * 72)
        print(f"  Close (from data): {close}")
        print(f"  Monthly (1M) RSI:  {rsi_1m} — {rsi_label}")
        print(f"  Monthly CCI:       {cci_1m}")
        print(f"  Monthly score:     {score_1m}")
        print(f"  → {rsi_comment}")
        print()

        # Score breakdown highlights (overbought/oversold terms)
        breakdown = ta_1m.get("score_breakdown") or {}
        overbought_terms = [k for k in breakdown if "overbought" in k.lower() or "overextension" in k.lower()]
        if overbought_terms:
            print("  Overbought/extension penalties in score:")
            for k in overbought_terms[:8]:
                print(f"    {k}: {breakdown[k]}")
        print()

        # RSI across timeframes
        print("  RSI by timeframe:")
        for tf in TIMEFRAMES_ORDER:
            ta = get_usd_ta(symbol_data, tf)
            if ta and ta.get("rsi") is not None:
                r = ta.get("rsi")
                label, _ = rsi_verdict(r)
                print(f"    {tf}: {r:.1f} — {label}")
        print()

    # Recommendation
    print("=" * 72)
    print("  RECOMMENDATION (indicator-based)")
    print("=" * 72)
    ta_gold_1m = get_usd_ta(data.get("GC=F", {}), "1M")
    ta_silver_1m = get_usd_ta(data.get("SI=F", {}), "1M")
    rsi_g = ta_gold_1m.get("rsi") if ta_gold_1m else None
    rsi_s = ta_silver_1m.get("rsi") if ta_silver_1m else None

    if rsi_g is not None and rsi_s is not None:
        if rsi_g >= 70 or rsi_s >= 70:
            print("  • Monthly RSI is very overbought for Gold and/or Silver.")
            print("  • SELL / REDUCE: Indicators support taking profit or trimming exposure.")
            print("  • BUY BACK: Consider re-entry when monthly RSI returns to 40–50 (averages).")
        elif rsi_g < 40 or rsi_s < 40:
            print("  • Monthly RSI is oversold — potential buy zone.")
        else:
            print("  • Monthly RSI in middle range — hold or add on dips.")
    print()
    print("  (Run with --refresh to update data; e.g. yesterday 5300 vs today 4700 will")
    print("   update closes and RSI. This summary uses the last saved result_scores.)")
    print("=" * 72)

    # Elliott Wave — Weekly, 2W & Monthly price targets
    ew_data = get_ohlcv_and_elliott_wave_targets()
    print_elliott_wave_levels(ew_data)


if __name__ == "__main__":
    main()
