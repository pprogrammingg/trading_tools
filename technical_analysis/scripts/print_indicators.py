#!/usr/bin/env python3
"""
Print indicators for any category or symbol and timeframes.

Module layout:
- Indicator enum; constants from configuration.json (tf_rules, default_timeframes, result_file_exclude)
- Resolution: resolve_categories_or_symbols, _resolve_one, _load_symbols_config
- Data: _load_result_file, _get_ta_from_results, _find_result_file_for_symbol, _get_ta_for_symbol_tf,
  _fetch_and_compute, _get_indicator_value
- Formatting: _format_elliott_wave, _format_indicator_value
- Report: _normalize_indicators, _normalize_timeframes, build_report_lines, print_indicators
- CLI: main()

Programmatic usage:
  from scripts.print_indicators import print_indicators, build_report_lines, Indicator

  print_indicators(
    [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200, Indicator.ELLIOTT_WAVE_COUNT],
    ["BTC-USD", "precious_metals", "index_etfs"],
    ["1D", "1W", "1M"],
  )
  # Or get lines without printing (e.g. for tests):
  lines = build_report_lines(indicators, categories_or_symbols, timeframes, get_indicator_value=mock_fn)

Aliases and tickers: configuration.json (symbol_aliases, category_aliases). "BTC" -> BTC-USD, "GOLD" -> GC=F.
Default run: precious_metals, [sma50, sma100, sma200, elliott_wave], [1W, 1M].

Run (from technical_analysis/, use project venv):
  ../venv/bin/python scripts/print_indicators.py
  ../venv/bin/python scripts/print_indicators.py --indicators sma50 sma200 --categories BTC --timeframes 1W 1M
"""

import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# Allow running from scripts/ or technical_analysis/
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if getattr(sys, "_print_indicators_chdir", True):
    os.chdir(ROOT)

RESULTS_DIR = ROOT / "result_scores"

try:
    from config_loader import (
        load_configuration,
        get_tf_rules,
        get_default_timeframes,
        get_result_file_exclude,
        get_symbols_config,
    )
except ImportError:
    from technical_analysis.config_loader import (
        load_configuration,
        get_tf_rules,
        get_default_timeframes,
        get_result_file_exclude,
        get_symbols_config,
    )


class Indicator(str, Enum):
    """Indicators that can be printed. Use these in the indicators array."""
    SMA_50 = "sma50"
    SMA_100 = "sma100"
    SMA_200 = "sma200"
    ELLIOTT_WAVE_COUNT = "elliott_wave"


def _load_symbols_config() -> Dict[str, List[str]]:
    """Load category -> tickers from configuration.json 'categories'."""
    return get_symbols_config()


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
    ta = usd.get("ta_library") or {}
    tv = usd.get("tradingview_library") or {}
    # Merge so any key from either is available (prefer non-None)
    merged = dict(ta)
    for k, v in tv.items():
        if merged.get(k) is None and v is not None:
            merged[k] = v
    return merged if merged else (ta or tv or None)


def _find_result_file_for_symbol(symbol: str) -> Optional[Tuple[Dict, str]]:
    """Search result_scores for a file containing symbol. Returns (data, category_key) or None."""
    if not RESULTS_DIR.exists():
        return None
    exclude = get_result_file_exclude()
    for path in RESULTS_DIR.glob("*_results.json"):
        if path.name in exclude:
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
        try:
            import importlib.util
            _ta_path = ROOT / "technical_analysis.py"
            if _ta_path.exists():
                spec = importlib.util.spec_from_file_location("_ta_module", _ta_path)
                _ta = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_ta)
                download_data = _ta.download_data
                resample_ohlcv = _ta.resample_ohlcv
            else:
                return None
        except Exception:
            return None
    tf_rules = get_tf_rules()
    rule = tf_rules.get(tf, "7D")
    need_long = indicator in (Indicator.SMA_100, Indicator.SMA_200)
    min_bars = 200 if indicator == Indicator.SMA_200 else (100 if indicator == Indicator.SMA_100 else 50)
    cat = category_key if category_key != "unknown" else "precious_metals"
    # For 1W + SMA100/SMA200 we need 100/200 weekly bars; crypto gets max to ensure enough history
    if tf == "1M":
        period = "10y" if (need_long and indicator == Indicator.SMA_200) else "2y"
    elif tf == "1W" and need_long:
        period = "max" if cat == "cryptocurrencies" else "5y"
    else:
        period = "2y" if tf == "1M" else "1y"
    df = download_data(symbol, period=period, category=cat, use_cache=True, force_refresh=False)
    if df is None or len(df) < 50:
        return None
    resampled = resample_ohlcv(df, rule)
    if resampled is None or len(resampled) < min_bars:
        if need_long and period != "10y":
            period_refetch = "max" if cat == "cryptocurrencies" else ("5y" if tf == "1W" else "10y")
            df = download_data(symbol, period=period_refetch, category=cat, use_cache=False, force_refresh=True)
            if df is None or len(df) < 50:
                return None
            resampled = resample_ohlcv(df, rule)
        if resampled is None or len(resampled) < min_bars:
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
            val = ta.get("sma100")
            if val is not None:
                return val
            # Fall through to on-the-fly if not in results yet
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


