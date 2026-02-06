"""
Shared RSI and Stoch RSI logic: load OHLCV by timeframe, compute RSI(14), Stoch RSI.
Used by: backtesting/gold_rsi_stoch_rsi_backtest.py, scripts/print_indicator_value.py.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

RSI_PERIOD = 14
STOCH_K, STOCH_D, STOCH_PERIOD = 3, 3, 14

# Timeframe -> pandas resample rule (from config or fallback)
def _tf_rules():
    try:
        from config_loader import get_tf_rules
        return get_tf_rules()
    except Exception:
        return {"4H": "4h", "1D": "1D", "2D": "2D", "3D": "3D", "1W": "7D", "2W": "14D", "1M": "30D"}


def get_ohlcv_for_timeframe(symbol: str, tf: str, category: str = "precious_metals", period: str = "5y"):
    """Load OHLCV for symbol and resample to timeframe. Returns DataFrame or None if insufficient data."""
    rules = _tf_rules()
    rule = rules.get(tf, "7D")
    min_bars = RSI_PERIOD + STOCH_PERIOD + STOCH_K + STOCH_D

    try:
        from technical_analysis import download_data, resample_ohlcv
        if tf == "4H":
            df = download_data(symbol, period="60d", interval="1h", category=category, use_cache=True)
        else:
            df = download_data(symbol, period=period, category=category, use_cache=True)
    except Exception:
        import yfinance as yf
        df = yf.download(
            symbol,
            period=period if tf != "4H" else "60d",
            interval="1d" if tf != "4H" else "1h",
            progress=False,
            auto_adjust=False,
        )
    if df is None or len(df) < min_bars:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    try:
        from technical_analysis import resample_ohlcv
        res = resample_ohlcv(df, rule)
    except Exception:
        res = df.resample(rule).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    if res is None or len(res) < min_bars:
        return None
    return res


def compute_rsi(close: pd.Series, period: int = RSI_PERIOD):
    """RSI(period). Returns series or None."""
    if close is None or len(close) < period:
        return None
    try:
        from tradingview_indicators import RSI
        return RSI(close, period)
    except Exception:
        try:
            from ta.momentum import RSIIndicator
            return RSIIndicator(close, period).rsi()
        except Exception:
            return None


def compute_stoch_rsi(close: pd.Series, rsi_period: int = RSI_PERIOD, k: int = STOCH_K, d: int = STOCH_D, stoch_period: int = STOCH_PERIOD):
    """Stoch RSI: (stoch_k_series, stoch_d_series) in 0–1, or (None, None)."""
    rsi = compute_rsi(close, rsi_period)
    if rsi is None or len(rsi) < stoch_period + k + d:
        return None, None
    try:
        from technical_analysis import compute_stochrsi_tv
        sk, sd = compute_stochrsi_tv(rsi, k_period=k, d_period=d, stoch_period=stoch_period)
        return sk, sd
    except Exception:
        return None, None


def get_current_rsi_stochrsi(df: pd.DataFrame):
    """
    Current (last) RSI and Stoch RSI %K, %D for the given OHLCV DataFrame.
    Returns (rsi_last, stoch_k_last, stoch_d_last). Stoch values in 0–100.
    """
    if df is None or len(df) == 0 or "Close" not in df.columns:
        return None, None, None
    close = df["Close"]
    rsi = compute_rsi(close)
    stoch_k, stoch_d = compute_stoch_rsi(close)
    rsi_last = float(rsi.iloc[-1]) if rsi is not None and len(rsi) else None
    if stoch_k is None or len(stoch_k) == 0:
        return rsi_last, None, None
    sk_last = float(stoch_k.iloc[-1])
    sd_last = float(stoch_d.iloc[-1]) if stoch_d is not None and len(stoch_d) else None
    # Scale 0–1 to 0–100 if needed
    if sk_last <= 1.0:
        sk_last, sd_last = sk_last * 100.0, (sd_last * 100.0 if sd_last is not None else None)
    return rsi_last, sk_last, sd_last
