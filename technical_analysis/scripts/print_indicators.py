#!/usr/bin/env python3
"""
Print indicators for any category or symbol and timeframes.

Programmatic usage:
  from scripts.print_indicators import print_indicators, Indicator

  print_indicators(
    [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200, Indicator.ELLIOTT_WAVE_COUNT],
    ["BTC-USD", "precious_metals", "index_etfs"],
    ["1D", "1W", "1M"],
  )

Aliases and tickers live in technical_analysis/configuration.json (symbol_aliases, category_aliases).
- "BTC" -> config resolves to BTC-USD data; "GOLD" -> GC=F.
- "BTC/GOLD" -> BTC vs GOLD: both symbols resolved and printed (BTC-USD, GC=F).

Default run: precious_metals, [sma50, sma100, sma200, elliott_wave], [1W, 1M].

Run in console (from technical_analysis/):
  python scripts/print_indicators.py
  python scripts/print_indicators.py --indicators sma50 sma200 elliott_wave --categories BTC PRECIOUS_METALS --timeframes 1W 1M
  python scripts/print_indicators.py --categories BTC/GOLD --timeframes 1W 1M
  python scripts/print_indicators.py --help
"""

import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Allow running from scripts/ or technical_analysis/
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if getattr(sys, "_print_indicators_chdir", True):
    os.chdir(ROOT)

RESULTS_DIR = ROOT / "result_scores"
SYMBOLS_CONFIG_PATH = ROOT / "symbols_config.json"

try:
    from config_loader import load_configuration
except ImportError:
    from technical_analysis.config_loader import load_configuration


class Indicator(str, Enum):
    """Indicators that can be printed. Use these in the indicators array."""
    SMA_50 = "sma50"
    SMA_100 = "sma100"
    SMA_200 = "sma200"
    ELLIOTT_WAVE_COUNT = "elliott_wave"


def _load_symbols_config() -> Dict[str, List[str]]:
    if not SYMBOLS_CONFIG_PATH.exists():
        return {}
    with open(SYMBOLS_CONFIG_PATH) as f:
        return json.load(f)


def _load_result_file(category_key: str) -> Optional[Dict]:
    path = RESULTS_DIR / f"{category_key}_results.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _find_category_for_symbol(symbol: str, symbols_config: Dict[str, List[str]]) -> Optional[str]:
    for cat, symbols in symbols_config.items():
        if symbol in symbols:
            return cat
    return None


def _resolve_one(
    item: str,
    symbols_config: Dict[str, List[str]],
    config: Dict[str, Any],
) -> Optional[Tuple[str, str]]:
    """Resolve one token to (ticker, category_key). Uses configuration.json symbol_aliases then category_aliases + symbols_config."""
    item = (item or "").strip()
    if not item:
        return None
    symbol_aliases = config.get("symbol_aliases") or {}
    category_aliases = config.get("category_aliases") or {}

    # Normalize for lookup: as-is, upper, and key with underscores
    key_plain = item.replace(" ", "_")
    key_lower = key_plain.lower()
    key_upper = key_plain.upper()

    # 1) Symbol alias: user says BTC -> data ticker BTC-USD
    for k in (item, key_plain, key_upper, key_lower):
        if k in symbol_aliases:
            ticker = symbol_aliases[k]
            cat = _find_category_for_symbol(ticker, symbols_config)
            return (ticker, cat or "unknown")

    # 2) Category alias: user says PRECIOUS_METALS -> category key precious_metals (handled by caller for expansion)
    if key_lower in category_aliases:
        cat_key = category_aliases[key_lower]
        if cat_key in symbols_config:
            return None  # signal: expand category (caller will iterate symbols)

    # 3) Direct category key in symbols_config
    if key_lower in symbols_config:
        return None  # signal: expand category

    # 4) Already a known ticker in symbols_config
    cat = _find_category_for_symbol(item, symbols_config)
    if cat:
        return (item, cat)

    return (item, "unknown")


