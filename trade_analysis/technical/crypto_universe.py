"""
Crypto spot universe: top N non-stablecoins by market cap + mandatory symbols (TAO, NEAR).

Used by config_loader (scoring) and build_trade_index (display as BASE/USD and BASE/BTC).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import FrozenSet, List, Optional, Set, Tuple

# yfinance spot candidates to rank (exclude stables / wrapped / ETFs by filter below).
_MCAP_CANDIDATES: Tuple[str, ...] = (
    "BTC-USD",
    "ETH-USD",
    "XRP-USD",
    "BNB-USD",
    "SOL-USD",
    "DOGE-USD",
    "ADA-USD",
    "TRX-USD",
    "AVAX-USD",
    "LINK-USD",
    "DOT-USD",
    "POL-USD",
    "ATOM-USD",
    "UNI-USD",
    "LTC-USD",
    "BCH-USD",
    "APT-USD",
    "SUI-USD",
    "HBAR-USD",
    "FIL-USD",
    "ICP-USD",
    "NEAR-USD",
    "TAO-USD",
    "SHIB-USD",
    "PEPE-USD",
)

# Known stables / pegged — never count toward top-N.
STABLE_BASES: FrozenSet[str] = frozenset(
    {
        "USDT",
        "USDC",
        "DAI",
        "BUSD",
        "TUSD",
        "USDP",
        "FDUSD",
        "PYUSD",
        "USDD",
        "EURC",
        "USDE",
        "FRAX",
        "LUSD",
        "GUSD",
        "USDS",
    }
)

# Not spot L1/L2 projects (ETFs, trust wrappers, TSX products).
NON_SPOT_SUFFIXES: Tuple[str, ...] = (".TO", "-B.TO")
NON_SPOT_TICKERS: FrozenSet[str] = frozenset(
    {
        "IBIT",
        "FBTC",
        "GBTC",
        "BITB",
        "ARKB",
        "ETHA",
        "ETHE",
        "FETH",
        "GSOL",
        "BSOL",
        "ETHX",
        "EBIT",
        "BTCC",
        "BTCX",
        "SOLA",
        "MNRS",
        "WGMI",
    }
)

ALWAYS_INCLUDE: Tuple[str, ...] = ("TAO-USD", "NEAR-USD")
TOP_N_DEFAULT = 5

# Last-resort ordering if yfinance unavailable (typical large-cap non-stables).
FALLBACK_TOP5: Tuple[str, ...] = (
    "BTC-USD",
    "ETH-USD",
    "XRP-USD",
    "BNB-USD",
    "SOL-USD",
)

_CACHE_NAME = "crypto_universe.json"


def _base_symbol(yahoo_ticker: str) -> str:
    return yahoo_ticker.upper().replace("-USD", "").split(".")[0]


def is_stablecoin(yahoo_ticker: str) -> bool:
    base = _base_symbol(yahoo_ticker)
    if base in STABLE_BASES:
        return True
    if base.startswith("USD") and len(base) <= 5:
        return True
    return False


def is_spot_crypto(yahoo_ticker: str) -> bool:
    t = yahoo_ticker.upper()
    if not t.endswith("-USD"):
        return False
    if any(t.endswith(s) for s in NON_SPOT_SUFFIXES):
        return False
    if _base_symbol(t) in NON_SPOT_TICKERS:
        return False
    if is_stablecoin(t):
        return False
    return True


def _cache_path() -> Path:
    return Path(__file__).resolve().parent / "result_scores" / _CACHE_NAME


def _read_cache() -> Optional[List[str]]:
    p = _cache_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        syms = data.get("symbols")
        if isinstance(syms, list) and syms:
            return [str(s) for s in syms]
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _write_cache(symbols: List[str]) -> None:
    p = _cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"symbols": symbols, "policy": f"top{TOP_N_DEFAULT}_non_stable_plus_tao_near"}, indent=2),
        encoding="utf-8",
    )


def fetch_market_caps(candidates: Tuple[str, ...]) -> List[Tuple[str, float]]:
    import yfinance as yf

    ranked: List[Tuple[str, float]] = []
    for sym in candidates:
        if not is_spot_crypto(sym):
            continue
        try:
            info = yf.Ticker(sym).info or {}
            mc = info.get("marketCap")
            if mc is not None and float(mc) > 0:
                ranked.append((sym, float(mc)))
        except Exception:
            continue
    ranked.sort(key=lambda x: -x[1])
    return ranked


def resolve_crypto_symbols(
    top_n: int = TOP_N_DEFAULT,
    always_include: Tuple[str, ...] = ALWAYS_INCLUDE,
    use_network: bool = True,
    force_refresh: bool = False,
) -> List[str]:
    """
    Top `top_n` non-stable spot coins by market cap + always_include (TAO, NEAR).
    Deduplicated, stable order.
    """
    if not force_refresh:
        cached = _read_cache()
        if cached:
            return cached

    top: List[str] = []
    if use_network:
        try:
            ranked = fetch_market_caps(_MCAP_CANDIDATES)
            top = [s for s, _ in ranked[:top_n]]
        except Exception:
            top = []

    if len(top) < top_n:
        for s in FALLBACK_TOP5:
            if s not in top:
                top.append(s)
            if len(top) >= top_n:
                break
        top = top[:top_n]

    out: List[str] = []
    seen: Set[str] = set()
    for s in top + list(always_include):
        su = s.upper()
        if not is_spot_crypto(su) and su not in {a.upper() for a in always_include}:
            continue
        if su not in seen:
            seen.add(su)
            out.append(su)
    _write_cache(out)
    return out


def display_pair(base_yahoo: str, quote: str) -> str:
    """ETH-USD + usd -> ETH/USD; + btc -> ETH/BTC."""
    base = _base_symbol(base_yahoo)
    q = quote.lower()
    if q in ("usd", "usdt"):
        return f"{base}/USD"
    if q == "btc":
        return f"{base}/BTC"
    return f"{base}/{quote.upper()}"


def index_pairs_for_symbol(yahoo_ticker: str) -> List[Tuple[str, str]]:
    """
    Rows to emit in trade index: (display_ticker, yfinance denom key).
    BTC-USD -> only BTC/USD. Others -> BASE/USD + BASE/BTC.
    """
    base = _base_symbol(yahoo_ticker)
    pairs: List[Tuple[str, str]] = [(display_pair(yahoo_ticker, "usd"), "usd")]
    if base != "BTC":
        pairs.append((display_pair(yahoo_ticker, "btc"), "btc_denominated"))
    return pairs


def allowed_crypto_set(use_network: bool = False) -> Set[str]:
    return set(resolve_crypto_symbols(use_network=use_network, force_refresh=False))
