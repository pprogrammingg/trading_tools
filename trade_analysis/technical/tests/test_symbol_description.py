#!/usr/bin/env python3
"""Tests for symbol description column builder."""

import sys
import unittest
from pathlib import Path

TRADE_ROOT = Path(__file__).resolve().parents[1]
if str(TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(TRADE_ROOT))
from trade_paths import setup_import_paths

setup_import_paths()

from symbol_description import build_symbol_description  # noqa: E402


class TestSymbolDescription(unittest.TestCase):
    def test_equity_with_metrics_and_note(self):
        name, meta, about = build_symbol_description(
            "AAPL",
            "AAPL",
            "faang_hot_stocks",
            fund_metrics={
                "long_name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "business_summary": "Designs smartphones and services.",
            },
            notes={"AAPL": "Quality compounder; services growth."},
            category_label="FAANG / Hot Stocks",
        )
        self.assertIn("Apple", name)
        self.assertIn("FAANG", meta)
        self.assertIn("Technology", meta)
        self.assertIn("Consumer Electronics", meta)
        self.assertIn("Quality compounder", about)

    def test_futures_static_blurb(self):
        name, meta, about = build_symbol_description(
            "HG=F",
            "HG=F",
            "industrial_metals",
            category_label="Industrial Metals",
        )
        self.assertEqual(name, "HG=F")
        self.assertIn("Industrial Metals", meta)
        self.assertIn("copper", about.lower())

    def test_crypto_display_name(self):
        name, meta, about = build_symbol_description(
            "BTC-USD",
            "BTC-USD",
            "cryptocurrencies",
            notes={"BTC-USD": "Digital store of value."},
            category_label="Cryptocurrencies",
        )
        self.assertIn("Bitcoin", name)
        self.assertIn("Cryptocurrencies", meta)
        self.assertIn("store of value", about)

    def test_no_cross_ticker_note_leak(self):
        """Symbols without notes must not inherit another ticker's note (e.g. NFG)."""
        notes = {"NFG": "Gold explorer (Quebec); high-grade discovery leverage; pre-production."}
        _name, _meta, about = build_symbol_description(
            "ZEC-USD",
            "ZEC-USD",
            "miner_hpc",
            notes=notes,
            profiles_cache={
                "ZEC-USD": {
                    "long_name": "Zcash USD",
                    "summary": "Zcash (ZEC) is a privacy-focused cryptocurrency.",
                }
            },
            category_label="AI Infra / Datacenter & HPC",
        )
        self.assertNotIn("Gold explorer", about)
        self.assertIn("Zcash", about)


if __name__ == "__main__":
    unittest.main()
