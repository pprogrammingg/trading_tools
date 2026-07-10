#!/usr/bin/env python3
"""Tests for sector ETF signal aggregation."""

import json
import tempfile
import unittest
from pathlib import Path

TECH_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(TECH_ROOT) not in sys.path:
    sys.path.insert(0, str(TECH_ROOT))

from sector_signal import (  # noqa: E402
    MAX_PICKS_PER_SECTOR,
    _aggregate_sector_verdict,
    compute_sector_signal,
    load_sector_etfs,
    pick_sector_index_rows,
    sector_verdict_sort_rank,
)


class TestSectorSignal(unittest.TestCase):
    def test_load_sector_etfs_has_gold_and_crypto(self):
        mapping = load_sector_etfs()
        self.assertIn("gold_miners", mapping)
        self.assertIn("GDX", mapping["gold_miners"])
        self.assertIn("IBIT", mapping["cryptocurrencies"])

    def test_aggregate_majority_five_tier(self):
        self.assertEqual(
            _aggregate_sector_verdict(["Accumulation", "Accumulation", "Neutral"]),
            "Accumulation",
        )
        self.assertEqual(
            _aggregate_sector_verdict(["Sell", "Sell", "Neutral"]),
            "Sell",
        )
        self.assertEqual(
            _aggregate_sector_verdict(["Strong Sell (Get Out)", "Strong Sell (Get Out)", "Neutral"]),
            "Strong Sell (Get Out)",
        )
        self.assertEqual(_aggregate_sector_verdict([]), "Neutral")

    def test_sector_verdict_sort_rank(self):
        self.assertLess(sector_verdict_sort_rank("Strong Accumulation"), sector_verdict_sort_rank("Accumulation"))
        self.assertLess(sector_verdict_sort_rank("Sell"), sector_verdict_sort_rank("Strong Sell (Get Out)"))

    def test_compute_from_fixture(self):
        sym_data = {
            "1W": {"rsi": 45, "stoch": 40, "macd": 0.1, "adx": 25, "momentum": 0.5, "trend": 1},
            "2W": {"rsi": 42, "stoch": 38, "macd": 0.05, "adx": 22, "momentum": 0.3, "trend": 1},
            "1M": {"rsi": 40, "stoch": 35, "macd": 0.02, "adx": 20, "momentum": 0.2, "trend": 0},
            "2M": {"rsi": 38, "stoch": 32, "macd": -0.01, "adx": 18, "momentum": 0.1, "trend": 0},
            "composite_score_usd": 6.5,
        }
        with tempfile.TemporaryDirectory() as tmp:
            result_dir = Path(tmp)
            (result_dir / "precious_metals_results.json").write_text(
                json.dumps({"GDX": sym_data, "GDXJ": sym_data}),
                encoding="utf-8",
            )
            out = compute_sector_signal(
                "gold_miners",
                result_dir,
                sector_etfs={"gold_miners": ["GDX", "GDXJ", "MISSING"]},
            )
        self.assertIn(
            out["sector_verdict"],
            ("Strong Accumulation", "Accumulation", "Neutral", "Sell", "Strong Sell (Get Out)"),
        )
        self.assertIn("GDX", out["etf_summary"])

    def test_pick_sector_index_rows_max_ten(self):
        rows = [
            {"symbol": f"S{i}", "yahoo_symbol": f"S{i}", "final_score": float(i), "tech_score": float(i)}
            for i in range(20)
        ]
        etfs = {"ai_semiconductors": ["SMH", "SOXX"]}
        rows.extend(
            [
                {"symbol": "SMH", "yahoo_symbol": "SMH", "final_score": 99.0, "tech_score": 9.0},
                {"symbol": "SOXX", "yahoo_symbol": "SOXX", "final_score": 98.0, "tech_score": 9.0},
            ]
        )
        picks = pick_sector_index_rows(
            "ai_semiconductors",
            rows,
            max_picks=MAX_PICKS_PER_SECTOR,
            etfs_per_industry=2,
            sector_etfs=etfs,
        )
        self.assertLessEqual(len(picks), MAX_PICKS_PER_SECTOR)
        self.assertEqual(picks[0]["symbol"], "SMH")
        self.assertEqual(picks[1]["symbol"], "SOXX")

    def test_must_include_pinned_in_gold_miners(self):
        rows = [
            {"symbol": "GDX", "yahoo_symbol": "GDX", "final_score": 5.0, "tech_score": 4.0},
            {"symbol": "GDXJ", "yahoo_symbol": "GDXJ", "final_score": 4.8, "tech_score": 4.0},
            {"symbol": "FNV", "yahoo_symbol": "FNV", "final_score": 4.5, "tech_score": 4.0},
            {"symbol": "NFG", "yahoo_symbol": "NFG.V", "final_score": 3.5, "tech_score": 2.3},
            {"symbol": "EQX", "yahoo_symbol": "EQX", "final_score": 4.2, "tech_score": 3.8},
        ]
        picks = pick_sector_index_rows(
            "gold_miners",
            rows,
            max_picks=5,
            etfs_per_industry=2,
            sector_etfs={"gold_miners": ["GDX", "GDXJ"]},
            must_include=["NFG.V"],
        )
        symbols = [p["symbol"] for p in picks]
        self.assertIn("NFG", symbols)
        self.assertEqual(symbols[:2], ["GDX", "GDXJ"])


if __name__ == "__main__":
    unittest.main()
