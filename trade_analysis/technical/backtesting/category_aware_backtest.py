#!/usr/bin/env python3
"""
Category-Aware Backtesting Framework
Tests if different indicators work better for different asset categories
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import numpy as np

# Import the scoring functions
from technical_analysis import compute_indicators_tv, compute_indicators_with_score

# Test assets by category (uncorrelated)
TEST_ASSETS = {
    "cryptocurrencies": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "tech_stocks": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "commodities": ["GC=F", "SI=F", "CL=F", "PA=F"],  # Gold, Silver, Oil, Palladium
    "mining": ["AEM", "AG", "PAAS", "HL"],
    "renewable_energy": ["ENPH", "SEDG", "NEE"],
    "semiconductors": ["AVGO", "AMD", "QCOM"],
    "index_etfs": ["SPY", "IWM", "QQQ"]
}

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
                        "rsi_divergence": "bearish_divergence" in str(score_result.get("score_breakdown", {})),
                        "macd_divergence": "macd_bearish_divergence" in str(score_result.get("score_breakdown", {})),
                        "volume_surge": "volume_surge" in str(score_result.get("score_breakdown", {})),
                        "base_formation": "base" in str(score_result.get("score_breakdown", {})),
                        "overextension": "overextension" in str(score_result.get("score_breakdown", {})),
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
        "indicator_performance": defaultdict(lambda: {"returns": [], "count": 0}),
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
            indicators = result.get("indicators", {})
            
            # Forward returns by score
            for days, return_pct in result.get("forward_returns", {}).items():
                if return_pct is not None:
                    stats["score_vs_returns"][days].append({
                        "score": score,
                        "return": return_pct
                    })
            
            # Indicator performance
            for indicator, value in indicators.items():
                if isinstance(value, bool) and value:
                    for days, return_pct in result.get("forward_returns", {}).items():
                        if return_pct is not None:
                            stats["indicator_performance"][f"{indicator}_{days}"]["returns"].append(return_pct)
                            stats["indicator_performance"][f"{indicator}_{days}"]["count"] += 1
                elif isinstance(value, (int, float)) and not pd.isna(value):
                    # Store indicator value with returns
                    for days, return_pct in result.get("forward_returns", {}).items():
                        if return_pct is not None:
                            stats["indicator_performance"][f"{indicator}_{days}"]["returns"].append(return_pct)
                            stats["indicator_performance"][f"{indicator}_{days}"]["count"] += 1
            
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
            "indicator_effectiveness": {},
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
        
        # Indicator effectiveness
        for indicator_key, data in stats["indicator_performance"].items():
            if data["count"] >= 5:  # Minimum sample size
                returns = data["returns"]
                avg_return = np.mean(returns)
                win_rate = (np.array(returns) > 0).sum() / len(returns) * 100
                
                analysis["indicator_effectiveness"][indicator_key] = {
                    "avg_return": avg_return,
                    "win_rate": win_rate,
                    "sample_size": data["count"]
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

def print_category_analysis(category_analysis):
    """Print detailed analysis by category"""
    print("\n" + "="*80)
    print("CATEGORY-SPECIFIC ANALYSIS")
    print("="*80)
    
    for category, analysis in sorted(category_analysis.items()):
        print(f"\n{'='*80}")
        print(f"{category.upper()}")
        print('='*80)
        print(f"Total test points: {analysis['total_tests']}")
        
        # Predictive power
        if analysis["predictive_power"]:
            print("\nPredictive Power (Score vs Forward Returns):")
            for days, stats in sorted(analysis["predictive_power"].items()):
                print(f"\n  {days} forward:")
                print(f"    Correlation: {stats['correlation']:.3f}")
                if stats['avg_return_high_score'] is not None:
                    print(f"    Avg return (score >= 6): {stats['avg_return_high_score']:.2f}% (n={stats['high_score_count']})")
                if stats['avg_return_low_score'] is not None:
                    print(f"    Avg return (score <= 2): {stats['avg_return_low_score']:.2f}% (n={stats['low_score_count']})")
                print(f"    Total sample: {stats['sample_size']}")
        
        # Indicator effectiveness
        if analysis["indicator_effectiveness"]:
            print("\nIndicator Effectiveness:")
            # Group by indicator type
            indicator_groups = defaultdict(list)
            for key, data in analysis["indicator_effectiveness"].items():
                indicator_name = key.split('_')[0]  # e.g., 'rsi', 'adx', 'divergence'
                indicator_groups[indicator_name].append((key, data))
            
            for indicator_name, items in sorted(indicator_groups.items()):
                print(f"\n  {indicator_name.upper()}:")
                for key, data in sorted(items, key=lambda x: x[1]["avg_return"], reverse=True)[:5]:
                    print(f"    {key:30s}: Avg return {data['avg_return']:6.2f}%, Win rate {data['win_rate']:5.1f}% (n={data['sample_size']})")
        
        # High vs low score
        if analysis["high_vs_low_score"]:
            hvl = analysis["high_vs_low_score"]
            print("\nHigh Score (>=6) vs Low Score (<=2):")
            print(f"  High score: {hvl['high_avg_return']:.2f}% avg return, {hvl['high_win_rate']:.1f}% win rate (n={hvl['high_count']})")
            print(f"  Low score:  {hvl['low_avg_return']:.2f}% avg return, {hvl['low_win_rate']:.1f}% win rate (n={hvl['low_count']})")
            if hvl['high_avg_return'] and hvl['low_avg_return']:
                improvement = hvl['high_avg_return'] - hvl['low_avg_return']
                print(f"  Improvement: {improvement:+.2f}%")

def print_category_comparison(category_analysis):
    """Compare categories to see which work best"""
    print("\n" + "="*80)
    print("CATEGORY COMPARISON")
    print("="*80)
    
    # Compare predictive power across categories
    print("\nPredictive Power by Category (20d forward returns):")
    print(f"{'Category':<20s} {'Correlation':<12s} {'High Score Return':<18s} {'Low Score Return':<18s} {'Sample':<8s}")
    print("-" * 80)
    
    for category, analysis in sorted(category_analysis.items()):
        stats = analysis["predictive_power"].get("20d", {})
        if stats:
            corr = stats.get("correlation", 0)
            high_ret = stats.get("avg_return_high_score", 0) or 0
            low_ret = stats.get("avg_return_low_score", 0) or 0
            sample = stats.get("sample_size", 0)
            print(f"{category:<20s} {corr:>10.3f}   {high_ret:>15.2f}%      {low_ret:>15.2f}%      {sample:>6d}")
    
    # Best performing indicators by category
    print("\n\nBest Performing Indicators by Category:")
    for category, analysis in sorted(category_analysis.items()):
        if analysis["indicator_effectiveness"]:
            # Get top 3 indicators
            top_indicators = sorted(
                analysis["indicator_effectiveness"].items(),
                key=lambda x: x[1]["avg_return"],
                reverse=True
            )[:3]
            
            if top_indicators:
                print(f"\n{category.upper()}:")
                for key, data in top_indicators:
                    indicator_name = key.split('_')[0]
                    print(f"  {indicator_name:15s}: {data['avg_return']:6.2f}% avg return, {data['win_rate']:5.1f}% win rate")

def main():
    """Run comprehensive category-aware backtest"""
    print("="*80)
    print("CATEGORY-AWARE PREDICTIVE SCORING BACKTEST")
    print("="*80)
    print("\nTesting on diverse uncorrelated assets by category...")
    print("Including: BTC-USD, ETH-USD, SOL-USD for crypto validation\n")
    
    all_results = {}
    
    # Test each category
    for category, symbols in TEST_ASSETS.items():
        print(f"\n{category.upper()}:")
        for symbol in symbols:
            try:
                results = backtest_symbol(symbol, category, timeframe="1W")
                if results:
                    all_results[(symbol, category)] = results
                else:
                    print(f"    ✗ {symbol}: Failed")
            except Exception as e:
                print(f"    ✗ {symbol}: Error - {e}")
    
    # Analyze by category
    print("\n" + "="*80)
    print("ANALYZING RESULTS BY CATEGORY...")
    print("="*80)
    
    category_analysis = analyze_by_category(all_results)
    print_category_analysis(category_analysis)
    print_category_comparison(category_analysis)
    
    # Save detailed results
    output_file = Path("category_aware_backtest_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "category_analysis": category_analysis,
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
    for category, analysis in category_analysis.items():
        stats = analysis["predictive_power"].get("20d", {})
        if stats and stats.get("correlation", 0) > 0.2:
            good_categories.append((category, stats["correlation"]))
    
    if good_categories:
        print("\nCategories with strong predictive power:")
        for category, corr in sorted(good_categories, key=lambda x: x[1], reverse=True):
            print(f"  ✓ {category}: Correlation {corr:.3f}")
    
    # Find categories that might need adjustment
    weak_categories = []
    for category, analysis in category_analysis.items():
        stats = analysis["predictive_power"].get("20d", {})
        if stats and stats.get("correlation", 0) < 0.1:
            weak_categories.append((category, stats["correlation"]))
    
    if weak_categories:
        print("\nCategories that may need scoring adjustments:")
        for category, corr in sorted(weak_categories, key=lambda x: x[1]):
            print(f"  ⚠ {category}: Correlation {corr:.3f} (may need category-specific tuning)")
    
    return category_analysis

if __name__ == "__main__":
    main()
