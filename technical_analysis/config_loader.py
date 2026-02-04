"""
Single place to load configuration.json. Use from any script; do not repeat config/alias logic.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
CONFIGURATION_PATH = ROOT / "configuration.json"

_cached_config: Optional[Dict[str, Any]] = None


def load_configuration(force_reload: bool = False) -> Dict[str, Any]:
    """Load configuration.json: symbol_aliases, category_aliases, symbol_display_names, category_display_names, gold_silver_tickers."""
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config
    if not CONFIGURATION_PATH.exists():
        _cached_config = {
            "symbol_aliases": {},
            "category_aliases": {},
            "symbol_display_names": {},
            "category_display_names": {},
            "gold_silver_tickers": ["GC=F", "SI=F"],
            "ticker_download_category": {"GC=F": "gold", "SI=F": "precious_metals"},
        }
        return _cached_config
    with open(CONFIGURATION_PATH) as f:
        data = json.load(f)
    _cached_config = {
        "symbol_aliases": data.get("symbol_aliases") or {},
        "category_aliases": {
            k.strip().replace(" ", "_"): v
            for k, v in (data.get("category_aliases") or {}).items()
        },
        "symbol_display_names": data.get("symbol_display_names") or {},
        "category_display_names": data.get("category_display_names") or {},
        "gold_silver_tickers": data.get("gold_silver_tickers") or ["GC=F", "SI=F"],
        "ticker_download_category": data.get("ticker_download_category") or {"GC=F": "gold", "SI=F": "precious_metals"},
    }
    return _cached_config


def get_ticker(alias: str) -> Optional[str]:
    """Resolve alias to data ticker (e.g. BTC -> BTC-USD, GOLD -> GC=F)."""
    cfg = load_configuration()
    aliases = cfg.get("symbol_aliases") or {}
    for k in (alias, alias.replace(" ", "_"), alias.upper(), alias.lower()):
        if k in aliases:
            return aliases[k]
    return aliases.get(alias) if alias in aliases else None


def get_display_name_symbol(ticker: str) -> str:
    """Display name for ticker (e.g. GC=F -> Gold). Falls back to ticker if not in config."""
    cfg = load_configuration()
    names = cfg.get("symbol_display_names") or {}
    return names.get(ticker, ticker)


def get_display_name_category(category_key: str) -> str:
    """Display name for category (e.g. precious_metals -> Precious Metals). Falls back to category_key."""
    cfg = load_configuration()
    names = cfg.get("category_display_names") or {}
    return names.get(category_key, category_key.replace("_", " ").title())


def get_gold_silver_tickers() -> List[str]:
    """Tickers used for gold/silver analysis (GC=F, SI=F)."""
    cfg = load_configuration()
    return list(cfg.get("gold_silver_tickers") or ["GC=F", "SI=F"])


def get_download_category_for_ticker(ticker: str) -> str:
    """Category used for download_data/cache (e.g. GC=F -> gold, SI=F -> precious_metals). Default precious_metals."""
    cfg = load_configuration()
    mapping = cfg.get("ticker_download_category") or {}
    return mapping.get(ticker, "precious_metals")
