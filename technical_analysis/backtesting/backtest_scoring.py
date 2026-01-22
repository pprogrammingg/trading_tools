#!/usr/bin/env python3
"""
Comprehensive Backtesting Framework for Predictive Scoring System
Tests the improved scoring system on diverse uncorrelated assets
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Import the scoring functions
from technical_analysis import compute_indicators_tv, compute_indicators_with_score

# Test assets across different categories (uncorrelated)
TEST_ASSETS = {
    "tech_stocks": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "commodities": ["GC=F", "SI=F", "CL=F"],  # Gold, Silver, Oil
    "cryptocurrencies": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "mining": ["AEM", "AG", "PAAS", "HL"],
    "renewable_energy": ["ENPH", "SEDG", "NEE"],
    "semiconductors": ["AVGO", "AMD", "QCOM"],
    "index_etfs": ["SPY", "IWM", "QQQ"]
}

def download_test_data(symbol, period="1y"):
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

def calculate_forward_returns(df, days_ahead=[5, 10, 20, 30, 60]):
    """Calculate forward returns for backtesting"""
    forward_returns = {}
    current_price = df["Close"].iloc[-1]
    
    for days in days_ahead:
        if len(df) > days:
            future_price = df["Close"].iloc[-1-days] if len(df) > days else None
            if future_price and current_price > 0:
                forward_returns[f"{days}d_return"] = ((current_price / future_price) - 1) * 100
            else:
                forward_returns[f"{days}d_return"] = None
        else:
            forward_returns[f"{days}d_return"] = None
    
    return forward_returns

def backtest_scoring(symbol, timeframe="1W", lookback_days=252):
    """
    Backtest scoring system on a single asset
    Returns historical scores and forward returns
    """
    print(f"  Testing {symbol} ({timeframe})...")
    
    # Download data
    df = download_test_data(symbol, period="2y")  # Get 2 years for backtesting
    if df is None or len(df) < lookback_days:
        return None
    
    results = []
    
    # Resample to timeframe
    if timeframe == "1W":
        df_resampled = df.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    elif timeframe == "1M":
        df_resampled = df.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    else:
        df_resampled = df
    
    # Test at multiple points in time
    test_points = []
    step = max(1, len(df_resampled) // 20)  # Test ~20 points
    for i in range(lookback_days, len(df_resampled), step):
        test_points.append(i)
    
    if len(test_points) == 0:
        test_points = [len(df_resampled) - 1]
    
    for point_idx in test_points:
        if point_idx >= len(df_resampled):
            continue
        
        # Get data up to this point
        df_test = df_resampled.iloc[:point_idx+1].copy()
        
        if len(df_test) < 50:  # Need minimum data
            continue
        
        try:
            # Calculate score
            score_result = compute_indicators_tv(df_test)
            score = score_result.get("score", 0)
            
            # Calculate forward returns
            if point_idx < len(df_resampled) - 5:
                future_data = df_resampled.iloc[point_idx:]
                if len(future_data) >= 5:
                    current_price = df_test["Close"].iloc[-1]
                    future_prices = {}
                    for days in [5, 10, 20, 30]:
                        if len(future_data) > days:
                            future_price = future_data["Close"].iloc[days] if days < len(future_data) else None
                            if future_price and current_price > 0:
                                future_prices[f"{days}d_return"] = ((future_price / current_price) - 1) * 100
                    
                    results.append({
                        "date": df_test.index[-1],
                        "score": score,
                        "price": current_price,
                        "forward_returns": future_prices,
                        "indicators": {
                            "rsi": score_result.get("rsi"),
                            "adx": score_result.get("adx"),
                            "cci": score_result.get("cci"),
                            "momentum": score_result.get("momentum"),
                        }
                    })
        except Exception as e:
            print(f"    Error at point {point_idx}: {e}")
            continue
    
    return results

def analyze_backtest_results(all_results):
    """Analyze backtest results and calculate statistics"""
    analysis = {
        "total_tests": 0,
        "score_distribution": defaultdict(int),
        "score_vs_returns": defaultdict(list),
        "high_score_performance": [],
        "low_score_performance": [],
        "predictive_power": {}
    }
    
    for symbol, results in all_results.items():
        if not results:
            continue
        
        for result in results:
            analysis["total_tests"] += 1
            score = result["score"]
            
            # Score distribution
            score_bucket = f"{int(score//2)*2}-{int(score//2)*2+2}"
            analysis["score_distribution"][score_bucket] += 1
            
            # Forward returns by score
            for days, return_pct in result.get("forward_returns", {}).items():
                if return_pct is not None:
                    analysis["score_vs_returns"][days].append({
                        "score": score,
                        "return": return_pct
                    })
            
            # High vs low score performance
            if score >= 6:
                for days, return_pct in result.get("forward_returns", {}).items():
                    if return_pct is not None:
                        analysis["high_score_performance"].append({
                            "days": days,
                            "return": return_pct
                        })
            elif score <= 2:
                for days, return_pct in result.get("forward_returns", {}).items():
                    if return_pct is not None:
                        analysis["low_score_performance"].append({
                            "days": days,
                            "return": return_pct
                        })
    
    # Calculate predictive power
    for days in ["5d", "10d", "20d", "30d"]:
        returns_data = analysis["score_vs_returns"].get(f"{days}_return", [])
        if len(returns_data) > 10:
            # Calculate correlation between score and returns
            scores = [d["score"] for d in returns_data]
            returns = [d["return"] for d in returns_data]
            
            if len(scores) == len(returns):
                correlation = pd.Series(scores).corr(pd.Series(returns))
                avg_return_high_score = pd.Series([d["return"] for d in returns_data if d["score"] >= 6]).mean() if any(d["score"] >= 6 for d in returns_data) else None
                avg_return_low_score = pd.Series([d["return"] for d in returns_data if d["score"] <= 2]).mean() if any(d["score"] <= 2 for d in returns_data) else None
                
                analysis["predictive_power"][days] = {
                    "correlation": correlation,
                    "avg_return_high_score": avg_return_high_score,
                    "avg_return_low_score": avg_return_low_score,
                    "sample_size": len(returns_data)
                }
    
    return analysis

def print_backtest_summary(analysis):
    """Print backtest summary"""
    print("\n" + "="*80)
    print("BACKTEST SUMMARY")
    print("="*80)
    
    print(f"\nTotal test points: {analysis['total_tests']}")
    
    print("\nScore Distribution:")
    for bucket in sorted(analysis["score_distribution"].keys()):
        count = analysis["score_distribution"][bucket]
        pct = (count / analysis["total_tests"]) * 100
        print(f"  {bucket}: {count} ({pct:.1f}%)")
    
    print("\nPredictive Power (Score vs Forward Returns):")
    for days, stats in analysis["predictive_power"].items():
        print(f"\n  {days} forward:")
        print(f"    Correlation: {stats['correlation']:.3f}")
        print(f"    Avg return (score >= 6): {stats['avg_return_high_score']:.2f}%" if stats['avg_return_high_score'] else "    Avg return (score >= 6): N/A")
        print(f"    Avg return (score <= 2): {stats['avg_return_low_score']:.2f}%" if stats['avg_return_low_score'] else "    Avg return (score <= 2): N/A")
        print(f"    Sample size: {stats['sample_size']}")
    
    # High vs Low score performance
    if analysis["high_score_performance"]:
        high_score_returns = [d["return"] for d in analysis["high_score_performance"]]
        print(f"\nHigh Score (>=6) Performance:")
        print(f"  Average return: {pd.Series(high_score_returns).mean():.2f}%")
        print(f"  Win rate: {(pd.Series(high_score_returns) > 0).sum() / len(high_score_returns) * 100:.1f}%")
        print(f"  Sample size: {len(high_score_returns)}")
    
    if analysis["low_score_performance"]:
        low_score_returns = [d["return"] for d in analysis["low_score_performance"]]
        print(f"\nLow Score (<=2) Performance:")
        print(f"  Average return: {pd.Series(low_score_returns).mean():.2f}%")
        print(f"  Win rate: {(pd.Series(low_score_returns) > 0).sum() / len(low_score_returns) * 100:.1f}%")
        print(f"  Sample size: {len(low_score_returns)}")

def main():
    """Run comprehensive backtest"""
    print("="*80)
    print("PREDICTIVE SCORING SYSTEM BACKTEST")
    print("="*80)
    print("\nTesting on diverse uncorrelated assets...")
    
    all_results = {}
    
    # Test each category
    for category, symbols in TEST_ASSETS.items():
        print(f"\n{category.upper()}:")
        for symbol in symbols:
            try:
                results = backtest_scoring(symbol, timeframe="1W")
                if results:
                    all_results[symbol] = results
                    print(f"  ✓ {symbol}: {len(results)} test points")
                else:
                    print(f"  ✗ {symbol}: Failed")
            except Exception as e:
                print(f"  ✗ {symbol}: Error - {e}")
    
    # Analyze results
    print("\n" + "="*80)
    print("ANALYZING RESULTS...")
    print("="*80)
    
    analysis = analyze_backtest_results(all_results)
    print_backtest_summary(analysis)
    
    # Save detailed results
    output_file = Path("backtest_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "detailed_results": {k: [
                {
                    "date": str(r["date"]),
                    "score": r["score"],
                    "price": r["price"],
                    "forward_returns": r["forward_returns"],
                    "indicators": r["indicators"]
                } for r in results
            ] for k, results in all_results.items()}
        }, f, indent=2, default=str)
    
    print(f"\n✓ Detailed results saved to {output_file}")
    
    return analysis

if __name__ == "__main__":
    main()
