#!/usr/bin/env python3
"""
Print current indicator values (RSI, Stoch RSI, etc.) for given tickers, timeframes, and indicators.
Shared logic: scripts/rsi_stochrsi_common (get_ohlcv_for_timeframe, get_current_rsi_stochrsi).

Main API:
  print_indicator_value(tickers=None, timeframes=None, indicators=None)
  → tickers: list of symbols (e.g. ["GC=F", "BTC-USD"])
  → timeframes: list (e.g. ["4H", "1D", "3D", "1W", "1M"])
  → indicators: list (e.g. ["RSI", "StochRSI"]). Supported: RSI, StochRSI.

Usage (from technical_analysis/; use venv so pandas/yfinance are available):
  source .venv/bin/activate && python3 scripts/print_indicator_value.py --tickers GC=F BTC-USD --timeframes 4H 1D 3D 1W 1M
  # Or without activating: .venv/bin/python scripts/print_indicator_value.py --tickers GC=F BTC-USD ...
"""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Defaults
DEFAULT_TIMEFRAMES = ["4H", "1D", "3D", "1W", "1M"]
DEFAULT_TICKERS = ["GC=F"]
DEFAULT_INDICATORS = ["RSI", "StochRSI"]


def _normalize_indicators(indicators):
    """Return list of canonical names: RSI, StochRSI."""
    out = []
    for i in (indicators or []):
        s = (i or "").strip().replace(" ", "").lower()
        if s == "rsi":
            out.append("RSI")
        elif s in ("stochrsi", "stoch_rsi"):
            out.append("StochRSI")
        else:
            out.append(i.strip() if isinstance(i, str) else str(i))
    return out if out else list(DEFAULT_INDICATORS)


def _category_for_ticker(ticker):
    """Category used for download_data (precious_metals, cryptocurrencies, etc.)."""
    try:
        from config_loader import load_configuration
        cfg = load_configuration()
        tdc = cfg.get("ticker_download_category") or {}
        if ticker in tdc:
            return tdc[ticker]
        cats = cfg.get("categories") or {}
        for cat, symbols in cats.items():
            if ticker in (symbols or []):
                return cat
    except Exception:
        pass
    return "precious_metals"


def _symbol_label(ticker):
    """Short label for table (e.g. Gold for GC=F, Bitcoin for BTC-USD)."""
    try:
        from config_loader import load_configuration
        cfg = load_configuration()
        names = cfg.get("symbol_display_names") or {}
        if ticker in names:
            return names[ticker]
    except Exception:
        pass
    return "Gold" if ticker == "GC=F" else ("Bitcoin" if ticker == "BTC-USD" else ticker)


def print_indicator_value(tickers=None, timeframes=None, indicators=None, table_style="combined"):
    """
    Print current indicator values for each ticker × timeframe in a tabulated table.

    tickers: list of symbols (e.g. ["GC=F", "BTC-USD"]). Default: ["GC=F"].
    timeframes: list (e.g. ["4H", "1D", "3D", "1W", "1M]). Default: 4H, 1D, 3D, 1W, 1M.
    indicators: list (e.g. ["RSI", "StochRSI"]). Supported: RSI, StochRSI. Default: RSI, StochRSI.
    table_style: "combined" = one table with Symbol column; "per_symbol" = one block per symbol.
    """
    from scripts.rsi_stochrsi_common import get_ohlcv_for_timeframe, get_current_rsi_stochrsi

    ticker_list = list(tickers) if tickers else list(DEFAULT_TICKERS)
    tf_list = list(timeframes) if timeframes else list(DEFAULT_TIMEFRAMES)
    ind_list = _normalize_indicators(indicators)

    w_sym, w_tf, w_rsi, w_k, w_d = 10, 6, 10, 12, 12
    header_parts = ["Symbol", "TF"]
    if "RSI" in ind_list:
        header_parts.append("RSI")
    if "StochRSI" in ind_list:
        header_parts.extend(["K (fast)", "D (slow)"])
    col_widths = [w_sym, w_tf] + [w_rsi] * (1 if "RSI" in ind_list else 0) + [w_k, w_d] * (1 if "StochRSI" in ind_list else 0)

    def fmt_row(symbol_label, tf, rsi_last, sk_last, sd_last):
        row = [symbol_label, tf]
        if "RSI" in ind_list:
            row.append(f"{rsi_last:.2f}" if rsi_last is not None else "—")
        if "StochRSI" in ind_list:
            row.append(f"{sk_last:.2f}" if sk_last is not None else "—")
            row.append(f"{sd_last:.2f}" if sd_last is not None else "—")
        return row

    if table_style == "combined" and len(ticker_list) >= 1:
        print("  " + "  ".join(p.ljust(col_widths[i]) for i, p in enumerate(header_parts)))
        print("  " + "-" * (sum(col_widths) + 2 * (len(col_widths) - 1)))

        for symbol in ticker_list:
            label = _symbol_label(symbol)
            cat = _category_for_ticker(symbol)
            for tf in tf_list:
                df = get_ohlcv_for_timeframe(symbol, tf, category=cat)
                if df is None or len(df) == 0:
                    row = fmt_row(label, tf, None, None, None)
                else:
                    rsi_last, sk_last, sd_last = get_current_rsi_stochrsi(df)
                    row = fmt_row(label, tf, rsi_last, sk_last, sd_last)
                print("  " + "  ".join(str(x).ljust(col_widths[i]) for i, x in enumerate(row)))
        return

    # Per-symbol blocks
    per_header = ["TF"] + header_parts[2:]
    per_widths = [w_tf] + col_widths[2:]
    for symbol in ticker_list:
        print("=" * 70)
        print(f"  {symbol}  —  Current: {', '.join(ind_list)}")
        print("=" * 70)
        print("  " + "  ".join(p.ljust(per_widths[i]) for i, p in enumerate(per_header)))
        print("-" * 70)

        for tf in tf_list:
            cat = _category_for_ticker(symbol)
            df = get_ohlcv_for_timeframe(symbol, tf, category=cat)
            if df is None or len(df) == 0:
                row = [tf] + ["—"] * (len(per_header) - 1)
            else:
                rsi_last, sk_last, sd_last = get_current_rsi_stochrsi(df)
                row = [tf]
                if "RSI" in ind_list:
                    row.append(f"{rsi_last:.2f}" if rsi_last is not None else "—")
                if "StochRSI" in ind_list:
                    row.append(f"{sk_last:.2f}" if sk_last is not None else "—")
                    row.append(f"{sd_last:.2f}" if sd_last is not None else "—")
            print("  " + "  ".join(str(x).ljust(per_widths[i]) for i, x in enumerate(row)))
        print("=" * 70)


def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Print current indicator values (RSI, Stoch RSI) for tickers × timeframes.",
        epilog="Example: python3 scripts/print_indicator_value.py --tickers GC=F BTC-USD --timeframes 4H 1D 1W",
    )
    p.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS, help="Ticker list (e.g. GC=F BTC-USD)")
    p.add_argument("--timeframes", nargs="+", default=DEFAULT_TIMEFRAMES, help="Timeframes (e.g. 4H 1D 3D 1W 1M)")
    p.add_argument("--indicators", nargs="+", default=DEFAULT_INDICATORS, help="Indicators (e.g. RSI StochRSI)")
    p.add_argument("--per-symbol", action="store_true", help="Print one block per symbol instead of one table")
    args = p.parse_args()

    print_indicator_value(
        tickers=args.tickers,
        timeframes=args.timeframes,
        indicators=args.indicators,
        table_style="per_symbol" if args.per_symbol else "combined",
    )


if __name__ == "__main__":
    main()
