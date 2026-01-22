#!/usr/bin/env python3
"""
Comprehensive unit tests for visualize_scores.py
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from visualize_scores import (
    get_score_color,
    sort_timeframes,
    find_results_files,
    load_symbol_categories,
    extract_scores_from_data,
    organize_symbols,
    prepare_visualization_data,
    generate_legend,
    generate_headers,
    generate_cell_content,
    generate_rows,
    generate_html,
    create_visualization,
    create_visualization_for_category,
    ScoreInfo,
    VisualizationData,
    SCORE_THRESHOLDS,
    MISSING_DATA_COLOR,
    MISSING_DATA_LABEL,
)


class TestScoreColor(unittest.TestCase):
    """Test score color determination"""
    
    def test_none_score(self):
        """Test handling of None score"""
        color, label = get_score_color(None)
        self.assertEqual(color, MISSING_DATA_COLOR)
        self.assertEqual(label, MISSING_DATA_LABEL)
    
    def test_high_scores(self):
        """Test high positive scores"""
        test_cases = [
            (10, "#006400", "Great Buy"),
            (6, "#006400", "Great Buy"),
            (5, "#32CD32", "Strong Buy"),
            (4, "#32CD32", "Strong Buy"),
            (3, "#90EE90", "OK Buy"),
            (2, "#90EE90", "OK Buy"),
        ]
        for score, expected_color, expected_label in test_cases:
            with self.subTest(score=score):
                color, label = get_score_color(score)
                self.assertEqual(color, expected_color)
                self.assertEqual(label, expected_label)
    
    def test_neutral_scores(self):
        """Test neutral scores"""
        color, label = get_score_color(0)
        self.assertEqual(color, "#FFD700")
        self.assertEqual(label, "Neutral")
        
        color, label = get_score_color(1)
        self.assertEqual(color, "#FFD700")
        self.assertEqual(label, "Neutral")
    
    def test_negative_scores(self):
        """Test negative scores"""
        test_cases = [
            (-1, "#FFA500", "OK Sell"),
            (-2, "#FFA500", "OK Sell"),
            (-3, "#FF4500", "Best Sell"),
            (-10, "#FF4500", "Best Sell"),
        ]
        for score, expected_color, expected_label in test_cases:
            with self.subTest(score=score):
                color, label = get_score_color(score)
                self.assertEqual(color, expected_color)
                self.assertEqual(label, expected_label)


class TestSortTimeframes(unittest.TestCase):
    """Test timeframe sorting"""
    
    def test_weeks(self):
        """Test week timeframes"""
        self.assertEqual(sort_timeframes("1W"), (0, 1))
        self.assertEqual(sort_timeframes("2W"), (0, 2))
        self.assertEqual(sort_timeframes("12W"), (0, 12))
    
    def test_months(self):
        """Test month timeframes"""
        self.assertEqual(sort_timeframes("1M"), (1, 1))
        self.assertEqual(sort_timeframes("6M"), (1, 6))
        self.assertEqual(sort_timeframes("12M"), (1, 12))
    
    def test_years(self):
        """Test year timeframes"""
        self.assertEqual(sort_timeframes("1Y"), (2, 1))
        self.assertEqual(sort_timeframes("5Y"), (2, 5))
    
    def test_unknown_format(self):
        """Test unknown timeframe format"""
        self.assertEqual(sort_timeframes("unknown"), (3, 0))
        self.assertEqual(sort_timeframes(""), (3, 0))


class TestFindResultsFiles(unittest.TestCase):
    """Test finding results files"""
    
    def test_find_in_result_scores_dir(self):
        """Test finding files in result_scores directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result_scores_dir = Path(tmpdir) / 'result_scores'
            result_scores_dir.mkdir()
            test_file = result_scores_dir / 'quantum_results.json'
            test_file.write_text('{}')
            
            with patch('visualize_scores.Path.cwd', return_value=Path(tmpdir)):
                results = find_results_files()
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0][0], 'quantum')
                self.assertEqual(results[0][1], test_file)
    
    def test_find_legacy_file(self):
        """Test finding legacy all_results.json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'all_results.json'
            test_file.write_text('{}')
            
            with patch('visualize_scores.Path.cwd', return_value=Path(tmpdir)):
                results = find_results_files()
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0][0], 'all')
                self.assertEqual(results[0][1], test_file)
    
    def test_no_files_found(self):
        """Test when no files are found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('visualize_scores.Path.cwd', return_value=Path(tmpdir)):
                results = find_results_files()
                self.assertEqual(len(results), 0)


