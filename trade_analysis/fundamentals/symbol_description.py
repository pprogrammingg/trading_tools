"""Build symbol description (name, industry niche, what they do) for the trade index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

FUND_ROOT = Path(__file__).resolve().parent
PROFILES_CACHE_PATH = FUND_ROOT / "symbol_profiles_cache.json"

# Short blurbs when yfinance / notes are unavailable (futures, macro, crypto).
_STATIC_ABOUT: Dict[str, str] = {
    "GC=F": "COMEX gold futures; inflation hedge and real-rates sensitivity.",
    "SI=F": "COMEX silver futures; industrial and precious-metal demand.",
    "PA=F": "NYMEX palladium futures; auto catalyst and industrial metal.",
    "PL=F": "NYMEX platinum futures; jewelry and industrial demand.",
    "HG=F": "COMEX copper futures; electrification, grid, and construction demand.",
    "CL=F": "WTI crude oil futures; global energy benchmark.",
    "NG=F": "Natural gas futures; heating and power generation fuel.",
    "HO=F": "Heating oil futures; distillate fuel benchmark.",
    "RB=F": "RBOB gasoline futures; US retail fuel benchmark.",
    "ZC=F": "Corn futures; feed and ethanol demand.",
    "ZS=F": "Soybean futures; protein and oilseed crop.",
    "ZW=F": "Wheat futures; global staple grain.",
    "KC=F": "Coffee futures; soft commodity benchmark.",
    "CT=F": "Cotton futures; textile raw material.",
    "SB=F": "Sugar futures; soft commodity benchmark.",
    "ZN=F": "Zinc futures; galvanizing and industrial metal.",
    "ALI=F": "Aluminum futures; packaging and transport metal.",
    "^GSPC": "S&P 500 index; broad US large-cap benchmark.",
    "^VIX": "CBOE volatility index; equity fear gauge.",
    "DX-Y.NYB": "US Dollar Index; FX vs major trading partners.",
}


def load_profiles_cache() -> Dict[str, Dict[str, str]]:
    if not PROFILES_CACHE_PATH.is_file():
        return {}
    try:
        data = json.loads(PROFILES_CACHE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        out: Dict[str, Dict[str, str]] = {}
        for k, v in data.items():
            if str(k).startswith("_") or not isinstance(v, dict):
                continue
            out[str(k).upper()] = {str(f): str(v[f]) for f in v if v[f]}
        return out
    except (json.JSONDecodeError, OSError):
        return {}


def save_profiles_cache(cache: Dict[str, Dict[str, str]]) -> None:
    merged = load_profiles_cache()
    merged.update(cache)
    payload = {"_comment": "Auto-updated from --live-fundamentals; name/sector/industry/summary per ticker.", **merged}
    PROFILES_CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def profile_from_metrics(metrics: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, src in (
        ("long_name", "long_name"),
        ("sector", "sector"),
        ("industry", "industry"),
        ("summary", "business_summary"),
    ):
        val = metrics.get(src)
        if val:
            out[key] = str(val).strip()
    return out


def _lookup_note(notes: Dict[str, str], *keys: str) -> str:
    for k in keys:
        if not k:
            continue
        note = notes.get(k.upper()) or notes.get(k)
        if note:
            return note.strip()
    return ""


def build_symbol_description(
    yahoo_symbol: str,
    display_symbol: str,
    category: str,
    *,
    fund_metrics: Optional[Dict[str, Any]] = None,
    notes: Optional[Dict[str, str]] = None,
    profiles_cache: Optional[Dict[str, Dict[str, str]]] = None,
    category_label: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Return (name, meta_line, about_line) for the Description column.

    meta_line: portfolio niche · yfinance sector · industry
    about_line: investment note, business summary, or static blurb
    """
    from config_loader import get_display_name_category, get_display_name_symbol

    notes = notes or {}
    cache = profiles_cache or {}
    sym_u = yahoo_symbol.upper()
    cached = cache.get(sym_u) or {}

    cfg_name = get_display_name_symbol(yahoo_symbol)
    long_name = ""
    if fund_metrics:
        long_name = str(fund_metrics.get("long_name") or "").strip()
    if not long_name:
        long_name = cached.get("long_name", "")

    if cfg_name and cfg_name != yahoo_symbol:
        name = cfg_name
    elif long_name:
        name = long_name
    else:
        name = display_symbol

    niche = category_label or get_display_name_category(category)
    sector = (fund_metrics or {}).get("sector") or cached.get("sector") or ""
    industry = (fund_metrics or {}).get("industry") or cached.get("industry") or ""
    meta_parts = [p for p in (niche, sector, industry) if p]
    meta = " · ".join(meta_parts) if meta_parts else niche

    about = _lookup_note(notes, sym_u, display_symbol, yahoo_symbol)
    if not about and fund_metrics:
        about = str(fund_metrics.get("business_summary") or "").strip()
    if not about:
        about = cached.get("summary", "")
    if not about:
        about = _STATIC_ABOUT.get(sym_u) or _STATIC_ABOUT.get(yahoo_symbol) or ""
    if not about and yahoo_symbol.endswith("-USD"):
        about = "Cryptocurrency; spot USD pair."
    if not about and "=" in yahoo_symbol:
        about = "Exchange-traded futures contract."
    if not about:
        about = f"{niche} holding—add a note in ticker_investment_notes.json or run with --live-fundamentals."

    return name, meta, about
