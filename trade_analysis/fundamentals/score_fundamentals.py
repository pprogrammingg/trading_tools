"""Fundamental thesis text and scores for the trade index table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

FUND_ROOT = Path(__file__).resolve().parent
NOTES_PATH = FUND_ROOT / "ticker_investment_notes.json"


def load_ticker_notes() -> Dict[str, str]:
    if not NOTES_PATH.is_file():
        return {}
    try:
        data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if not str(k).startswith("_") and isinstance(v, str)}
    except (json.JSONDecodeError, OSError):
        return {}


def fundamental_score_from_metrics(m: Dict[str, Any]) -> float:
    """0–10 scale from yfinance-style metrics dict."""
    from fundamental_halal_screen import composite_score

    raw = composite_score(m)
    return min(max(raw * 6.5, 0.0), 10.0)


def note_fallback_score(note: str) -> float:
    """Heuristic when yfinance unavailable."""
    if not note:
        return 5.0
    n = note.lower()
    s = 5.0
    for w in ("leader", "growth", "margin", "dominant", "compound", "tailwind"):
        if w in n:
            s += 0.4
    for w in ("risk", "pressure", "volatile", "binary", "decline"):
        if w in n:
            s -= 0.35
    return min(max(s, 2.0), 8.5)


def build_fundamentals_column(
    ticker: str,
    category: str,
    metrics: Optional[Dict[str, Any]],
    notes: Dict[str, str],
) -> Tuple[str, float]:
    """
    Return (display text for Fundamentals column, fundamental_score 0-10).
    """
    sym = ticker.upper()
    note = notes.get(sym) or notes.get(ticker)
    parts = []
    if note:
        parts.append(note.strip())
    if metrics and not metrics.get("excluded"):
        from fundamental_halal_screen import format_fundamental_blurb

        blurb = format_fundamental_blurb(metrics)
        if blurb not in (parts[0] if parts else ""):
            parts.append(blurb)
    if not parts:
        cat_label = category.replace("_", " ").title()
        parts.append(
            f"{cat_label} name—verify thesis via fundamentals/RESEARCH_CONTEXT.md and research_sources.json."
        )
    text = " ".join(parts)
    if len(text) > 280:
        text = text[:277] + "…"
    if metrics and not metrics.get("excluded"):
        f_score = fundamental_score_from_metrics(metrics)
    elif note:
        f_score = note_fallback_score(note)
    else:
        f_score = 4.5
    return text, round(f_score, 1)
