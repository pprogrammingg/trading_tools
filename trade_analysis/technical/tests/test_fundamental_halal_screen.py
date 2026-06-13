#!/usr/bin/env python3
"""Unit tests for halal-aware industry keyword screen."""

import sys
import unittest
from pathlib import Path

FUND = Path(__file__).resolve().parents[2] / "fundamentals"
if str(FUND) not in sys.path:
    sys.path.insert(0, str(FUND))

from fundamental_halal_screen import industry_excluded, normalize_equity_symbol  # noqa: E402


class TestIndustryExcluded(unittest.TestCase):
    def test_defense_aerospace(self):
        bad, reason = industry_excluded("Industrials", "Aerospace & Defense", "Example Corp")
        self.assertTrue(bad)
        self.assertIn("defense", reason)

    def test_pharma_biotech(self):
        bad, reason = industry_excluded("Healthcare", "Biotechnology", "Example Pharma Inc")
        self.assertTrue(bad)
        self.assertIn("drug:", reason)

    def test_health_software_allowed(self):
        bad, reason = industry_excluded(
            "Healthcare",
            "Health Information Services",
            "Veeva Systems Inc",
        )
        self.assertFalse(bad, msg=reason)

    def test_surgical_robotics_allowed(self):
        bad, reason = industry_excluded(
            "Healthcare",
            "Medical Instruments & Supplies",
            "Intuitive Surgical Inc",
        )
        self.assertFalse(bad, msg=reason)

    def test_drug_manufacturer_excluded(self):
        bad, reason = industry_excluded(
            "Healthcare",
            "Drug Manufacturers—General",
            "Pfizer Inc",
        )
        self.assertTrue(bad)
        self.assertIn("drug:", reason)

    def test_gambling(self):
        bad, _ = industry_excluded("Consumer Cyclical", "Casinos", "Resorts Inc")
        self.assertTrue(bad)

    def test_visa_like_credit_services_allowed(self):
        allowed, _ = industry_excluded(
            "Financial Services",
            "Credit Services",
            "Visa Inc",
        )
        self.assertFalse(allowed)

    def test_normalize_skips_crypto_and_futures(self):
        self.assertIsNone(normalize_equity_symbol("BTC-USD"))
        self.assertIsNone(normalize_equity_symbol("GC=F"))
        self.assertEqual(normalize_equity_symbol("NVDA"), "NVDA")


if __name__ == "__main__":
    unittest.main()
