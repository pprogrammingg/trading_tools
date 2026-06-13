"""CLI / pipeline options for visualize_scores and index build."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VizBuildOptions:
    """Staged build: turn off work you do not need in CI or local iteration."""

    no_network: bool = False
    """If True, do not call yfinance for perf, ESG, or market-cap refresh; use cache on disk only."""
    skip_trending: bool = False
    """Skip scripts/build_trending_industries (network + heavy)."""
    write_index: bool = True
    """If False, do not write index.html or run index-stage static pages (halal, wealth, CME, etc.)."""
    only_index: bool = False
    """If True, only run index and landing assets; skip per-category score HTML (requires existing result files for aggregate pages)."""
    category: Optional[str] = None
    """If set, only (re)build that category’s *_scores.html; index still uses all categories in result_scores/ unless write_index is False."""
    max_workers: int = 4
    """Thread pool size for per-category HTML generation."""
