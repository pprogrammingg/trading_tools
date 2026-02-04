"""Tests for print_indicators script: Indicator enum, resolve_categories_or_symbols, print_indicators."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure we can import from scripts
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Prevent print_indicators from chdir when imported in tests
sys._print_indicators_chdir = False

from scripts.print_indicators import (
    Indicator,
    resolve_categories_or_symbols,
    print_indicators,
    _load_symbols_config,
    _get_ta_from_results,
    _format_elliott_wave,
    RESULTS_DIR,
    SYMBOLS_CONFIG_PATH,
)


class TestIndicatorEnum(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(Indicator.SMA_50.value, "sma50")
        self.assertEqual(Indicator.SMA_100.value, "sma100")
        self.assertEqual(Indicator.SMA_200.value, "sma200")
        self.assertEqual(Indicator.ELLIOTT_WAVE_COUNT.value, "elliott_wave")

    def test_enum_from_string_value(self):
        self.assertEqual(Indicator("sma50"), Indicator.SMA_50)
        self.assertEqual(Indicator("elliott_wave"), Indicator.ELLIOTT_WAVE_COUNT)


class TestResolveCategoriesOrSymbols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.symbols_config = _load_symbols_config()

    def test_resolve_category_precious_metals(self):
        resolved = resolve_categories_or_symbols(["precious_metals"], self.symbols_config)
        self.assertGreater(len(resolved), 0)
        symbols = [s for s, _ in resolved]
        self.assertIn("GC=F", symbols)
        self.assertIn("SI=F", symbols)
        for _, cat in resolved:
            self.assertEqual(cat, "precious_metals")

    def test_resolve_category_uppercase_alias(self):
        resolved = resolve_categories_or_symbols(["PRECIOUS_METALS"], self.symbols_config)
        self.assertGreater(len(resolved), 0)
        symbols = [s for s, _ in resolved]
        self.assertIn("GC=F", symbols)

    def test_resolve_index_funds_alias(self):
        resolved = resolve_categories_or_symbols(["INDEX_FUNDS"], self.symbols_config)
        self.assertGreater(len(resolved), 0)
        categories = {c for _, c in resolved}
        self.assertIn("index_etfs", categories)

    def test_resolve_symbol_btc_alias(self):
        resolved = resolve_categories_or_symbols(["BTC"], self.symbols_config)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0][0], "BTC-USD")
        self.assertEqual(resolved[0][1], "cryptocurrencies")

    def test_resolve_symbol_direct(self):
        resolved = resolve_categories_or_symbols(["BTC-USD", "GC=F"], self.symbols_config)
        self.assertEqual(len(resolved), 2)
        syms = {s for s, _ in resolved}
        self.assertIn("BTC-USD", syms)
        self.assertIn("GC=F", syms)

    def test_resolve_mixed_category_and_symbol(self):
        resolved = resolve_categories_or_symbols(
            ["BTC-USD", "precious_metals"],
            self.symbols_config,
        )
        symbols = [s for s, _ in resolved]
        self.assertIn("BTC-USD", symbols)
        self.assertIn("GC=F", symbols)

    def test_resolve_deduplicates(self):
        resolved = resolve_categories_or_symbols(
            ["precious_metals", "GC=F"],
            self.symbols_config,
        )
        symbols = [s for s, _ in resolved]
        self.assertEqual(symbols.count("GC=F"), 1)

    def test_resolve_pair_btc_gold(self):
        resolved = resolve_categories_or_symbols(["BTC/GOLD"], self.symbols_config)
        self.assertEqual(len(resolved), 2)
        symbols = [s for s, _ in resolved]
        self.assertIn("BTC-USD", symbols)
        self.assertIn("GC=F", symbols)


class TestPrintIndicators(unittest.TestCase):
    def test_print_indicators_captures_stdout(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicators(
                [Indicator.SMA_50, Indicator.ELLIOTT_WAVE_COUNT],
                ["precious_metals"],
                ["1W", "1M"],
            )
        out = buf.getvalue()
        self.assertIn("INDICATORS REPORT", out)
        self.assertIn("sma50", out)
        self.assertIn("elliott_wave", out)
        self.assertIn("1W", out)
        self.assertIn("1M", out)
        self.assertIn("GC=F", out)

    def test_print_indicators_with_empty_timeframes_uses_default(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicators(
                [Indicator.SMA_200],
                ["index_etfs"],
                [],  # empty -> should use default 1W, 1M
            )
        out = buf.getvalue()
        self.assertIn("INDICATORS REPORT", out)
        self.assertIn("1W", out)

    def test_print_indicators_accepts_string_indicators(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicators(
                ["sma50", "elliott_wave"],
                ["precious_metals"],
                ["1M"],
            )
        out = buf.getvalue()
        self.assertIn("INDICATORS REPORT", out)


class TestFormatElliottWave(unittest.TestCase):
    def test_format_empty_returns_dash(self):
        self.assertEqual(_format_elliott_wave(None), "—")
        self.assertEqual(_format_elliott_wave({}), "—")

    def test_format_position_only(self):
        self.assertEqual(
            _format_elliott_wave({"wave_position": "Wave 3 or 5"}),
            "Wave 3 or 5",
        )

    def test_format_with_wave_count(self):
        ew = {
            "wave_position": "Wave 3 or 5",
            "wave_count": {
                "primary": {
                    "waves": [
                        {"number": 1, "start_usd": 100.0, "end_usd": 150.0, "current_wave": True},
                        {"number": 2, "start_usd": 150.0, "end_usd": 120.0, "current_wave": False},
                    ],
                },
            },
        }
        out = _format_elliott_wave(ew)
        self.assertIn("Wave 3 or 5", out)
        self.assertIn("100.0", out)
        self.assertIn("150.0", out)
        self.assertIn("★", out)


class TestGetTaFromResults(unittest.TestCase):
    def test_get_ta_from_results_missing_file(self):
        ta = _get_ta_from_results("GC=F", "1W", "nonexistent_category_xyz")
        self.assertIsNone(ta)

    def test_get_ta_from_results_existing(self):
        if not (RESULTS_DIR / "precious_metals_results.json").exists():
            self.skipTest("precious_metals_results.json not found")
        ta = _get_ta_from_results("GC=F", "1W", "precious_metals")
        if ta is None:
            self.skipTest("No ta_library for GC=F 1W in results")
        self.assertIn("close", ta)
        self.assertIn("sma50", ta)
        self.assertIn("sma200", ta)


if __name__ == "__main__":
    unittest.main()
