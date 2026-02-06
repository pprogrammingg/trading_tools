"""Tests for print_indicators script: Indicator enum, resolve_categories_or_symbols, print_indicators, and that technical indicators are printed."""

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
    build_report_lines,
    _format_indicator_value,
    _normalize_indicators,
    _normalize_timeframes,
    _load_symbols_config,
    _get_ta_from_results,
    _format_elliott_wave,
    RESULTS_DIR,
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


class TestFormatIndicatorValue(unittest.TestCase):
    def test_format_numeric_sma50(self):
        self.assertEqual(_format_indicator_value(Indicator.SMA_50, 100.5), "sma50=100.5")

    def test_format_numeric_sma100_sma200(self):
        self.assertEqual(_format_indicator_value(Indicator.SMA_100, 99.0), "sma100=99.0")
        self.assertEqual(_format_indicator_value(Indicator.SMA_200, 98.25), "sma200=98.25")

    def test_format_none_returns_dash(self):
        self.assertEqual(_format_indicator_value(Indicator.SMA_50, None), "—")

    def test_format_elliott_wave_dict(self):
        ew = {"wave_position": "Wave 3", "wave_count": {"primary": {"waves": []}}}
        out = _format_indicator_value(Indicator.ELLIOTT_WAVE_COUNT, ew)
        self.assertIn("Wave 3", out)


class TestNormalizeIndicators(unittest.TestCase):
    def test_accepts_enum(self):
        self.assertEqual(_normalize_indicators([Indicator.SMA_50]), [Indicator.SMA_50])

    def test_accepts_string_value(self):
        self.assertEqual(_normalize_indicators(["sma50", "sma100"]), [Indicator.SMA_50, Indicator.SMA_100])

    def test_accepts_mixed(self):
        self.assertEqual(_normalize_indicators([Indicator.SMA_200, "elliott_wave"]), [Indicator.SMA_200, Indicator.ELLIOTT_WAVE_COUNT])


class TestNormalizeTimeframes(unittest.TestCase):
    def test_empty_uses_default(self):
        self.assertEqual(_normalize_timeframes([]), ["1W", "1M"])

    def test_preserves_valid(self):
        self.assertEqual(_normalize_timeframes(["1W", "1M"]), ["1W", "1M"])
        self.assertEqual(_normalize_timeframes(["1D"]), ["1D"])


class TestBuildReportLinesWithMockedIndicators(unittest.TestCase):
    """Tests that prove technical indicators (sma50, sma100, sma200) appear in the report when values are provided."""

    def _mock_get_value(self, sma50_val=None, sma100_val=None, sma200_val=None, elliott_val=None):
        def get_val(symbol: str, tf: str, ind: Indicator, category_key: str):
            if ind == Indicator.SMA_50:
                return sma50_val
            if ind == Indicator.SMA_100:
                return sma100_val
            if ind == Indicator.SMA_200:
                return sma200_val
            if ind == Indicator.ELLIOTT_WAVE_COUNT:
                return elliott_val
            return None
        return get_val

    def test_report_lines_contain_sma50_sma100_sma200_values_when_mocked(self):
        """When get_indicator_value returns fixed numbers, report lines must contain sma50=..., sma100=..., sma200=..."""
        get_val = self._mock_get_value(sma50_val=100.5, sma100_val=99.0, sma200_val=98.25)
        lines = build_report_lines(
            [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200],
            ["BTC-USD"],
            ["1W"],
            get_indicator_value=get_val,
        )
        report_text = "\n".join(lines)
        self.assertIn("sma50=100.5", report_text, "Report should show sma50 value")
        self.assertIn("sma100=99.0", report_text, "Report should show sma100 value")
        self.assertIn("sma200=98.25", report_text, "Report should show sma200 value")
        self.assertIn("INDICATORS REPORT", report_text)
        self.assertIn("BTC-USD", report_text)

    def test_report_lines_show_dash_for_missing_indicator(self):
        """When an indicator value is None, report should show — for that indicator."""
        get_val = self._mock_get_value(sma50_val=1.0, sma100_val=None, sma200_val=2.0)
        lines = build_report_lines(
            [Indicator.SMA_50, Indicator.SMA_100, Indicator.SMA_200],
            ["GC=F"],
            ["1M"],
            get_indicator_value=get_val,
        )
        report_text = "\n".join(lines)
        self.assertIn("sma50=1.0", report_text)
        self.assertIn("sma200=2.0", report_text)
        # Line for 1M should contain two numbers and one dash
        for line in lines:
            if "1M:" in line:
                self.assertIn("—", line, "Missing indicator should appear as —")
                break

    def test_report_no_symbols_resolved_message(self):
        lines = build_report_lines(
            [Indicator.SMA_50],
            [],
            ["1W"],
        )
        self.assertEqual(len(lines), 1)
        self.assertIn("No symbols resolved", lines[0])


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

    def test_printed_report_contains_indicator_values_when_from_results(self):
        """When result file exists, printed report should contain at least one line with indicator=number (technical indicators being printed)."""
        if not (RESULTS_DIR / "precious_metals_results.json").exists():
            self.skipTest("precious_metals_results.json not found")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_indicators(
                [Indicator.SMA_50, Indicator.SMA_200],
                ["precious_metals"],
                ["1W"],
            )
        out = buf.getvalue()
        # At least one line should match sma50=<number> or sma200=<number> (indicator values printed)
        self.assertRegex(
            out,
            r"sma50=\d+\.?\d*|sma200=\d+\.?\d*",
            "Report should show at least one numeric indicator (sma50 or sma200) when results exist",
        )


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
