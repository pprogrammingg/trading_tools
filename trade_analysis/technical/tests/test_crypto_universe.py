#!/usr/bin/env python3
"""Tests for crypto universe policy (top 5 non-stable + TAO + NEAR)."""

import sys
import unittest
from pathlib import Path

TECH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TECH))

from crypto_universe import (  # noqa: E402
    display_pair,
    index_pairs_for_symbol,
    is_stablecoin,
    resolve_crypto_symbols,
)


class TestCryptoUniverse(unittest.TestCase):
    def test_stable_detection(self):
        self.assertTrue(is_stablecoin("USDT-USD"))
        self.assertFalse(is_stablecoin("ETH-USD"))

    def test_resolve_includes_tao_near(self):
        syms = resolve_crypto_symbols(use_network=False, force_refresh=True)
        self.assertIn("TAO-USD", syms)
        self.assertIn("NEAR-USD", syms)
        self.assertLessEqual(len([s for s in syms if s not in ("TAO-USD", "NEAR-USD")]), 5)

    def test_index_pairs_eth(self):
        pairs = index_pairs_for_symbol("ETH-USD")
        labels = [p[0] for p in pairs]
        self.assertEqual(labels, ["ETH/USD", "ETH/BTC"])

    def test_index_pairs_btc_usd_only(self):
        pairs = index_pairs_for_symbol("BTC-USD")
        self.assertEqual(pairs, [("BTC/USD", "usd")])

    def test_display_pair(self):
        self.assertEqual(display_pair("SOL-USD", "usd"), "SOL/USD")
        self.assertEqual(display_pair("SOL-USD", "btc"), "SOL/BTC")


if __name__ == "__main__":
    unittest.main()
