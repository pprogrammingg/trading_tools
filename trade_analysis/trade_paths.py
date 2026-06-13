"""Canonical paths and import bootstrap for trade_analysis scripts."""

from __future__ import annotations

import sys
from pathlib import Path

TRADE_ROOT = Path(__file__).resolve().parent
TECH_ROOT = TRADE_ROOT / "technical"
FUND_ROOT = TRADE_ROOT / "fundamentals"
RESULT_SCORES_DIR = TECH_ROOT / "result_scores"
VIZ_OUTPUT_DIR = TECH_ROOT / "visualizations_output"
INDEX_HTML = TRADE_ROOT / "index.html"
INDEX_CSS = TRADE_ROOT / "index.css"


def setup_import_paths(*, technical: bool = True, fundamentals: bool = True) -> None:
    """Ensure technical/ and fundamentals/ are importable (idempotent)."""
    for root, enabled in ((TECH_ROOT, technical), (FUND_ROOT, fundamentals)):
        if enabled:
            s = str(root)
            if s not in sys.path:
                sys.path.insert(0, s)
