"""Reduce yfinance noise and skip symbols that cannot return equity fundamentals."""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from typing import FrozenSet

# Yahoo often fails for these; skip network calls in bulk pipelines.
KNOWN_BAD_SYMBOLS: FrozenSet[str] = frozenset(
    {
        "BITF",
        "IVN",
        "X",
        "MATIC-USD",
    }
)

_NON_EQUITY = re.compile(r"(=F|^[\^])")


def to_float(value: object) -> Optional[float]:
    """Coerce yfinance/pandas scalar to float; None on failure."""
    if value is None:
        return None
    try:
        import pandas as pd

        if isinstance(value, pd.Series):
            if value.empty:
                return None
            value = value.iloc[-1]
        if hasattr(value, "item"):
            try:
                value = value.item()
            except (ValueError, TypeError):
                pass
        v = float(value)
        if v != v:  # NaN
            return None
        return v
    except (TypeError, ValueError):
        return None


def symbol_skips_yahoo_download(sym: str) -> bool:
    """Skip yfinance .info / short-history download for non-equity or known-bad symbols."""
    s = sym.upper().strip()
    if s in KNOWN_BAD_SYMBOLS:
        return True
    if "-USD" in s or s.endswith("-USD"):
        return True
    if _NON_EQUITY.search(s):
        return True
    return False


def symbol_skips_yahoo_fundamentals(sym: str) -> bool:
    return symbol_skips_yahoo_download(sym)


def symbol_skips_perf_download(sym: str) -> bool:
    return symbol_skips_yahoo_download(sym)


@contextmanager
def quiet_yfinance():
    """Temporarily silence yfinance/urllib3 error spam during bulk fetches."""
    names = ("yfinance", "urllib3", "charset_normalizer", "peewee")
    loggers = [logging.getLogger(n) for n in names]
    prev = [(lg, lg.level, lg.disabled) for lg in loggers]
    for lg in loggers:
        lg.setLevel(logging.CRITICAL)
        lg.disabled = True
    try:
        yield
    finally:
        for lg, level, disabled in prev:
            lg.setLevel(level)
            lg.disabled = disabled