def _format_indicator_value(ind: Indicator, val: Any) -> str:
    """Format a single indicator value for report output."""
    if ind == Indicator.ELLIOTT_WAVE_COUNT and isinstance(val, dict):
        return _format_elliott_wave(val)
    if val is None:
        return "—"
    if isinstance(val, (int, float)):
        return f"{ind.value}={val}"
    return f"{ind.value}={val}"


def _normalize_indicators(indicators: Sequence[Any]) -> List[Indicator]:
    """Accept Indicator enum or string (e.g. 'sma50', 'elliott_wave') and return list of Indicator."""
    ind_list: List[Indicator] = []
    for i in indicators:
        if isinstance(i, Indicator):
            ind_list.append(i)
        elif isinstance(i, str):
            s = (i or "").strip().lower().replace(" ", "_")
            try:
                ind_list.append(Indicator(s))
            except ValueError:
                for e in Indicator:
                    if e.name == (i or "").strip().upper().replace(" ", "_") or e.value == s:
                        ind_list.append(e)
                        break
    return ind_list


def _normalize_timeframes(timeframes: Sequence[str]) -> List[str]:
    """Return non-empty timeframe list or default from configuration.json."""
    tf_list = [t.strip().upper() or "1W" for t in (timeframes or []) if t and str(t).strip()]
    return tf_list if tf_list else get_default_timeframes()


# Type for optional override when building report (e.g. in tests)
GetIndicatorValueFn = Callable[[str, str, Indicator, str], Any]


def build_report_lines(
    indicators: Sequence[Indicator],
    categories_or_symbols: Sequence[str],
    timeframes: Sequence[str],
    *,
    symbols_config: Optional[Dict[str, List[str]]] = None,
    get_indicator_value: Optional[GetIndicatorValueFn] = None,
) -> List[str]:
    """
    Build the indicators report as a list of lines (no print).
    Used by print_indicators and by tests to assert on content.
    If get_indicator_value is provided, it is used instead of _get_indicator_value.
    """
    ind_list = _normalize_indicators(indicators)
    if symbols_config is None:
        symbols_config = _load_symbols_config()
    resolved = resolve_categories_or_symbols(categories_or_symbols, symbols_config)
    if not resolved:
        return ["No symbols resolved from categories_or_symbols."]

    tf_list = _normalize_timeframes(timeframes)
    get_val = get_indicator_value or _get_indicator_value
    sep = "=" * 80
    lines: List[str] = [
        sep,
        "  INDICATORS REPORT",
        f"  Indicators: {[i.value for i in ind_list]}",
        f"  Timeframes: {tf_list}",
        sep,
    ]

    for symbol, category_key in resolved:
        lines.append("")
        lines.append(f"  {symbol}  (category: {category_key})")
        lines.append("-" * 60)
        for tf in tf_list:
            row: List[str] = [f"  {tf}:"]
            for ind in ind_list:
                val = get_val(symbol, tf, ind, category_key)
                row.append(_format_indicator_value(ind, val))
            lines.append(" | ".join(row))
        lines.append("")
    lines.append(sep)
    return lines


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
    lines = build_report_lines(indicators, categories_or_symbols, timeframes)
    for line in lines:
        print(line)


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
        default=get_default_timeframes(),
        help="Timeframes: 1D 1W 1M (default from configuration.json)",
    )
    args = parser.parse_args()

    inds = _normalize_indicators(args.indicators)
    if not inds:
        for a in args.indicators:
            a = (a or "").strip().lower()
            if a and a not in ("sma50", "sma100", "sma200") and "elliott" not in a and "wave" not in a:
                print(f"Unknown indicator: {a}", file=sys.stderr)
        inds = [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200, Indicator.ELLIOTT_WAVE_COUNT]

    print_indicators(inds, args.categories, args.timeframes)


if __name__ == "__main__":
    main()
