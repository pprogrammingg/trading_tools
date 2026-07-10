#!/usr/bin/env python3
"""Tests for fundamentals column formatting."""

import sys
import unittest
from pathlib import Path

FUND = Path(__file__).resolve().parents[2] / "fundamentals"
if str(FUND) not in sys.path:
    sys.path.insert(0, str(FUND))

from fundamental_halal_screen import format_fundamental_blurb, fundamental_strengths_weaknesses  # noqa: E402
from score_fundamentals import build_fundamentals_column  # noqa: E402


class TestFundamentalsColumn(unittest.TestCase):
    def test_live_metrics_strong_weak(self):
        m = {
            "ebitda_margin_pct": 56.0,
            "revenue_growth_pct": 48.0,
            "earnings_growth_pct": 85.0,
            "peg_ratio": 0.4,
            "excluded": False,
        }
        strong, weak = fundamental_strengths_weaknesses(m)
        self.assertTrue(any("EBITDA" in s for s in strong))
        text = format_fundamental_blurb(m, as_of_date="2026-07-09")
        self.assertIn("Last updated 2026-07-09", text)
        self.assertIn("Strong:", text)
        self.assertIn("Weak:", text)

    def test_missing_live_data_prompt(self):
        text, score = build_fundamentals_column(
            "XYZ",
            "tech_stocks",
            None,
            {},
            as_of_date="2026-07-09",
        )
        self.assertIn("Last updated 2026-07-09", text)
        self.assertIn("--live-fundamentals", text)
        self.assertEqual(score, 4.5)

    def test_manual_note_used(self):
        text, _ = build_fundamentals_column(
            "NVDA",
            "ai_semiconductors",
            None,
            {"NVDA": "AI capex cycle leader; high volatility, strong long-term theme."},
            as_of_date="2026-07-09",
        )
        self.assertIn("AI capex", text)
        self.assertIn("volatility", text.lower())


if __name__ == "__main__":
    unittest.main()
