#!/usr/bin/env python3
"""Tests for trade_analysis/index.html unified table."""

import re
import unittest
from pathlib import Path

TRADE_ROOT = Path(__file__).resolve().parents[2]
INDEX = TRADE_ROOT / "index.html"


class TestTradeIndexPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INDEX.is_file():
            raise FileNotFoundError(f"Run build_trade_index.py first: {INDEX}")
        cls.html = INDEX.read_text(encoding="utf-8")

    def test_has_scrollable_table(self):
        self.assertIn("trade-index-table-wrap", self.html)
        self.assertIn("Fundamentals", self.html)

    def test_has_rsi_columns(self):
        for col in ("W RSI", "2W RSI", "M RSI", "2M RSI"):
            self.assertIn(col, self.html)

    def test_has_final_score_column(self):
        self.assertIn("Final", self.html)

    def test_has_industry_group_headers(self):
        self.assertIn("industry-header", self.html)
        self.assertIn("Precious Metals", self.html)


if __name__ == "__main__":
    unittest.main()
