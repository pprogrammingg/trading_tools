#!/usr/bin/env python3
"""Tests for index landing sector ranking and halal exclusions."""

import json
import tempfile
import unittest
from pathlib import Path

from result_score_access import avg_ta_score
from index_landing_builder import (
    RANK_TIMEFRAMES,
    _rank_sector_symbols,
    build_index_primary_html,
)


class TestIndexLandingBuilder(unittest.TestCase):
    def test_avg_score_from_mock(self):
        data = {
            "1W": {"yfinance": {"usd": {"ta_library": {"score": 4.0, "rsi": 55}}}},
            "1M": {"yfinance": {"usd": {"ta_library": {"score": 6.0, "rsi": 60}}}},
            "2M": {"yfinance": {"usd": {"ta_library": {"score": 8.0, "rsi": 65}}}},
        }
        self.assertAlmostEqual(avg_ta_score(data, RANK_TIMEFRAMES), 6.0)

    def test_blocklist_excludes_defense_ticker(self):
        mock = {
            "NVDA": {
                "1W": {"yfinance": {"usd": {"ta_library": {"score": 5.0, "rsi": 50}}}},
                "1M": {"yfinance": {"usd": {"ta_library": {"score": 5.0, "rsi": 50}}}},
                "2M": {"yfinance": {"usd": {"ta_library": {"score": 5.0, "rsi": 50}}}},
            },
            "LMT": {
                "1W": {"yfinance": {"usd": {"ta_library": {"score": 9.0, "rsi": 70}}}},
                "1M": {"yfinance": {"usd": {"ta_library": {"score": 9.0, "rsi": 70}}}},
                "2M": {"yfinance": {"usd": {"ta_library": {"score": 9.0, "rsi": 70}}}},
            },
        }
        block = {"LMT"}
        ranked = _rank_sector_symbols(mock, block, False, "ai_semiconductors")
        syms = [r[0] for r in ranked]
        self.assertIn("NVDA", syms)
        self.assertNotIn("LMT", syms)

    def test_build_primary_html_has_unicorn_and_sector(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            payload = {
                "AAA": {
                    "1W": {"yfinance": {"usd": {"ta_library": {"score": 3.0, "rsi": 40}}}},
                    "1M": {"yfinance": {"usd": {"ta_library": {"score": 4.0, "rsi": 45}}}},
                    "2M": {"yfinance": {"usd": {"ta_library": {"score": 5.0, "rsi": 50}}}},
                }
            }
            (p / "ai_semiconductors_results.json").write_text(json.dumps(payload), encoding="utf-8")
            html = build_index_primary_html(p, allow_network=False)
            self.assertIn("unicorn-growth", html)
            self.assertIn("sector-tops", html)
            self.assertIn("sector-ai-semiconductors", html)
            self.assertIn("AAA", html)

    def test_space_defense_not_in_sector_sections(self):
        cats = {c for c, _ in __import__("index_landing_builder").INDEX_SECTOR_SECTIONS}
        self.assertNotIn("space_defense", cats)
        self.assertIn("healthcare", cats)


if __name__ == "__main__":
    unittest.main()
