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
    INDEX_SECTION_ELLIOTT_HEADER,
    INDEX_SECTION_CATEGORY_HEADER,
    INDEX_TOP_SCORER_COLUMNS,
    INDEX_ELLIOTT_COLUMNS,
    PAGE_TOP_SCORES_BY_CATEGORY,
    PAGE_ELLIOTT_WAVE_COUNT,
    PAGE_GOLD_PRESENTATION,
    PAGE_WEALTH_PHASE,
    PAGE_CME_SUNDAY_OPEN,
)

# Paths relative to technical_analysis/
def _base_dir():
    return Path(__file__).resolve().parent.parent


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


# ---- Index page tests ----
class TestIndexPage(unittest.TestCase):
    """Index page: link bar (incl. wealth phase link), category grid."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html("index.html")

    def test_has_link_to_gold_presentation(self):
        self.assertIn(f'href="{PAGE_GOLD_PRESENTATION}"', self.html)

    def test_has_link_to_top_scores_by_category(self):
        self.assertIn(f'href="{PAGE_TOP_SCORES_BY_CATEGORY}"', self.html)

    def test_has_link_to_elliott_wave_count(self):
        self.assertIn(f'href="{PAGE_ELLIOTT_WAVE_COUNT}"', self.html)

    def test_has_link_to_wealth_phase(self):
        self.assertIn(f'href="{PAGE_WEALTH_PHASE}"', self.html)

    def test_has_link_to_cme_sunday_open(self):
        self.assertIn(f'href="{PAGE_CME_SUNDAY_OPEN}"', self.html)

    def test_industry_category_header_present(self):
        self.assertIn(INDEX_SECTION_CATEGORY_HEADER, self.html)

    def test_category_grid_present(self):
        self.assertIn('class="category-grid"', self.html)


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


# ---- Elliott Wave count (standalone page) ----
class TestElliottWaveCountPage(unittest.TestCase):
    """Elliott Wave count standalone page: table headers and wave data format."""

    @classmethod
    def setUpClass(cls):
        cls.html = _load_html(PAGE_ELLIOTT_WAVE_COUNT)

    def test_page_has_header(self):
        self.assertIn(INDEX_SECTION_ELLIOTT_HEADER, self.html)

    def test_table_headers(self):
        headers = _table_header_row_in_fragment(self.html)
        self.assertGreater(len(headers), 0, "Table has no header row")
        core = ["Industry", "Symbol", "MktCap", "1M Gold", "2W Gold", "1W Gold", "Monthly Wave Count", "Weekly Wave Count", "2D Wave Count", "Alternative", "ESG"]
        for expected in core:
            self.assertIn(expected, headers, f"Expected column '{expected}'; got {headers}")
        self.assertGreaterEqual(len(headers), len(core), "Table should have at least core columns")

    def test_table_has_data_rows(self):
        n = _count_data_rows(self.html)
        self.assertGreater(n, 0, "Table should have at least one data row")

    def test_data_format_industry_and_symbol(self):
        self.assertIn("<td>", self.html)
        self.assertIn("<strong>", self.html)

    def test_wave_cells_visible(self):
        # Wave columns: — or wave position text or primary wave format (e.g. 1: 88.9k→95.0k ★)
        has_wave_or_na = (
            "—" in self.html
            or "Wave " in self.html
            or "Primary" in self.html
            or "★" in self.html
            or re.search(r">\d+\.?\d*[kM]?→", self.html)
        )
        self.assertTrue(has_wave_or_na, "Wave count columns should show — or wave data (position/primary/★)")

    def test_wave_cell_class_present(self):
        self.assertIn("wave-cell", self.html, "Wave cells should have wave-cell class for styling")

    def test_wave_detail_expandable(self):
        # When wave_count exists, cells show Primary/Secondary as <details>; otherwise fallback (— or wave position)
        has_expandable = "<details" in self.html and "Primary" in self.html
        has_fallback = "—" in self.html or "Wave " in self.html
        self.assertTrue(has_expandable or has_fallback, "Wave count should have expandable detail or fallback")

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