def resolve_categories_or_symbols(
    categories_or_symbols: Sequence[str],
    symbols_config: Optional[Dict[str, List[str]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, str]]:
    """
    Resolve user input to list of (symbol, category_key).
    - "BTC" -> lookup in configuration.json symbol_aliases -> BTC-USD data.
    - "BTC/GOLD" -> resolve each; show BTC-USD vs GC=F (both symbols in list).
    - Category (e.g. precious_metals, PRECIOUS_METALS) -> all symbols in that category (from symbols_config).
    """
    if symbols_config is None:
        symbols_config = _load_symbols_config()
    if config is None:
        config = load_configuration()
    out: List[Tuple[str, str]] = []
    seen_symbols: set = set()

    for item in categories_or_symbols:
        item = (item or "").strip()
        if not item:
            continue

        # Pair: BTC/GOLD -> resolve each part and add both (BTC vs GOLD data)
        if "/" in item:
            parts = [p.strip() for p in item.split("/") if p.strip()]
            for part in parts:
                one = _resolve_one(part, symbols_config, config)
                if one:
                    sym, cat = one
                    if sym not in seen_symbols:
                        seen_symbols.add(sym)
                        out.append((sym, cat))
            continue

        one = _resolve_one(item, symbols_config, config)
        if one is not None:
            sym, cat = one
            if sym not in seen_symbols:
                seen_symbols.add(sym)
                out.append((sym, cat))
            continue

        # Expand category: key_lower is a category in config or symbols_config
        category_aliases = config.get("category_aliases") or {}
        key_lower = item.replace(" ", "_").lower()
        cat_key = category_aliases.get(key_lower) or (key_lower if key_lower in symbols_config else None)
        if cat_key and cat_key in symbols_config:
            for sym in symbols_config[cat_key]:
                if sym not in seen_symbols:
                    seen_symbols.add(sym)
                    out.append((sym, cat_key))
            continue

        # Unknown: add as symbol
        if item not in seen_symbols:
            seen_symbols.add(item)
            out.append((item, "unknown"))

    return out


def _get_ta_from_results(symbol: str, tf: str, category_key: str) -> Optional[Dict]:
    data = _load_result_file(category_key)
    if not data or symbol not in data:
        return None
    tf_data = data[symbol].get(tf, {})
    yf = tf_data.get("yfinance", {})
    usd = yf.get("usd", {})
    return usd.get("ta_library") or usd.get("tradingview_library")


def _find_result_file_for_symbol(symbol: str) -> Optional[Tuple[Dict, str]]:
    """Search result_scores for a file containing symbol. Returns (data, category_key) or None."""
    if not RESULTS_DIR.exists():
        return None
    for path in RESULTS_DIR.glob("*_results.json"):
        if path.name in ("market_caps.json", "esg_ratings.json", "performance_vs_btc_eth.json", "performance_vs_spy.json"):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue
        if symbol in data:
            category_key = path.stem.replace("_results", "")
            return (data, category_key)
    return None


def _get_ta_for_symbol_tf(symbol: str, tf: str, category_key: str) -> Optional[Dict]:
    if category_key != "unknown":
        ta = _get_ta_from_results(symbol, tf, category_key)
        if ta is not None:
            return ta
    found = _find_result_file_for_symbol(symbol)
    if found:
        data, ck = found
        return _get_ta_from_results(symbol, tf, ck)
    return None


def _compute_sma(close_series, period: int) -> Optional[float]:
    if close_series is None or len(close_series) < period:
        return None
    try:
        val = close_series.rolling(window=period).mean().iloc[-1]
        return round(float(val), 4)
    except Exception:
        return None


def _compute_elliott_wave(close_series, high_series=None, low_series=None) -> Optional[Dict]:
    if close_series is None or len(close_series) < 40:
        return None
    try:
        from indicators.elliott_wave import calculate_elliott_wave_targets
    except ImportError:
        try:
            from technical_analysis.indicators.elliott_wave import calculate_elliott_wave_targets
        except ImportError:
            return None
    high = high_series if high_series is not None else close_series
    low = low_series if low_series is not None else close_series
    return calculate_elliott_wave_targets(close_series, high, low)


def _fetch_and_compute(
    symbol: str,
    tf: str,
    indicator: Indicator,
    category_key: str,
) -> Any:
    try:
        from technical_analysis import download_data, resample_ohlcv
    except ImportError:
        return None
    tf_rules = {"1D": "1D", "1W": "7D", "2W": "14D", "1M": "30D", "2D": "2D", "2M": "60D", "6M": "180D"}
    rule = tf_rules.get(tf, "7D")
    period = "2y" if tf == "1M" else "1y"
    cat = category_key if category_key != "unknown" else "precious_metals"
    df = download_data(symbol, period=period, category=cat, use_cache=True, force_refresh=False)
    if df is None or len(df) < 100:
        return None
    resampled = resample_ohlcv(df, rule)
    if resampled is None or len(resampled) < 50:
        return None
    close = resampled["Close"]
    high = resampled["High"] if "High" in resampled.columns else close
    low = resampled["Low"] if "Low" in resampled.columns else close

    if indicator == Indicator.SMA_50:
        return _compute_sma(close, 50)
    if indicator == Indicator.SMA_100:
        return _compute_sma(close, 100)
    if indicator == Indicator.SMA_200:
        return _compute_sma(close, 200)
    if indicator == Indicator.ELLIOTT_WAVE_COUNT:
        return _compute_elliott_wave(close, high, low)
    return None


def _get_indicator_value(
    symbol: str,
    tf: str,
    indicator: Indicator,
    category_key: str,
) -> Any:
    # 1) From result file
    ta = _get_ta_for_symbol_tf(symbol, tf, category_key)
    if ta is not None:
        if indicator == Indicator.SMA_50:
            return ta.get("sma50")
        if indicator == Indicator.SMA_200:
            return ta.get("sma200")
        if indicator == Indicator.SMA_100:
            # Often not in results; compute on the fly below
            pass
        if indicator == Indicator.ELLIOTT_WAVE_COUNT:
            ew = ta.get("elliott_wave")
            if isinstance(ew, dict):
                return ew
            return None
        if indicator.value in ta:
            return ta[indicator.value]

    # 2) On-the-fly
    return _fetch_and_compute(symbol, tf, indicator, category_key)


def _format_elliott_wave(ew: Optional[Dict]) -> str:
    if not ew or not isinstance(ew, dict):
        return "—"
    pos = ew.get("wave_position", "—")
    wc = ew.get("wave_count")
    if wc and isinstance(wc, dict):
        primary = wc.get("primary") or {}
        waves = primary.get("waves") or []
        parts = [pos]
        for w in waves[:3]:
            s = w.get("start_usd")
            e = w.get("end_usd")
            star = " ★" if w.get("current_wave") else ""
            if s is not None and e is not None:
                parts.append(f"W{w.get('number', '?')}: {s}→{e}{star}")
        return " | ".join(parts) if len(parts) > 1 else pos
    return str(pos)


def print_indicators(
    indicators: Sequence[Indicator],
    categories_or_symbols: Sequence[str],
    timeframes: Sequence[str],
    *,
    use_enum: bool = True,
) -> None:
    """
    Print requested indicators for the given categories/symbols and timeframes.

    - indicators: list of Indicator enum (e.g. [Indicator.SMA_50, Indicator.ELLIOTT_WAVE_COUNT])
    - categories_or_symbols: e.g. ["BTC-USD", "precious_metals", "index_etfs"]
    - timeframes: e.g. ["1D", "1W", "1M"]
    """
    # Normalize: accept strings like "SMA_50" or "elliott_wave"
    ind_list: List[Indicator] = []
    for i in indicators:
        if isinstance(i, Indicator):
            ind_list.append(i)
        elif isinstance(i, str):
            try:
                ind_list.append(Indicator(i.strip().lower().replace(" ", "_")))
            except ValueError:
                for e in Indicator:
                    if e.name == i.upper() or e.value == i.lower():
                        ind_list.append(e)
                        break

    symbols_config = _load_symbols_config()
    resolved = resolve_categories_or_symbols(categories_or_symbols, symbols_config)
    if not resolved:
        print("No symbols resolved from categories_or_symbols.")
        return

    tf_list = [t.strip().upper() or "1W" for t in timeframes if t and str(t).strip()]
    if not tf_list:
        tf_list = ["1W", "1M"]

    sep = "=" * 80
    print(sep)
    print("  INDICATORS REPORT")
    print(f"  Indicators: {[i.value for i in ind_list]}")
    print(f"  Timeframes: {tf_list}")
    print(sep)

    for symbol, category_key in resolved:
        print()
        print(f"  {symbol}  (category: {category_key})")
        print("-" * 60)
        for tf in tf_list:
            row: List[str] = [f"  {tf}:"]
            for ind in ind_list:
                val = _get_indicator_value(symbol, tf, ind, category_key)
                if ind == Indicator.ELLIOTT_WAVE_COUNT and isinstance(val, dict):
                    row.append(_format_elliott_wave(val))
                elif val is None:
                    row.append("—")
                elif isinstance(val, (int, float)):
                    row.append(f"{ind.value}={val}")
                else:
                    row.append(f"{ind.value}={val}")
            print(" | ".join(row))
        print()
    print(sep)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Print indicators for categories/symbols and timeframes.",
        epilog="""
Examples (run from technical_analysis/):
  python scripts/print_indicators.py
  python scripts/print_indicators.py --indicators sma50 sma200 elliott_wave --categories BTC precious_metals --timeframes 1W 1M
  python scripts/print_indicators.py --indicators elliott_wave --categories precious_metals --timeframes 1W 1M
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--indicators",
        nargs="+",
        default=["sma50", "sma100", "sma200", "elliott_wave"],
        help="Indicators: sma50, sma100, sma200, elliott_wave",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=["precious_metals"],
        help="Categories or symbols: e.g. BTC PRECIOUS_METALS index_etfs",
    )
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=["1W", "1M"],
        help="Timeframes: 1D 1W 1M",
    )
    args = parser.parse_args()

    inds = []
    for a in args.indicators:
        a = (a or "").strip().lower().replace(" ", "_")
        try:
            inds.append(Indicator(a))
        except ValueError:
            if a == "sma50":
                inds.append(Indicator.SMA_50)
            elif a == "sma100":
                inds.append(Indicator.SMA_100)
            elif a == "sma200":
                inds.append(Indicator.SMA_200)
            elif "elliott" in a or "wave" in a:
                inds.append(Indicator.ELLIOTT_WAVE_COUNT)
            else:
                print(f"Unknown indicator: {a}", file=sys.stderr)
    if not inds:
        inds = [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200, Indicator.ELLIOTT_WAVE_COUNT]

    print_indicators(inds, args.categories, args.timeframes)


if __name__ == "__main__":
    main()
