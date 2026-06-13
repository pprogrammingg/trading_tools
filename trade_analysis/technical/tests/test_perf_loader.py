#!/usr/bin/env python3
"""Tests for perf_loader scalar coercion and phase ranking safety."""

import sys
import unittest
from pathlib import Path

import pandas as pd

TECH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TECH))
sys.path.insert(0, str(TECH / "visualization"))

from perf_loader import _sanitize_perf_entry, _spy_row  # noqa: E402
from yfinance_quiet import symbol_skips_perf_download, to_float  # noqa: E402


class TestToFloat(unittest.TestCase):
    def test_series_last(self):
        s = pd.Series([1.0, 2.5])
        self.assertEqual(to_float(s), 2.5)

    def test_none(self):
        self.assertIsNone(to_float(None))


class TestPerfLoader(unittest.TestCase):
    def test_matic_skipped(self):
        self.assertTrue(symbol_skips_perf_download("MATIC-USD"))

    def test_sanitize_entry(self):
        self.assertEqual(_sanitize_perf_entry({"1M_vs_spy": "1.5", "1W_vs_spy": None})["1M_vs_spy"], 1.5)

    def test_spy_row_skips_crypto(self):
        row = _spy_row("ETH-USD", 1.0, 0.5)
        self.assertIsNone(row["1M_vs_spy"])


if __name__ == "__main__":
    unittest.main()
