"""Portfolio position metadata (held / accounts) for the trade index."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


def _normalize_acc(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
        return [p for p in parts if p]
    if isinstance(raw, (list, tuple)):
        out: List[str] = []
        for x in raw:
            s = str(x).strip()
            if s:
                out.append(s)
        return out
    return []


def get_portfolio_map() -> Dict[str, Dict[str, Any]]:
    """Yahoo symbol -> {held: bool, acc: [str, ...]}."""
    try:
        from config_loader import get_ticker, load_configuration

        cfg = load_configuration()
        raw = cfg.get("portfolio") or {}
        if not isinstance(raw, dict):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for key, meta in raw.items():
            if str(key).startswith("_") or not isinstance(meta, dict):
                continue
            yahoo = get_ticker(str(key)) or get_ticker(str(key).upper()) or str(key).upper()
            yahoo_u = str(yahoo).upper()
            held = bool(meta.get("held"))
            acc = _normalize_acc(meta.get("acc"))
            # Prefer held=true if duplicate keys resolve to same yahoo
            prev = out.get(yahoo_u)
            if prev and prev.get("held") and not held:
                continue
            out[yahoo_u] = {"held": held, "acc": acc}
        return out
    except Exception:
        return {}


def position_for_symbol(yahoo_symbol: str, portfolio: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    m = portfolio if portfolio is not None else get_portfolio_map()
    hit = m.get(yahoo_symbol.upper()) or {}
    return {
        "held": bool(hit.get("held")),
        "acc": list(hit.get("acc") or []),
    }


def format_acc(acc: Sequence[str]) -> str:
    return ", ".join(acc) if acc else "—"


def sector_phase_rank(verdict: str) -> int:
    """0 = accumulation, 1 = sell / take-profit, 2 = neutral (for non-held sector ordering)."""
    v = str(verdict or "Neutral").strip()
    if v in ("Strong Accumulation", "Accumulation"):
        return 0
    if v in ("Sell", "Strong Sell (Get Out)"):
        return 1
    return 2
