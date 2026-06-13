"""Shared HTML formatting helpers."""

from __future__ import annotations

import html
from typing import Optional


def esc_html(text: str) -> str:
    return html.escape(text, quote=True)


def fmt_num(value: Optional[float], decimals: int = 1, missing: str = "—") -> str:
    if value is None:
        return missing
    return f"{value:.{decimals}f}"
