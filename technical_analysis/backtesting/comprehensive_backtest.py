#!/usr/bin/env python3
"""
Comprehensive Backtesting Framework
Tests scoring system across ALL assets in symbols_config.json
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np
import sys

# Import the scoring functions
from technical_analysis import compute_indicators_tv, load_symbols_config

def download_test_data(symbol, period="2y"):
    """Download historical data for testing"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if len(df) == 0:
            return None
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        return df
    except Exception as e:
        print(f"  Error downloading {symbol}: {e}")
        return None

def resample_data(df, timeframe="1W"):
    """Resample data to specified timeframe"""
    if timeframe == "1W":
        df_resampled = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == "1M":
        df_resampled = df.resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    else:
        df_resampled = df
    
    # Rename columns to match expected format
    df_resampled.columns = [col.capitalize() for col in df_resampled.columns]
    return df_resampled

def calculate_forward_returns(df, current_idx, days_ahead=[5, 10, 20, 30, 60]):
    """Calculate forward returns from a specific point"""
    forward_returns = {}
    if current_idx >= len(df):
        return forward_returns
    
    current_price = df["Close"].iloc[current_idx]
    
    for days in days_ahead:
        future_idx = current_idx + days
        if future_idx < len(df):
            future_price = df["Close"].iloc[future_idx]
            if current_price > 0:
                forward_returns[f"{days}d_return"] = ((future_price / current_price) - 1) * 100
        else:
            forward_returns[f"{days}d_return"] = None
    
    return forward_returns

