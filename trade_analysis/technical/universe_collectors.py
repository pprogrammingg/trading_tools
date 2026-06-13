"""Collect ticker universes from config or result_scores JSON."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Sequence, Set, Tuple

_TRADE_ROOT = Path(__file__).resolve().parents[1]
if str(_TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRADE_ROOT))
for _sub in ("technical", "fundamentals"):
    _p = str(_TRADE_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from crypto_universe import allowed_crypto_set, index_pairs_for_symbol, is_spot_crypto
from exclusion_policy import EXCLUDED_CATEGORIES, load_ticker_blocklist, is_blocklisted
from fundamental_halal_screen import normalize_equity_symbol


def collect_equity_symbols_from_config(
    *,
    skip_categories: frozenset[str],
    extra_tickers: Sequence[str] = (),
) -> List[str]:
    """Equity tickers from configuration.json, minus skip categories + extras."""
    from config_loader import get_symbols_config

    cfg = get_symbols_config()
    seen: Set[str] = set()
    out: List[str] = []
    for cat, syms in cfg.items():
        if cat in skip_categories:
            continue
        for s in syms:
            n = normalize_equity_symbol(s)
            if n and n not in seen:
                seen.add(n)
                out.append(n)
    for x in extra_tickers:
        n = normalize_equity_symbol(x) or x.upper()
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def collect_index_rows_from_results(
    result_dir: Path,
    *,
    crypto_allowed: Set[str] | None = None,
) -> List[Tuple[str, str, dict, str, str]]:
    """
    Rows for trade index: (yahoo_symbol, category, symbol_data, display_ticker, denom).
    """
    import json

    rows: List[Tuple[str, str, dict, str, str]] = []
    seen_display: Set[str] = set()
    blocklist = load_ticker_blocklist()
    if crypto_allowed is None:
        crypto_allowed = allowed_crypto_set(use_network=False)
    if not result_dir.is_dir():
        return rows
    for path in sorted(result_dir.glob("*_results.json")):
        cat = path.stem.replace("_results", "")
        if cat in EXCLUDED_CATEGORIES:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for sym, sym_data in data.items():
            if not isinstance(sym_data, dict):
                continue
            if is_blocklisted(sym, blocklist):
                continue
            if cat == "cryptocurrencies":
                if sym.upper() not in crypto_allowed:
                    continue
                for display, denom in index_pairs_for_symbol(sym):
                    if display in seen_display:
                        continue
                    seen_display.add(display)
                    rows.append((sym, cat, sym_data, display, denom))
                continue
            if sym.upper().endswith("-USD") and is_spot_crypto(sym) and sym.upper() in crypto_allowed:
                continue
            if sym in seen_display:
                continue
            seen_display.add(sym)
            rows.append((sym, cat, sym_data, sym, "usd"))
    return rows
