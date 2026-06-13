#!/usr/bin/env python3
"""Tests for exclusion_policy blocklist helpers."""

import sys
import unittest
from pathlib import Path

FUND = Path(__file__).resolve().parents[2] / "fundamentals"
TECH = Path(__file__).resolve().parents[1]
TRADE = Path(__file__).resolve().parents[2]
for p in (TRADE, TECH, FUND):
    sys.path.insert(0, str(p))

from exclusion_policy import (  # noqa: E402
    EXCLUDED_TICKERS,
    FUNDAMENTAL_SCAN_SKIP_CATEGORIES,
    base_symbol,
    is_blocklisted,
    load_ticker_blocklist,
)


class TestExclusionPolicy(unittest.TestCase):
    def test_base_symbol(self):
        self.assertEqual(base_symbol("MATIC-USD"), "MATIC")
        self.assertEqual(base_symbol("IVN.TO"), "IVN")

    def test_is_blocklisted(self):
        block = load_ticker_blocklist()
        self.assertTrue(is_blocklisted("PFE", block))
        self.assertTrue(is_blocklisted("LMT", block))
        self.assertFalse(is_blocklisted("NVDA", block))

    def test_static_tickers_in_blocklist(self):
        block = load_ticker_blocklist()
        for t in ("JNJ", "PLTR"):
            self.assertIn(t, block)
            self.assertIn(t, EXCLUDED_TICKERS)

    def test_fundamental_skip_superset(self):
        self.assertIn("energy_commodities", FUNDAMENTAL_SCAN_SKIP_CATEGORIES)
        self.assertIn("space_defense", FUNDAMENTAL_SCAN_SKIP_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
