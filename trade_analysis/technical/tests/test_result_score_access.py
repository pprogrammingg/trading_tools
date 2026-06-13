#!/usr/bin/env python3
"""Tests for shared result JSON access helpers."""

import sys
import unittest
from pathlib import Path

TECH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TECH))

from result_score_access import avg_ta_score, get_ta_block, tech_score_to_display  # noqa: E402


class TestResultScoreAccess(unittest.TestCase):
    def test_get_ta_block_prefers_ta_library(self):
        data = {"1W": {"yfinance": {"usd": {"ta_library": {"score": 5.0}}}}}
        block = get_ta_block(data, "1W")
        self.assertEqual(block["score"], 5.0)

    def test_avg_and_display(self):
        data = {
            "1W": {"yfinance": {"usd": {"ta_library": {"score": 4.0}}}},
            "1M": {"yfinance": {"usd": {"ta_library": {"score": 6.0}}}},
        }
        self.assertAlmostEqual(avg_ta_score(data, ("1W", "1M")), 5.0)
        self.assertAlmostEqual(tech_score_to_display(5.0), 3.9, places=1)


if __name__ == "__main__":
    unittest.main()
