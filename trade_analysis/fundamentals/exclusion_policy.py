"""
Shared industry/ticker exclusions for index, fundamentals, and hot-pick pipelines.

Excludes: military/defense, adult, alcohol, pharma/drugs (not health software, medtech, or robotics).
"""

from __future__ import annotations

from typing import FrozenSet, Set, Tuple

# Whole configuration.json categories to drop from trade index / fundamental scans.
EXCLUDED_CATEGORIES: FrozenSet[str] = frozenset(
    {
        "space_defense",
        "financials",
        "macro_trend",
    }
)

# Static ticker blocklist (base symbol or full yahoo symbol).
EXCLUDED_TICKERS: FrozenSet[str] = frozenset(
    {
        # Alcohol & tobacco
        "BUD",
        "TAP",
        "STZ",
        "DEO",
        "SAM",
        "BF.A",
        "BF.B",
        "BF-B",
        "MO",
        "PM",
        "BTI",
        # Gambling / casinos
        "LVS",
        "MGM",
        "WYNN",
        "CZR",
        "PENN",
        "DKNG",
        "FLUT",
        # Defense / military / space defense
        "PLTR",
        "LMT",
        "RTX",
        "NOC",
        "GD",
        "KTOS",
        "UMAC",
        "RKLB",
        "BA",
        "LHX",
        "HII",
        "TDG",
        "HWM",
        "AXON",
        "AVAV",
        "TXT",
        "LDOS",
        "CACI",
        "SAIC",
        # Adult
        "PLBY",
        "RICK",
        "PRTY",
        # Pharma / drug manufacturers (health software, medtech, robotics allowed)
        "JNJ",
        "PFE",
        "ABBV",
        "LLY",
        "NVO",
        "MRK",
        "BMY",
        "GILD",
        "AMGN",
        "REGN",
        "VRTX",
        "BIIB",
        "ZTS",
        "MRNA",
        "BNTX",
    }
)

EXCLUDED_INDUSTRY_KEYWORDS: FrozenSet[str] = frozenset(
    {
        "defense",
        "aerospace & defense",
        "military",
        "weapon",
        "ordnance",
        "missile",
        "gun ",
        "firearm",
        "tobacco",
        "cigarette",
        "distillery",
        "brewer",
        "brewery",
        "winery",
        "wine ",
        "spirit",
        "alcohol",
        "casino",
        "gambling",
        "betting",
        "lottery",
        "adult enter",
        "adult entertain",
        "pornograph",
        "swine",
        "pork ",
        "conventional bank",
        "money center bank",
        "regional bank",
        "thrifts & mortgage",
        "mortgage finance",
        "life insurance",
        "property & casualty insurance",
        "insurance—",
        "insurance carriers",
        "asset management & custody banks",
    }
)

# Drug / pharma — excluded even when sector is "Healthcare".
DRUG_INDUSTRY_KEYWORDS: FrozenSet[str] = frozenset(
    {
        "pharmaceutical",
        "pharma",
        "drug manufacturer",
        "drug manufacturers",
        "drug—generic",
        "drug-generic",
        "biotechnology",
    }
)

# yfinance industries that are health-adjacent but not drug makers — never keyword-exclude.
HEALTH_TECH_INDUSTRY_ALLOW: FrozenSet[str] = frozenset(
    {
        "health information",
        "healthcare technology",
        "health care technology",
        "medical instruments",
        "medical devices",
        "medical device",
        "diagnostics",
        "diagnostic",
        "research & consulting",
        "scientific & technical instruments",
    }
)

EXCLUDED_FINANCIAL_INDUSTRY_KEYWORDS: FrozenSet[str] = frozenset(
    {
        "banks",
        "savings institution",
        "insurance carriers",
        "mortgage finance",
        "life insurance",
    }
)

# Categories skipped for fundamental hot-pick scan (index exclusions + commodity macros).
FUNDAMENTAL_SCAN_SKIP_CATEGORIES: FrozenSet[str] = EXCLUDED_CATEGORIES | frozenset(
    {
        "energy_commodities",
        "agricultural_commodities",
    }
)

_BLOCKLIST_CONFIG_CATEGORIES: Tuple[str, ...] = ("space_defense", "financials")


def base_symbol(yahoo_ticker: str) -> str:
    """Normalize to base ticker for blocklist checks (BTC-USD → BTC, IVN.TO → IVN)."""
    t = yahoo_ticker.upper().strip()
    return t.replace("-USD", "").split(".")[0].split("-")[0]


def load_ticker_blocklist(
    *,
    include_config_categories: Tuple[str, ...] = _BLOCKLIST_CONFIG_CATEGORIES,
) -> frozenset[str]:
    """Static EXCLUDED_TICKERS plus symbols from excluded config categories."""
    out: set[str] = set(EXCLUDED_TICKERS)
    try:
        from config_loader import get_symbols_config

        cfg = get_symbols_config()
        for cat in include_config_categories:
            for sym in cfg.get(cat, []):
                out.add(base_symbol(sym))
    except Exception:
        pass
    return frozenset(out)


def is_blocklisted(symbol: str, blocklist: frozenset[str] | set[str]) -> bool:
    su = symbol.upper()
    return su in blocklist or base_symbol(su) in blocklist
