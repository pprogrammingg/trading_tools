#!/usr/bin/env python3
"""Tests for shared result JSON access helpers."""

import sys
import unittest
from pathlib import Path

TECH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TECH))

from result_score_access import (  # noqa: E402
    avg_ta_score,
    collect_ta_metrics,
    get_ta_block,
    index_tech_score,
    rsi_score_adjustment,
    tech_score_to_display,
)


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

    def test_collect_ta_metrics_includes_macd(self):
        data = {
            "1W": {
                "yfinance": {
                    "usd": {
                        "ta_library": {
                            "score": 5.0,
                            "rsi": 44.0,
                            "macd_bullish": True,
                            "macd_positive": True,
                            "adx": 28.0,
                            "momentum": 4.5,
                            "close": 110.0,
                            "ema50": 100.0,
                        }
                    }
                }
            }
        }
        m = collect_ta_metrics(data, ("1W",))
        self.assertTrue(m["1W_macd_bullish"])
        self.assertEqual(m["1W_adx"], 28.0)

    def test_index_tech_score_consensus_adjustment(self):
        metrics = collect_ta_metrics(
            {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {
                                "score": 6.0,
                                "rsi": 55.0,
                                "macd_bullish": True,
                                "macd_positive": True,
                                "adx": 30.0,
                                "momentum": 5.0,
                                "close": 120.0,
                                "ema50": 100.0,
                                "obv_trending_up": True,
                                "gmma_bullish": True,
                            }
                        }
                    }
                }
            },
            ("1W",),
        )
        base = tech_score_to_display(6.0)
        blended = index_tech_score(6.0, metrics, ("1W",))
        self.assertGreaterEqual(blended, base)

    def test_rsi_score_adjustment_oversold_vs_overbought(self):
        oversold = {"1W_rsi": 18.0}
        overbought = {"1W_rsi": 88.0}
        self.assertGreater(rsi_score_adjustment(oversold, ("1W",)), 0.0)
        self.assertLess(rsi_score_adjustment(overbought, ("1W",)), 0.0)
        self.assertGreater(
            rsi_score_adjustment(oversold, ("1W",)),
            rsi_score_adjustment({"1W_rsi": 28.0}, ("1W",)),
        )


if __name__ == "__main__":
    unittest.main()
