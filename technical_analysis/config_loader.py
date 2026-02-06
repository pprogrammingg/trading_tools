"""
Single place to load configuration.json. Use from any script; do not repeat config/alias logic.
Categories (symbols by category), tf_rules, default_timeframes, result_file_exclude live in configuration.json.
Replaces symbols_config.json; categories are in configuration.json under "categories".
"""

import json
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional

ROOT = Path(__file__).resolve().parent
CONFIGURATION_PATH = ROOT / "configuration.json"

_DEFAULT_TF_RULES = {"4H": "4H", "1D": "1D", "2D": "2D", "3D": "3D", "1W": "7D", "2W": "14D", "1M": "30D", "2M": "60D", "6M": "180D"}
_DEFAULT_DEFAULT_TIMEFRAMES = ["1W", "1M"]
_DEFAULT_RESULT_FILE_EXCLUDE = frozenset({
    "market_caps.json", "esg_ratings.json", "performance_vs_btc_eth.json", "performance_vs_spy.json",
})

_cached_config: Optional[Dict[str, Any]] = None


def load_configuration(force_reload: bool = False) -> Dict[str, Any]:
    """Load configuration.json: aliases, display names, tf_rules, default_timeframes, result_file_exclude, gold_silver_tickers."""
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config
    if not CONFIGURATION_PATH.exists():
        _cached_config = {
            "categories": {},
            "max_symbols_per_category": None,
            "symbol_aliases": {},
            "category_aliases": {},
            "symbol_display_names": {},
            "category_display_names": {},
            "gold_silver_tickers": ["GC=F", "SI=F"],
            "ticker_download_category": {"GC=F": "gold", "SI=F": "precious_metals"},
            "tf_rules": dict(_DEFAULT_TF_RULES),
            "default_timeframes": list(_DEFAULT_DEFAULT_TIMEFRAMES),
            "result_file_exclude": list(_DEFAULT_RESULT_FILE_EXCLUDE),
        }
        return _cached_config
    with open(CONFIGURATION_PATH) as f:
        data = json.load(f)
    exclude = data.get("result_file_exclude")
    if isinstance(exclude, list):
        exclude = list(exclude)
    else:
        exclude = list(_DEFAULT_RESULT_FILE_EXCLUDE)
    categories = data.get("categories")
    if not isinstance(categories, dict):
        categories = {}
    max_per_cat = data.get("max_symbols_per_category")
    _cached_config = {
        "categories": {k: list(v) if isinstance(v, (list, tuple)) else [] for k, v in categories.items()},
        "max_symbols_per_category": int(max_per_cat) if max_per_cat is not None and str(max_per_cat).strip() != "" else None,
        "symbol_aliases": data.get("symbol_aliases") or {},
        "category_aliases": {
            k.strip().replace(" ", "_"): v
            for k, v in (data.get("category_aliases") or {}).items()
        },
        "symbol_display_names": data.get("symbol_display_names") or {},
        "category_display_names": data.get("category_display_names") or {},
        "gold_silver_tickers": data.get("gold_silver_tickers") or ["GC=F", "SI=F"],
        "ticker_download_category": data.get("ticker_download_category") or {"GC=F": "gold", "SI=F": "precious_metals"},
        "tf_rules": data.get("tf_rules") or dict(_DEFAULT_TF_RULES),
        "default_timeframes": data.get("default_timeframes") or list(_DEFAULT_DEFAULT_TIMEFRAMES),
        "result_file_exclude": exclude,
    }
    return _cached_config


def get_tf_rules() -> Dict[str, str]:
    """Timeframe label -> pandas resample rule (e.g. 1W -> 7D). From configuration.json tf_rules."""
    cfg = load_configuration()
    return dict(cfg.get("tf_rules") or _DEFAULT_TF_RULES)


def get_default_timeframes() -> List[str]:
    """Default timeframes for indicators report (e.g. [1W, 1M]). From configuration.json default_timeframes."""
    cfg = load_configuration()
    return list(cfg.get("default_timeframes") or _DEFAULT_DEFAULT_TIMEFRAMES)


def get_result_file_exclude() -> FrozenSet[str]:
    """Result JSON filenames to exclude when searching for symbol data. From configuration.json result_file_exclude."""
    cfg = load_configuration()
    raw = cfg.get("result_file_exclude")
    if isinstance(raw, (list, tuple)):
        return frozenset(raw)
    return _DEFAULT_RESULT_FILE_EXCLUDE


def get_symbols_config() -> Dict[str, List[str]]:
    """Category -> list of tickers. From configuration.json categories; trimmed to max_symbols_per_category (e.g. 3) when set to reduce data."""
    cfg = load_configuration()
    raw = cfg.get("categories") or {}
    if not isinstance(raw, dict):
        return {}
    out = {}
    max_n = cfg.get("max_symbols_per_category")
    for k, v in raw.items():
        symbols = list(v) if isinstance(v, (list, tuple)) else []
        if max_n is not None and max_n > 0 and len(symbols) > max_n:
            symbols = symbols[:max_n]
        out[k] = symbols
    return out


def update_categories(categories: Dict[str, List[str]]) -> None:
    """Update configuration.json 'categories' and clear cache. Use after adding/removing symbols (e.g. discover_hot_stocks)."""
    global _cached_config
    if not CONFIGURATION_PATH.exists():
        raise FileNotFoundError(f"{CONFIGURATION_PATH} not found")
    with open(CONFIGURATION_PATH) as f:
        data = json.load(f)
    data["categories"] = {k: list(v) for k, v in categories.items()}
    with open(CONFIGURATION_PATH, "w") as f:
        json.dump(data, f, indent=2)
    _cached_config = None


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