def backtest_symbol(symbol, category, timeframe="1W", min_data_points=50):
    """
    Backtest scoring system on a single asset
    Returns historical scores and forward returns
    """
    print(f"  Testing {symbol} ({category})...")
    
    # Download data
    df = download_test_data(symbol, period="2y")
    if df is None or len(df) < min_data_points:
        print(f"    ✗ Insufficient data")
        return None
    
    # Resample to timeframe
    df_resampled = resample_data(df, timeframe)
    
    if len(df_resampled) < min_data_points:
        print(f"    ✗ Insufficient data after resampling")
        return None
    
    results = []
    
    # Test at multiple points in time (walk-forward)
    test_points = []
    step = max(1, len(df_resampled) // 30)  # Test ~30 points
    start_idx = min(100, len(df_resampled) - 60)  # Need enough history
    
    for i in range(start_idx, len(df_resampled) - 30, step):  # Leave 30 periods for forward returns
        test_points.append(i)
    
    if len(test_points) == 0:
        test_points = [len(df_resampled) - 31]  # Use last available point
    
    for point_idx in test_points:
        if point_idx >= len(df_resampled) - 5:
            continue
        
        # Get data up to this point
        df_test = df_resampled.iloc[:point_idx+1].copy()
        
        if len(df_test) < 50:
            continue
        
        try:
            # Calculate score with category awareness
            score_result = compute_indicators_tv(df_test, category=category)
            score = score_result.get("score", 0)
            
            # Calculate forward returns
            forward_returns = calculate_forward_returns(df_resampled, point_idx, days_ahead=[5, 10, 20, 30])
            
            if any(v is not None for v in forward_returns.values()):
                results.append({
                    "date": str(df_test.index[-1]),
                    "score": score,
                    "price": df_test["Close"].iloc[-1],
                    "forward_returns": forward_returns,
                    "indicators": {
                        "rsi": score_result.get("rsi"),
                        "adx": score_result.get("adx"),
                        "cci": score_result.get("cci"),
                        "momentum": score_result.get("momentum"),
                    },
                    "score_breakdown": score_result.get("score_breakdown", {})
                })
        except Exception as e:
            print(f"    Error at point {point_idx}: {e}")
            continue
    
    if results:
        print(f"    ✓ {len(results)} test points")
    else:
        print(f"    ✗ No valid test points")
    
    return results

def analyze_by_category(all_results):
    """Analyze results by category to see which indicators work best"""
    category_stats = defaultdict(lambda: {
        "total_tests": 0,
        "score_vs_returns": defaultdict(list),
        "high_score_returns": [],
        "low_score_returns": []
    })
    
    for (symbol, category), results in all_results.items():
        if not results:
            continue
        
        stats = category_stats[category]
        
        for result in results:
            stats["total_tests"] += 1
            score = result["score"]
            
            # Forward returns by score
            for days, return_pct in result.get("forward_returns", {}).items():
                if return_pct is not None:
                    stats["score_vs_returns"][days].append({
                        "score": score,
                        "return": return_pct
                    })
            
            # High vs low score performance
            if score >= 6:
                for days, return_pct in result.get("forward_returns", {}).items():
                    if return_pct is not None:
                        stats["high_score_returns"].append({
                            "days": days,
                            "return": return_pct
                        })
            elif score <= 2:
                for days, return_pct in result.get("forward_returns", {}).items():
                    if return_pct is not None:
                        stats["low_score_returns"].append({
                            "days": days,
                            "return": return_pct
                        })
    
    # Calculate statistics
    category_analysis = {}
    for category, stats in category_stats.items():
        analysis = {
            "total_tests": stats["total_tests"],
            "predictive_power": {},
            "high_vs_low_score": {}
        }
        
        # Predictive power (correlation between score and returns)
        for days in ["5d", "10d", "20d", "30d"]:
            returns_data = stats["score_vs_returns"].get(f"{days}_return", [])
            if len(returns_data) > 5:
                scores = [d["score"] for d in returns_data]
                returns = [d["return"] for d in returns_data]
                
                correlation = pd.Series(scores).corr(pd.Series(returns))
                
                high_score_returns = [d["return"] for d in returns_data if d["score"] >= 6]
                low_score_returns = [d["return"] for d in returns_data if d["score"] <= 2]
                
                analysis["predictive_power"][days] = {
                    "correlation": correlation if not pd.isna(correlation) else 0,
                    "avg_return_high_score": np.mean(high_score_returns) if high_score_returns else None,
                    "avg_return_low_score": np.mean(low_score_returns) if low_score_returns else None,
                    "sample_size": len(returns_data),
                    "high_score_count": len(high_score_returns),
                    "low_score_count": len(low_score_returns)
                }
        
        # High vs low score comparison
        if stats["high_score_returns"] and stats["low_score_returns"]:
            high_returns = [d["return"] for d in stats["high_score_returns"]]
            low_returns = [d["return"] for d in stats["low_score_returns"]]
            
            analysis["high_vs_low_score"] = {
                "high_avg_return": np.mean(high_returns),
                "high_win_rate": (np.array(high_returns) > 0).sum() / len(high_returns) * 100,
                "low_avg_return": np.mean(low_returns),
                "low_win_rate": (np.array(low_returns) > 0).sum() / len(low_returns) * 100,
                "high_count": len(high_returns),
                "low_count": len(low_returns)
            }
        
        category_analysis[category] = analysis
    
    return category_analysis

def print_summary(category_analysis):
    """Print comprehensive backtest summary"""
    print("\n" + "="*80)
    print("COMPREHENSIVE BACKTEST SUMMARY")
    print("="*80)
    
    total_tests = sum(a["total_tests"] for a in category_analysis.values())
    print(f"\nTotal test points across all categories: {total_tests}")
    
    print("\n" + "="*80)
    print("PREDICTIVE POWER BY CATEGORY (20d forward returns)")
    print("="*80)
    print(f"{'Category':<25s} {'Correlation':<12s} {'High Score':<15s} {'Low Score':<15s} {'Sample':<8s}")
    print("-" * 80)
    
    for category, analysis in sorted(category_analysis.items()):
        stats = analysis["predictive_power"].get("20d", {})
        if stats:
            corr = stats.get("correlation", 0)
            high_ret = stats.get("avg_return_high_score", 0) or 0
            low_ret = stats.get("avg_return_low_score", 0) or 0
            sample = stats.get("sample_size", 0)
            print(f"{category:<25s} {corr:>10.3f}   {high_ret:>13.2f}%    {low_ret:>13.2f}%    {sample:>6d}")
    
    print("\n" + "="*80)
    print("HIGH SCORE (>=6) vs LOW SCORE (<=2) PERFORMANCE")
    print("="*80)
    for category, analysis in sorted(category_analysis.items()):
        if analysis["high_vs_low_score"]:
            hvl = analysis["high_vs_low_score"]
            print(f"\n{category.upper()}:")
            print(f"  High score: {hvl['high_avg_return']:.2f}% avg return, {hvl['high_win_rate']:.1f}% win rate (n={hvl['high_count']})")
            print(f"  Low score:  {hvl['low_avg_return']:.2f}% avg return, {hvl['low_win_rate']:.1f}% win rate (n={hvl['low_count']})")
            if hvl['high_avg_return'] and hvl['low_avg_return']:
                improvement = hvl['high_avg_return'] - hvl['low_avg_return']
                print(f"  Improvement: {improvement:+.2f}%")

def main():
    """Run comprehensive backtest on ALL assets"""
    print("="*80)
    print("COMPREHENSIVE BACKTEST - ALL ASSETS")
    print("="*80)
    print("\nLoading symbols from symbols_config.json...")
    
    # Load all symbols from config
    symbols_config = load_symbols_config()
    
    print(f"\nFound {len(symbols_config)} categories:")
    for category in symbols_config.keys():
        print(f"  - {category}: {len(symbols_config[category])} symbols")
    
    print("\n" + "="*80)
    print("RUNNING BACKTESTS...")
    print("="*80)
    
    all_results = {}
    total_symbols = sum(len(symbols) for symbols in symbols_config.values())
    current_symbol = 0
    
    # Test each category
    for category, symbols in symbols_config.items():
        print(f"\n{category.upper()} ({len(symbols)} symbols):")
        for symbol in symbols:
            current_symbol += 1
            print(f"[{current_symbol}/{total_symbols}]", end=" ")
            try:
                results = backtest_symbol(symbol, category, timeframe="1W")
                if results:
                    all_results[(symbol, category)] = results
                else:
                    print(f"✗ {symbol}: Failed")
            except Exception as e:
                print(f"✗ {symbol}: Error - {e}")
    
    # Analyze results
    print("\n" + "="*80)
    print("ANALYZING RESULTS...")
    print("="*80)
    
    category_analysis = analyze_by_category(all_results)
    print_summary(category_analysis)
    
    # Save detailed results
    output_file = Path("comprehensive_backtest_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "category_analysis": category_analysis,
            "total_symbols_tested": len(all_results),
            "total_test_points": sum(len(r) for r in all_results.values()),
            "detailed_results": {f"{k[0]}_{k[1]}": [
                {
                    "date": r["date"],
                    "score": r["score"],
                    "price": r["price"],
                    "forward_returns": r["forward_returns"],
                    "indicators": r["indicators"]
                } for r in results
            ] for k, results in all_results.items()}
        }, f, indent=2, default=str)
    
    print(f"\n✓ Detailed results saved to {output_file}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    # Find categories where scoring works well
    good_categories = []
    weak_categories = []
    
    for category, analysis in category_analysis.items():
        stats = analysis["predictive_power"].get("20d", {})
        if stats:
            corr = stats.get("correlation", 0)
            if corr > 0.2:
                good_categories.append((category, corr))
            elif corr < 0.1:
                weak_categories.append((category, corr))
    
    if good_categories:
        print("\n✓ Categories with strong predictive power:")
        for category, corr in sorted(good_categories, key=lambda x: x[1], reverse=True):
            print(f"  {category}: Correlation {corr:.3f}")
    
    if weak_categories:
        print("\n⚠ Categories that may need scoring adjustments:")
        for category, corr in sorted(weak_categories, key=lambda x: x[1]):
            print(f"  {category}: Correlation {corr:.3f} (may need category-specific tuning)")
    
    return category_analysis

if __name__ == "__main__":
    main()
