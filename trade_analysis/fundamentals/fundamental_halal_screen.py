"""
Halal-aware equity screen for fundamental hot-pick generation.

Uses yfinance `info` sector/industry strings plus keyword blocks (defense, gambling,
alcohol, etc.). This is a heuristic screen—not Islamic finance certification.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TRADE_ROOT = Path(__file__).resolve().parents[1]
if str(_TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRADE_ROOT))
from trade_paths import setup_import_paths  # noqa: E402

setup_import_paths(technical=True, fundamentals=True)

from exclusion_policy import (
    DRUG_INDUSTRY_KEYWORDS,
    EXCLUDED_FINANCIAL_INDUSTRY_KEYWORDS,
    EXCLUDED_INDUSTRY_KEYWORDS,
    HEALTH_TECH_INDUSTRY_ALLOW,
)

# Substrings matched against sector, industry, and long business name (case-insensitive).
_EXCLUDED_INDUSTRY_PATTERNS: Tuple[str, ...] = tuple(sorted(EXCLUDED_INDUSTRY_KEYWORDS))
_DRUG_INDUSTRY_PATTERNS: Tuple[str, ...] = tuple(sorted(DRUG_INDUSTRY_KEYWORDS))
_HEALTH_TECH_ALLOW: Tuple[str, ...] = tuple(sorted(HEALTH_TECH_INDUSTRY_ALLOW))

# Stronger financial exclusions (interest-heavy business models). Not "credit" alone (hits payment networks).
_EXCLUDED_FINANCIAL_INDUSTRIES: Tuple[str, ...] = tuple(sorted(EXCLUDED_FINANCIAL_INDUSTRY_KEYWORDS))


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def industry_excluded(sector: str, industry: str, long_name: str) -> Tuple[bool, str]:
    """
    Return (True, reason) if the name/industry should be excluded from the halal-aware list.
    """
    blob = f"{_norm(sector)} {_norm(industry)} {_norm(long_name)}"
    ind_blob = f"{_norm(industry)} {_norm(long_name)}"
    for pat in _DRUG_INDUSTRY_PATTERNS:
        if pat in blob:
            return True, f"drug:{pat}"
    for allow in _HEALTH_TECH_ALLOW:
        if allow in ind_blob or allow in _norm(sector):
            return False, ""
    for pat in _EXCLUDED_INDUSTRY_PATTERNS:
        if pat in blob:
            return True, f"keyword:{pat}"
    fin_blob = f"{_norm(industry)} {_norm(long_name)}"
    for pat in _EXCLUDED_FINANCIAL_INDUSTRIES:
        if pat not in fin_blob:
            continue
        # Allow fee-based payments / exchanges / asset-light fintech.
        if any(x in fin_blob for x in ("payment", "capital markets", "exchange", "financial data")):
            continue
        if "bank" in fin_blob or "insurance" in fin_blob or "mortgage" in fin_blob or "thrifts" in fin_blob:
            return True, f"financial:{pat}"
    return False, ""


def fetch_screen_info(ticker: str) -> Dict[str, Any]:
    """
    Pull yfinance info for screening. Returns dict with pass/fail, metrics, and raw labels.
    """
    import yfinance as yf

    from yfinance_quiet import quiet_yfinance

    with quiet_yfinance():
        t = yf.Ticker(ticker)
        info = t.info or {}
    sector = info.get("sector") or ""
    ind = info.get("industry") or ""
    long_name = info.get("longName") or info.get("shortName") or ""
    bad, reason = industry_excluded(sector, ind, long_name)

    def _pct(x: Any) -> Optional[float]:
        if x is None:
            return None
        try:
            v = float(x)
            # yfinance margins often 0.22 for 22%; growth fields may be 0.18 or 18.
            if abs(v) <= 1.0:
                return v * 100.0
            return v
        except (TypeError, ValueError):
            return None

    ebitda_m = _pct(info.get("ebitdaMargins"))
    rev_g = _pct(info.get("revenueGrowth"))
    earn_g = _pct(info.get("earningsGrowth"))
    peg_raw = info.get("pegRatio")
    peg_f: Optional[float]
    try:
        pf = float(peg_raw)
        peg_f = pf if pf == pf and 0 < pf < 100 else None  # NaN / insane
    except (TypeError, ValueError):
        peg_f = None
    price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
    summary_raw = info.get("longBusinessSummary") or info.get("description") or ""
    summary = " ".join(str(summary_raw).split())
    if len(summary) > 220:
        summary = summary[:217].rstrip() + "…"

    return {
        "ticker": ticker.upper(),
        "excluded": bad,
        "exclude_reason": reason,
        "sector": sector,
        "industry": ind,
        "long_name": long_name,
        "business_summary": summary,
        "ebitda_margin_pct": ebitda_m,
        "revenue_growth_pct": rev_g,
        "earnings_growth_pct": earn_g,
        "peg_ratio": peg_f,
        "price": float(price) if price is not None and price == price else None,
        "raw_info_keys_ok": bool(info),
    }


def composite_score(metrics: Dict[str, Any]) -> float:
    """Higher is better for ranking pass names."""
    em = metrics.get("ebitda_margin_pct")
    rg = metrics.get("revenue_growth_pct")
    eg = metrics.get("earnings_growth_pct")
    s = 0.0
    if em is not None and em > 0:
        s += min(em / 40.0, 1.0) * 0.45
    if rg is not None:
        s += max(min(rg / 25.0, 1.5), 0.0) * 0.35
    if eg is not None:
        s += max(min(eg / 25.0, 1.5), 0.0) * 0.20
    return s


def format_fundamental_blurb(m: Dict[str, Any]) -> str:
    """One-line summary for the hot-pick table."""
    parts: List[str] = []
    em = m.get("ebitda_margin_pct")
    rg = m.get("revenue_growth_pct")
    eg = m.get("earnings_growth_pct")
    if em is not None:
        parts.append(f"EBITDA margin ~{em:.0f}%")
    if rg is not None:
        parts.append(f"rev growth ~{rg:.0f}% YoY (yfinance)")
    if eg is not None:
        parts.append(f"earnings growth ~{eg:.0f}% YoY")
    peg = m.get("peg_ratio")
    if peg is not None and 0 < peg < 5:
        parts.append(f"PEG ~{peg:.1f}")
    if not parts:
        parts.append("Margins/growth: verify in filings—yfinance incomplete.")
    return "; ".join(parts) + " Halal screen: passed sector/industry keywords."


_RE_TICKER_OK = re.compile(r"^[A-Z]{1,6}$")
_RE_EXCHANGE_TICKER_OK = re.compile(r"^[A-Z0-9]{1,6}\.[A-Z]{1,4}$")


def normalize_equity_symbol(sym: str) -> Optional[str]:
    s = sym.upper().strip()
    if s.endswith("-USD") or "=" in s or s.startswith("^"):
        return None
    if _RE_TICKER_OK.match(s) or _RE_EXCHANGE_TICKER_OK.match(s):
        return s
    return None
