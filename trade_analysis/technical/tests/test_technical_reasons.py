#!/usr/bin/env python3
"""Tests for RSI/Stoch technical reason interpreter."""

import sys
import unittest
from pathlib import Path

TECH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TECH))

from technical_reasons import (  # noqa: E402
    build_technical_reasons,
    format_tf_snapshot,
    rsi_verdict_bias,
    stoch_verdict_bias,
    verdict_display_label,
    verdict_sort_rank,
)


class TestTechnicalReasons(unittest.TestCase):
    def _sample_metrics(self) -> dict:
        return {
            "1W_rsi": 28.0,
            "1W_score": 6.2,
            "1W_macd_bullish": True,
            "1W_macd_positive": False,
            "1W_adx": 22.0,
            "1W_adx_strong_trend": False,
            "1W_momentum": -4.0,
            "1W_close": 100.0,
            "1W_ema50": 95.0,
            "1W_obv_trending_up": True,
            "1W_acc_dist_trending_up": False,
            "1W_gmma_bullish": False,
            "1W_volume_above_avg": True,
            "1W_stoch": 24.0,
            "1W_stoch_d": 20.0,
        }

    def test_compact_tf_line(self):
        line = format_tf_snapshot("1W", self._sample_metrics(), "W")
        self.assertIsNotNone(line)
        assert line is not None
        self.assertTrue(line.startswith("W | "))
        self.assertIn("rsi: 28", line)
        self.assertIn("macd:", line)
        self.assertIn("stoch: 24/20 (neutral)", line)

    def test_rsi_bias_monotonic(self):
        self.assertGreater(rsi_verdict_bias(10), rsi_verdict_bias(25))
        self.assertGreater(rsi_verdict_bias(25), 0.0)
        self.assertEqual(rsi_verdict_bias(50), 0.0)
        self.assertLess(rsi_verdict_bias(85), rsi_verdict_bias(75))
        self.assertLess(rsi_verdict_bias(75), 0.0)

    def test_stoch_bias_monotonic(self):
        self.assertGreater(stoch_verdict_bias(8), stoch_verdict_bias(18))
        self.assertGreater(stoch_verdict_bias(18), 0.0)
        self.assertEqual(stoch_verdict_bias(50), 0.0)
        self.assertLess(stoch_verdict_bias(92), stoch_verdict_bias(85))
        self.assertLess(stoch_verdict_bias(85), 0.0)

    def test_stoch_only_overbought_sell(self):
        v, text = build_technical_reasons(
            {
                "1W_rsi": 55.0,
                "1W_score": 5.0,
                "1W_stoch": 88.0,
                "1W_stoch_d": 85.0,
            },
            timeframes=("1W",),
            tf_labels={"1W": "W"},
        )
        self.assertIn(v, ("Sell", "Strong Sell (Get Out)"))
        self.assertIn("Stoch", text)

    def test_deep_oversold_accumulation(self):
        m = self._sample_metrics()
        m["1W_rsi"] = 18.0
        m["1M_rsi"] = 25.0
        m["1M_score"] = 5.0
        m["1M_macd_bullish"] = False
        m["1M_macd_positive"] = False
        m["1M_adx"] = 18.0
        m["1M_momentum"] = -2.0
        m["1M_close"] = 90.0
        m["1M_ema50"] = 95.0
        v, text = build_technical_reasons(m, timeframes=("1W", "1M"), tf_labels={"1W": "W", "1M": "M"})
        self.assertIn(v, ("Strong Accumulation", "Accumulation"))
        self.assertIn("oversold", text.lower())

    def test_overbought_sell(self):
        v, text = build_technical_reasons(
            {
                "1M_rsi": 78.0,
                "1M_score": 3.0,
                "1M_macd_bullish": False,
                "1M_macd_positive": False,
                "1M_adx": 30.0,
                "1M_momentum": -5.0,
                "1M_close": 80.0,
                "1M_ema50": 90.0,
                "1M_stoch": 88.0,
                "1M_stoch_d": 85.0,
            },
            timeframes=("1M",),
        )
        self.assertIn(v, ("Sell", "Strong Sell (Get Out)"))
        self.assertIn("overbought", text.lower())

    def test_high_weekly_rsi_blocks_accumulation_like_smh(self):
        v, text = build_technical_reasons(
            {
                "1W_rsi": 69.9,
                "1W_score": 8.4,
                "1W_macd_bullish": True,
                "1W_macd_positive": True,
                "1W_adx": 41.0,
                "1W_adx_strong_trend": True,
                "1W_momentum": 50.0,
                "1W_close": 300.0,
                "1W_ema50": 280.0,
                "1W_gmma_bullish": True,
                "1W_volume_above_avg": True,
                "2W_rsi": 75.7,
                "2W_score": 5.8,
                "2W_macd_bullish": True,
                "2W_macd_positive": True,
                "2W_adx": 47.0,
                "2W_momentum": 50.0,
                "2W_close": 300.0,
                "2W_ema50": 280.0,
                "2W_obv_trending_up": True,
                "2W_gmma_bullish": True,
                "1M_rsi": 87.5,
                "1M_score": 8.7,
                "1M_macd_bullish": True,
                "1M_macd_positive": True,
                "1M_adx": 39.0,
                "1M_momentum": 50.0,
                "1M_close": 300.0,
                "1M_ema50": 280.0,
                "1M_obv_trending_up": True,
                "1M_gmma_bullish": True,
                "2M_rsi": 85.0,
                "2M_score": 0.0,
                "2M_macd_bullish": False,
                "2M_macd_positive": False,
                "2M_adx": 49.0,
                "2M_momentum": 50.0,
                "2M_obv_trending_up": True,
                "2M_gmma_bullish": True,
            },
            timeframes=("1W", "2W", "1M", "2M"),
            tf_labels={"1W": "W", "2W": "2W", "1M": "M", "2M": "2M"},
        )
        self.assertIn(v, ("Sell", "Strong Sell (Get Out)"))
        self.assertNotIn(v, ("Strong Accumulation", "Accumulation"))
        self.assertIn("overbought", text.lower())

    def test_verdict_sort_rank(self):
        self.assertLess(verdict_sort_rank("Strong Accumulation"), verdict_sort_rank("Accumulation"))
        self.assertLess(verdict_sort_rank("Sell"), verdict_sort_rank("Strong Sell (Get Out)"))

    def test_accumulation_display_labels(self):
        self.assertEqual(verdict_display_label("Strong Accumulation"), "**Strong Accumulation**")
        self.assertEqual(verdict_display_label("Accumulation"), "**Accumulation**")
        self.assertEqual(verdict_display_label("Strong Sell (Get Out)"), "Strong Sell (Get Out)")


if __name__ == "__main__":
    unittest.main()