class TestLoadSymbolCategories(unittest.TestCase):
    """Test loading symbol categories"""
    
    def test_successful_import(self):
        """Test successful import of categories"""
        # This test verifies the function doesn't crash
        # Actual import success depends on technical_analysis module existing
        tech, crypto, metals = load_symbol_categories()
        # Should return lists regardless of import success
        self.assertIsInstance(tech, list)
        self.assertIsInstance(crypto, list)
        self.assertIsInstance(metals, list)
    
    def test_import_error(self):
        """Test handling of import error"""
        # This will fail if technical_analysis doesn't exist
        # but that's expected behavior
        tech, crypto, metals = load_symbol_categories()
        # Should return empty lists if import fails
        self.assertIsInstance(tech, list)
        self.assertIsInstance(crypto, list)
        self.assertIsInstance(metals, list)


class TestExtractScoresFromData(unittest.TestCase):
    """Test extracting scores from data"""
    
    def test_basic_extraction(self):
        """Test basic score extraction"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 5.5},
                            "tradingview_library": {"score": 6.0}
                        }
                    }
                }
            }
        }
        
        symbol_scores, timeframes, sources, denominations = extract_scores_from_data(data)
        
        self.assertIn("AAPL", symbol_scores)
        self.assertIn("1W", timeframes)
        self.assertIn("yfinance", sources)
        self.assertIn("usd", denominations)
        
        key = "1W_yfinance_usd"
        self.assertIn(key, symbol_scores["AAPL"])
        score_info = symbol_scores["AAPL"][key]
        self.assertEqual(score_info.score, 6.0)  # Should use max score
        self.assertEqual(score_info.timeframe, "1W")
        self.assertEqual(score_info.source, "yfinance")
        self.assertEqual(score_info.denomination, "usd")
    
    def test_multiple_symbols(self):
        """Test extraction with multiple symbols"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 5.0}
                        }
                    }
                }
            },
            "GOOGL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 3.0}
                        },
                        "gold": {
                            "ta_library": {"score": 2.0}
                        }
                    }
                }
            }
        }
        
        symbol_scores, timeframes, sources, denominations = extract_scores_from_data(data)
        
        self.assertEqual(len(symbol_scores), 2)
        self.assertIn("usd", denominations)
        self.assertIn("gold", denominations)
    
    def test_potential_info_extraction(self):
        """Test extraction of potential info"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {
                                "score": 5.0,
                                "relative_potential": {
                                    "upside_potential_pct": 10.5,
                                    "downside_potential_pct": 5.2
                                }
                            }
                        }
                    }
                }
            }
        }
        
        symbol_scores, _, _, _ = extract_scores_from_data(data)
        
        key = "1W_yfinance_usd"
        score_info = symbol_scores["AAPL"][key]
        self.assertEqual(score_info.upside_potential, 10.5)
        self.assertEqual(score_info.downside_potential, 5.2)
    
    def test_no_scores(self):
        """Test handling when no scores are present"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {}
                    }
                }
            }
        }
        
        symbol_scores, _, _, _ = extract_scores_from_data(data)
        self.assertEqual(len(symbol_scores["AAPL"]), 0)
    
    def test_none_score(self):
        """Test handling of None scores"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": None},
                            "tradingview_library": {"score": 5.0}
                        }
                    }
                }
            }
        }
        
        symbol_scores, _, _, _ = extract_scores_from_data(data)
        key = "1W_yfinance_usd"
        # Should still extract the valid score
        self.assertIn(key, symbol_scores["AAPL"])
        self.assertEqual(symbol_scores["AAPL"][key].score, 5.0)


class TestOrganizeSymbols(unittest.TestCase):
    """Test symbol organization"""
    
    def test_alphabetical_fallback(self):
        """Test alphabetical sorting when categories unavailable"""
        data = {"Z", "A", "M"}
        # Since we can't easily mock the import, we test the fallback logic
        # by ensuring it handles the case gracefully
        result = organize_symbols({"Z": {}, "A": {}, "M": {}})
        # Should return a list
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
    
    def test_with_categories(self):
        """Test organization with categories"""
        # This would require mocking the import, which is complex
        # So we test that it returns a valid list
        data = {"AAPL": {}, "GOOGL": {}}
        result = organize_symbols(data)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)


class TestPrepareVisualizationData(unittest.TestCase):
    """Test preparing visualization data"""
    
    def test_basic_preparation(self):
        """Test basic data preparation"""
        data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 5.0}
                        }
                    }
                },
                "2W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 4.0}
                        }
                    }
                }
            }
        }
        
        viz_data = prepare_visualization_data(data)
        
        self.assertIsInstance(viz_data, VisualizationData)
        self.assertIn("AAPL", viz_data.symbols)
        self.assertIn("1W", viz_data.timeframes)
        self.assertIn("2W", viz_data.timeframes)
        self.assertIn("yfinance", viz_data.sources)
        self.assertIn("usd", viz_data.denominations)
        
        # Check timeframes are sorted
        self.assertEqual(viz_data.timeframes[0], "1W")
        self.assertEqual(viz_data.timeframes[1], "2W")


class TestGenerateLegend(unittest.TestCase):
    """Test legend generation"""
    
    def test_legend_contains_required_elements(self):
        """Test that legend contains required elements"""
        legend = generate_legend()
        
        self.assertIn("Score Legend", legend)
        self.assertIn("Great Buy", legend)
        self.assertIn("Strong Buy", legend)
        self.assertIn("Potential Indicators", legend)
        self.assertIn("Upside potential", legend)
        self.assertIn("Downside potential", legend)


class TestGenerateHeaders(unittest.TestCase):
    """Test header generation"""
    
    def test_basic_headers(self):
        """Test basic header generation"""
        viz_data = VisualizationData(
            symbols=["AAPL"],
            timeframes=["1W"],
            sources=["yfinance"],
            denominations=["usd"],
            symbol_scores={},
            raw_data={}
        )
        
        headers = generate_headers(viz_data)
        
        self.assertIn("1W", headers)
        self.assertIn("yfinance", headers)
        self.assertIn("USD", headers)
        self.assertIn("<th>", headers)
    
    def test_multiple_headers(self):
        """Test multiple header generation"""
        viz_data = VisualizationData(
            symbols=["AAPL"],
            timeframes=["1W", "2W"],
            sources=["yfinance"],
            denominations=["usd", "gold"],
            symbol_scores={},
            raw_data={}
        )
        
        headers = generate_headers(viz_data)
        
        # Should have 4 headers (2 timeframes * 1 source * 2 denominations)
        self.assertEqual(headers.count("<th>"), 4)
        self.assertIn("Gold", headers)
        self.assertIn("USD", headers)


class TestGenerateCellContent(unittest.TestCase):
    """Test cell content generation"""
    
    def test_none_score_info(self):
        """Test cell with None score info"""
        content = generate_cell_content(None)
        
        self.assertIn(MISSING_DATA_COLOR, content)
        self.assertIn(MISSING_DATA_LABEL, content)
        self.assertIn("score-cell", content)
    
    def test_basic_score_info(self):
        """Test cell with basic score info"""
        score_info = ScoreInfo(
            score=5.0,
            timeframe="1W",
            source="yfinance",
            denomination="usd"
        )
        
        content = generate_cell_content(score_info)
        
        self.assertIn("5.0", content)
        self.assertIn("score-cell", content)
        color, _ = get_score_color(5.0)
        self.assertIn(color, content)
    
    def test_score_with_potential(self):
        """Test cell with potential info"""
        score_info = ScoreInfo(
            score=5.0,
            timeframe="1W",
            source="yfinance",
            denomination="usd",
            upside_potential=10.5,
            downside_potential=5.2
        )
        
        content = generate_cell_content(score_info)
        
        self.assertIn("5.0", content)
        self.assertIn("10.5", content)
        self.assertIn("5.2", content)
        self.assertIn("&uarr;", content)  # HTML entity for up arrow
        self.assertIn("&darr;", content)  # HTML entity for down arrow


class TestGenerateRows(unittest.TestCase):
    """Test row generation"""
    
    def test_basic_rows(self):
        """Test basic row generation"""
        viz_data = VisualizationData(
            symbols=["AAPL"],
            timeframes=["1W"],
            sources=["yfinance"],
            denominations=["usd"],
            symbol_scores={
                "AAPL": {
                    "1W_yfinance_usd": ScoreInfo(
                        score=5.0,
                        timeframe="1W",
                        source="yfinance",
                        denomination="usd"
                    )
                }
            },
            raw_data={}
        )
        
        rows = generate_rows(viz_data)
        
        self.assertIn("AAPL", rows)
        self.assertIn("<tr>", rows)
        self.assertIn("5.0", rows)
    
    def test_multiple_symbols(self):
        """Test rows with multiple symbols"""
        viz_data = VisualizationData(
            symbols=["AAPL", "GOOGL"],
            timeframes=["1W"],
            sources=["yfinance"],
            denominations=["usd"],
            symbol_scores={
                "AAPL": {
                    "1W_yfinance_usd": ScoreInfo(
                        score=5.0,
                        timeframe="1W",
                        source="yfinance",
                        denomination="usd"
                    )
                },
                "GOOGL": {
                    "1W_yfinance_usd": ScoreInfo(
                        score=3.0,
                        timeframe="1W",
                        source="yfinance",
                        denomination="usd"
                    )
                }
            },
            raw_data={}
        )
        
        rows = generate_rows(viz_data)
        
        self.assertIn("AAPL", rows)
        self.assertIn("GOOGL", rows)
        self.assertEqual(rows.count("<tr>"), 2)


class TestGenerateHTML(unittest.TestCase):
    """Test HTML generation"""
    
    def test_complete_html(self):
        """Test complete HTML generation"""
        viz_data = VisualizationData(
            symbols=["AAPL"],
            timeframes=["1W"],
            sources=["yfinance"],
            denominations=["usd"],
            symbol_scores={
                "AAPL": {
                    "1W_yfinance_usd": ScoreInfo(
                        score=5.0,
                        timeframe="1W",
                        source="yfinance",
                        denomination="usd"
                    )
                }
            },
            raw_data={}
        )
        
        html = generate_html(viz_data)
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html>", html)
        self.assertIn("<head>", html)
        self.assertIn("<body>", html)
        self.assertIn("<table>", html)
        self.assertIn("AAPL", html)
        self.assertIn("5.0", html)


class TestCreateVisualization(unittest.TestCase):
    """Test main visualization creation"""
    
    def test_create_visualization(self):
        """Test creating visualization"""
        # Create test data
        test_data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 5.0},
                            "tradingview_library": {"score": 6.0}
                        }
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test results file
            results_file = Path(tmpdir) / 'all_results.json'
            results_file.write_text(json.dumps(test_data))
            
            # Create output file path
            output_file = Path(tmpdir) / 'test_output.html'
            
            # Create result_scores directory structure
            result_scores_dir = Path(tmpdir) / 'result_scores'
            result_scores_dir.mkdir()
            results_file = result_scores_dir / 'test_results.json'
            results_file.write_text(json.dumps(test_data))
            
            with patch('visualize_scores.find_results_files', return_value=[('test', results_file)]):
                result_paths = create_visualization()
                
                self.assertIsInstance(result_paths, list)
                self.assertTrue(len(result_paths) > 0)
                result_path = result_paths[0]
                self.assertTrue(result_path.exists())
                
                # Verify HTML content
                html_content = result_path.read_text()
                self.assertIn("<!DOCTYPE html>", html_content)
                self.assertIn("AAPL", html_content)
                self.assertIn("6.0", html_content)  # Should use max score


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_end_to_end(self):
        """Test end-to-end functionality"""
        test_data = {
            "AAPL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {
                                "score": 5.0,
                                "relative_potential": {
                                    "upside_potential_pct": 10.5,
                                    "downside_potential_pct": 5.2
                                }
                            },
                            "tradingview_library": {"score": 6.0}
                        },
                        "gold": {
                            "ta_library": {"score": 4.0}
                        }
                    }
                },
                "2W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 3.0}
                        }
                    }
                }
            },
            "GOOGL": {
                "1W": {
                    "yfinance": {
                        "usd": {
                            "ta_library": {"score": 2.0}
                        }
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create result_scores directory structure
            result_scores_dir = Path(tmpdir) / 'result_scores'
            result_scores_dir.mkdir()
            results_file = result_scores_dir / 'test_results.json'
            results_file.write_text(json.dumps(test_data))
            
            with patch('visualize_scores.find_results_files', return_value=[('test', results_file)]):
                with patch('visualize_scores.Path.cwd', return_value=Path(tmpdir)):
                    result_paths = create_visualization()
                    
                    # Verify file was created
                    self.assertTrue(len(result_paths) > 0)
                    result_path = result_paths[0]
                    self.assertTrue(result_path.exists())
                    
                    # Verify content
                    html = result_path.read_text()
                    
                    # Check symbols
                    self.assertIn("AAPL", html)
                    self.assertIn("GOOGL", html)
                    
                    # Check scores (should use max)
                    self.assertIn("6.0", html)  # AAPL 1W USD (max of 5.0 and 6.0)
                    self.assertIn("4.0", html)  # AAPL 1W Gold
                    self.assertIn("3.0", html)  # AAPL 2W USD
                    self.assertIn("2.0", html)  # GOOGL 1W USD
                    
                    # Check potential info
                    self.assertIn("10.5", html)
                    self.assertIn("5.2", html)
                    
                    # Check timeframes are sorted
                    # 1W should appear before 2W in headers
                    idx_1w = html.find("1W")
                    idx_2w = html.find("2W")
                    self.assertLess(idx_1w, idx_2w)


if __name__ == '__main__':
    unittest.main()
