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
        for col in ("W", "RSI", "Stoch", "2W", "M", "2M"):
            self.assertIn(col, self.html)

    def test_has_final_score_column(self):
        self.assertIn("Final", self.html)

    def test_has_industry_group_headers(self):
        self.assertIn("industry-header", self.html)
        self.assertIn("Precious Metals", self.html)

    def test_has_five_tier_verdict_labels(self):
        for label in (
            "Strong Accumulation",
            "Accumulation",
            "Neutral",
            "Sell",
            "Strong Sell",
        ):
            self.assertIn(label, self.html)

    def test_has_sector_etf_signal_rows(self):
        self.assertIn("sector-signal-row", self.html)
        self.assertIn("Sector call from benchmark ETFs", self.html)

    def test_sectors_sorted_by_verdict_rank(self):
        classes = re.findall(
            r"sector-signal-row sector-([\w-]+)",
            self.html,
        )
        self.assertGreater(len(classes), 0)
        rank = {
            "strong-accumulation": 0,
            "accumulation": 1,
            "neutral": 2,
            "sell": 3,
            "strong-sell": 4,
        }
        ranks = [rank.get(c, 2) for c in classes]
        self.assertEqual(ranks, sorted(ranks))


if __name__ == "__main__":
    unittest.main()
