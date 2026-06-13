#!/usr/bin/env python3
"""
UI tests for index and standalone pages: major sections, table headers/rows, data format.
Uses visualization_common for constants (single source of truth with visuals).
"""

import re
import unittest
from pathlib import Path

from visualization_common import (
    INDEX_SECTION_TOP_SCORERS_HEADER,
    INDEX_SECTION_CATEGORY_HEADER,
    PAGE_TOP_SCORES_BY_CATEGORY,
    PAGE_GOLD_PRESENTATION,
    PAGE_WEALTH_PHASE,
    PAGE_CME_SUNDAY_OPEN,
    PAGE_HOT_PICK_PLAN,
)

# Paths relative to trade_analysis/technical/
def _base_dir():
    return Path(__file__).resolve().parent.parent


def _trade_index_path() -> Path:
    return _base_dir().parent / "index.html"


def _page_path(filename: str) -> Path:
    return _base_dir() / "visualizations_output" / filename


def _load_html(filename: str) -> str:
    path = _page_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"{filename} not found at {path}")
    return path.read_text(encoding="utf-8")


def _extract_th_text(html: str) -> list:
    """Extract text content of all <th>...</th> in order."""
    return re.findall(r"<th[^>]*>([^<]*)</th>", html, re.IGNORECASE)


def _table_header_row_in_fragment(fragment: str) -> list:
    """First row of <th> in fragment (first table's thead)."""
    thead = re.search(r"<thead[^>]*>(.*?)</thead>", fragment, re.DOTALL | re.IGNORECASE)
    if not thead:
        return []
    return _extract_th_text(thead.group(1))


def _count_data_rows(fragment: str) -> int:
    """Count <tr> that contain <td> in fragment (tbody)."""
    tbody = re.search(r"<tbody[^>]*>(.*?)</tbody>", fragment, re.DOTALL | re.IGNORECASE)
    if not tbody:
        return 0
    return len(re.findall(r"<tr[^>]*>.*?<td", tbody.group(1), re.DOTALL | re.IGNORECASE))


# ---- Trade index (primary dashboard at trade_analysis/index.html) ----
class TestIndexPage(unittest.TestCase):
    """Primary trade index: unified ticker table."""

    @classmethod
    def setUpClass(cls):
        path = _trade_index_path()
        if not path.exists():
            raise FileNotFoundError(f"Run build_trade_index.py: {path}")
        cls.html = path.read_text(encoding="utf-8")

    def test_has_fundamentals_column(self):
        self.assertIn("Fundamentals", self.html)

    def test_has_rsi_and_final_score(self):
        self.assertIn("W RSI", self.html)
        self.assertIn("Final", self.html)

    def test_links_to_technical_views(self):
        self.assertIn("technical/visualizations_output/hot_pick_plan.html", self.html)

    def test_has_ticker_rows(self):
        self.assertIn("<tbody>", self.html)
        self.assertIn("NVDA", self.html)  # or any scored symbol from result_scores


# ---- Top scores by category (standalone page) ----
class TestTopScoresByCategoryPage(unittest.TestCase):
    """Top scores by category standalone page: table headers and data format."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html(PAGE_TOP_SCORES_BY_CATEGORY)

    def test_page_has_header(self):
        self.assertIn(INDEX_SECTION_TOP_SCORERS_HEADER, self.html)

    def test_table_headers(self):
        headers = _table_header_row_in_fragment(self.html)
        self.assertGreater(len(headers), 0, "Table has no header row")
        core = ["Category", "Symbol", "MktCap", "1M Gold", "2W Gold", "1W Gold"]
        for expected in core:
            self.assertIn(expected, headers, f"Expected column '{expected}'; got {headers}")
        self.assertGreaterEqual(len(headers), len(core), "Table should have at least core columns")

    def test_table_has_data_rows(self):
        n = _count_data_rows(self.html)
        self.assertGreater(n, 0, "Table should have at least one data row")

    def test_data_format_symbol_strong(self):
        self.assertIn("<strong>", self.html)
        self.assertIn("</strong>", self.html)

    def test_data_format_score_or_na(self):
        has_score = bool(re.search(r">\s*-?\d+\.?\d*\s*<", self.html)) or "—" in self.html
        self.assertTrue(has_score, "Table should contain numeric scores or —")

    def test_back_link_to_index(self):
        self.assertIn('href="index.html"', self.html)


# ---- Wealth phase page ----
class TestWealthPhasePage(unittest.TestCase):
    """Wealth phase page: phases, performance-based hotness, Monthly/Weekly toggle."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html(PAGE_WEALTH_PHASE)

    def test_has_phase_cards(self):
        self.assertIn("phase-card", self.html)

    def test_has_temperature_or_order(self):
        self.assertIn("phase-order", self.html)
        self.assertIn("phase-temp", self.html)

    def test_has_toggle_monthly_weekly(self):
        self.assertIn("toggle-monthly", self.html)
        self.assertIn("toggle-weekly", self.html)

    def test_has_flow_bar(self):
        self.assertIn("flow-bar", self.html)

    def test_back_link_to_index(self):
        self.assertIn('href="index.html"', self.html)


# ---- Hot pick plan page ----
class TestHotPickPlanPage(unittest.TestCase):
    """Horizon hot-pick tables: Ticker, price, niche, fundies, technicals."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html(PAGE_HOT_PICK_PLAN)

    def test_table_headers(self):
        headers = _table_header_row_in_fragment(self.html)
        for expected in ["Ticker", "USD Price", "Fundamental", "Technical"]:
            self.assertTrue(
                any(expected in h for h in headers),
                f"Expected a column containing '{expected}'; got {headers}",
            )

    def test_back_link_to_index(self):
        self.assertIn('href="index.html"', self.html)

    def test_has_horizon_section_ids(self):
        self.assertIn('id="fundamental-1-6"', self.html)
        self.assertIn('id="horizon-3"', self.html)
        self.assertIn("3-Month hot picks", self.html)
        self.assertIn('id="horizon-24"', self.html)

    def test_links_modular_css_js(self):
        self.assertIn("hot_pick_plan.css", self.html)
        self.assertIn("hot_pick_plan.js", self.html)


# ---- CME Sunday Open page ----
class TestCmeSundayOpenPage(unittest.TestCase):
    """CME Sunday 6pm ET Open page: table, updated after 6 PM EST on Sunday."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html(PAGE_CME_SUNDAY_OPEN)

    def test_has_cme_table(self):
        self.assertIn("cme-table", self.html)
        self.assertIn("Direction", self.html)
        self.assertIn("Move %", self.html)

    def test_has_updated_note(self):
        self.assertIn("6 PM EST on Sunday", self.html)

    def test_back_link_to_index(self):
        self.assertIn('href="index.html"', self.html)


if __name__ == "__main__":
    unittest.main()
