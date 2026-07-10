"""Fundamental thesis text and scores for the trade index table."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _split_note_strengths_weaknesses(note: str) -> Tuple[List[str], List[str]]:
    """Best-effort split of a manual note into strong vs weak clauses."""
    strong: List[str] = []
    weak: List[str] = []
    parts = [p.strip() for p in re.split(r"[;.]", note) if p.strip()]
    weak_kw = (
        "risk",
        "pressure",
        "volatile",
        "binary",
        "decline",
        "competition",
        "cyclical",
        "pre-production",
        "high beta",
    )
    for part in parts:
        low = part.lower()
        if any(k in low for k in weak_kw):
            weak.append(part)
        else:
            strong.append(part)
    return strong, weak


def _format_fundamentals_line(
    *,
    as_of_date: str,
    strong: List[str],
    weak: List[str],
) -> str:
    s_txt = "; ".join(strong) if strong else "—"
    w_txt = "; ".join(weak) if weak else "—"
    return f"Last updated {as_of_date}: Strong: {s_txt}. Weak: {w_txt}."


def build_fundamentals_column(
    ticker: str,
    category: str,
    metrics: Optional[Dict[str, Any]],
    notes: Dict[str, str],
    *,
    as_of_date: str,
) -> Tuple[str, float]:
    """
    Return (display text for Fundamentals column, fundamental_score 0-10).
    """
    sym = ticker.upper()
    note = notes.get(sym) or notes.get(ticker)

    if metrics and not metrics.get("excluded"):
        from fundamental_halal_screen import format_fundamental_blurb

        text = format_fundamental_blurb(metrics, as_of_date=as_of_date)
        if note:
            note_strong, note_weak = _split_note_strengths_weaknesses(note)
            if note_strong:
                text = text.replace("Strong: —", f"Strong: {'; '.join(note_strong)}", 1)
            elif note:
                text = text.replace("Strong: —", f"Strong: {note.strip()}", 1)
            if note_weak:
                base_weak = text.split("Weak: ", 1)[-1].rstrip(".")
                text = text.replace(f"Weak: {base_weak}.", f"Weak: {base_weak}; {'; '.join(note_weak)}.", 1)
        f_score = fundamental_score_from_metrics(metrics)
        return _truncate(text), round(f_score, 1)

    if note:
        strong, weak = _split_note_strengths_weaknesses(note)
        if not strong:
            strong = [note.strip()]
        text = _format_fundamentals_line(as_of_date=as_of_date, strong=strong, weak=weak)
        return _truncate(text), round(note_fallback_score(note), 1)

    text = _format_fundamentals_line(
        as_of_date=as_of_date,
        strong=[],
        weak=["no live fundamentals — run build_trade_index.py --live-fundamentals"],
    )
    return _truncate(text), 4.5


def _truncate(text: str, limit: int = 320) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
