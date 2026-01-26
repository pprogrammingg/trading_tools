#!/usr/bin/env python3
"""
Comprehensive Backtest: Seasonality and ISM Impact on Scoring
Tests how seasonality and ISM business cycle adjustments affect scores
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import yfinance as yf
import pandas as pd
from datetime import datetime
from collections import defaultdict
from scoring.improved_scoring import improved_scoring
from indicators.market_context import get_market_context
from indicators.seasonality import get_seasonal_adjustment_for_timeframe
from indicators.ism_business_cycle import get_ism_data, get_ism_adjustment_for_timeframe

def resample_to_timeframe(df, timeframe):
    """Resample data to specified timeframe"""
    if timeframe == "4H":
        return df.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "1D":
        return df.resample('D').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "2D":
        return df.resample('2D').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "1W":
        return df.resample('W').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "2W":
        return df.resample('2W').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "1M":
        return df.resample('ME').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "2M":
        return df.resample('2ME').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    elif timeframe == "3M":
        return df.resample('3ME').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
    return df

def backtest_seasonality_ism(symbol, category="cryptocurrencies", timeframes=None):
    """
    Backtest seasonality and ISM impact on scores
    
    Args:
        symbol: Symbol to test (e.g., "ETH-USD")
        category: Asset category
        timeframes: List of timeframes to test (default: all)
    """
    if timeframes is None:
        timeframes = ['1D', '2D', '1W', '2W', '1M', '2M', '3M']
    
    print(f"\n{'='*80}")
    print(f"BACKTESTING: {symbol} - Seasonality & ISM Impact")
    print(f"{'='*80}\n")
    
    # Download data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="max", interval="1d")
    
    if len(df) < 100:
        print(f"✗ Insufficient data: {len(df)} days")
        return None
    
    print(f"✓ Downloaded {len(df)} days of data")
    print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  Years: {(df.index[-1] - df.index[0]).days / 365.25:.2f}\n")
    
    results = {}
    market_context = get_market_context()
    ism_data = get_ism_data()
    
    # Get seasonality data (for crypto)
    seasonality_data = None
    if category == "cryptocurrencies":
        try:
            _, seasonality_data = get_seasonal_adjustment_for_timeframe(df, "1M")
        except:
            pass
    
    print(f"Market Context:")
    print(f"  SPX/Gold Trend: {market_context.get('spx_gold_trend', 'unknown')}")
    print(f"  Market Adjustment: {market_context.get('market_adjustment', 0.0):+.2f}")
    print(f"  VIX: {market_context.get('vix', 'N/A')}")
    print(f"  VIX Adjustment: {market_context.get('vix_adjustment', 0.0):+.2f}")
    print(f"  ISM PMI: {ism_data.get('ism_pmi', 'N/A') if ism_data else 'N/A'}")
    print(f"  ISM Phase: {ism_data.get('phase', 'unknown') if ism_data else 'unknown'}")
    if seasonality_data:
        print(f"  Current Month: {seasonality_data.get('current_month', 'N/A')}")
        print(f"  Seasonality Score: {seasonality_data.get('seasonality_score', 0):.1f}/100")
    print()
    
    # Test each timeframe
    for timeframe in timeframes:
        print(f"Testing {timeframe}...", end=" ")
        
        try:
            # Resample
            df_tf = resample_to_timeframe(df.copy(), timeframe)
            
            if len(df_tf) < 50:
                print("✗ (insufficient data)")
                continue
            
            # Test at multiple points
            test_points = []
            step = max(1, len(df_tf) // 20)
            for i in range(50, len(df_tf), step):
                test_points.append(i)
            
            if len(test_points) == 0:
                test_points = [len(df_tf) - 1]
            
            scores_with_seasonality = []
            scores_without_seasonality = []
            scores_with_ism = []
            scores_without_ism = []
            scores_full = []
            seasonality_adjustments = []
            ism_adjustments = []
            
            for point_idx in test_points:
                df_historical = df_tf.iloc[:point_idx+1]
                
                if len(df_historical) < 50:
                    continue
                
                # Score with all adjustments
                result_full = improved_scoring(
                    df_historical, category, timeframe=timeframe, 
                    market_context=market_context, original_daily_df=df
                )
                
                score_full = result_full.get('score', 0)
                breakdown = result_full.get('breakdown', {})
                
                seasonality_adj = breakdown.get('seasonality_adjustment', 0)
                ism_adj = breakdown.get('ism_adjustment', 0)
                
                scores_full.append(score_full)
                seasonality_adjustments.append(seasonality_adj)
                ism_adjustments.append(ism_adj)
                
                # Calculate scores without adjustments
                score_without_seasonality = score_full - seasonality_adj
                score_without_ism = score_full - ism_adj
                
                scores_without_seasonality.append(score_without_seasonality)
                scores_without_ism.append(score_without_ism)
                scores_with_seasonality.append(score_full - ism_adj)  # With seasonality, without ISM
                scores_with_ism.append(score_full - seasonality_adj)  # With ISM, without seasonality
            
            if len(scores_full) == 0:
                print("✗ (no valid test points)")
                continue
            
            # Calculate statistics
            avg_score_full = sum(scores_full) / len(scores_full)
            avg_score_no_season = sum(scores_without_seasonality) / len(scores_without_seasonality)
            avg_score_no_ism = sum(scores_without_ism) / len(scores_without_ism)
            avg_seasonality_adj = sum(seasonality_adjustments) / len(seasonality_adjustments)
            avg_ism_adj = sum(ism_adjustments) / len(ism_adjustments)
            
            impact_seasonality = avg_score_full - avg_score_no_season
            impact_ism = avg_score_full - avg_score_no_ism
            
            results[timeframe] = {
                'avg_score_full': round(avg_score_full, 2),
                'avg_score_no_seasonality': round(avg_score_no_season, 2),
                'avg_score_no_ism': round(avg_score_no_ism, 2),
                'avg_seasonality_adjustment': round(avg_seasonality_adj, 2),
                'avg_ism_adjustment': round(avg_ism_adj, 2),
                'seasonality_impact': round(impact_seasonality, 2),
                'ism_impact': round(impact_ism, 2),
                'test_points': len(scores_full),
            }
            
            print(f"✓ (Full: {avg_score_full:+.1f}, "
                  f"Seasonality Impact: {impact_seasonality:+.2f}, "
                  f"ISM Impact: {impact_ism:+.2f})")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    return {
        'symbol': symbol,
        'category': category,
        'data_years': (df.index[-1] - df.index[0]).days / 365.25,
        'market_context': {
            'spx_gold_trend': market_context.get('spx_gold_trend'),
            'market_adjustment': market_context.get('market_adjustment', 0.0),
            'vix': market_context.get('vix'),
            'vix_adjustment': market_context.get('vix_adjustment', 0.0),
            'ism_pmi': ism_data.get('ism_pmi') if ism_data else None,
            'ism_phase': ism_data.get('phase') if ism_data else None,
        },
        'seasonality': seasonality_data,
        'results': results,
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SEASONALITY & ISM IMPACT BACKTEST")
    print("="*80)
    
    # Test multiple crypto symbols
    symbols = ["ETH-USD", "BTC-USD", "SOL-USD"]
    
    all_results = {}
    for symbol in symbols:
        result = backtest_seasonality_ism(symbol, category="cryptocurrencies")
        if result:
            all_results[symbol] = result
    
    # Save results
    output_file = "backtesting/seasonality_ism_backtest_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print("RESULTS SUMMARY")
    print(f"{'='*80}\n")
    
    for symbol, result in all_results.items():
        print(f"{symbol}:")
        print(f"  ISM PMI: {result['market_context'].get('ism_pmi', 'N/A')}")
        print(f"  ISM Phase: {result['market_context'].get('ism_phase', 'unknown')}")
        if result.get('seasonality'):
            print(f"  Current Month: {result['seasonality'].get('current_month', 'N/A')}")
            print(f"  Seasonality Score: {result['seasonality'].get('seasonality_score', 0):.1f}/100")
        print()
        
        for tf, tf_result in result['results'].items():
            print(f"  {tf}:")
            print(f"    Full Score: {tf_result['avg_score_full']:+.2f}")
            print(f"    Seasonality Impact: {tf_result['seasonality_impact']:+.2f}")
            print(f"    ISM Impact: {tf_result['ism_impact']:+.2f}")
            print(f"    Avg Seasonality Adj: {tf_result['avg_seasonality_adjustment']:+.2f}")
            print(f"    Avg ISM Adj: {tf_result['avg_ism_adjustment']:+.2f}")
        print()
    
    print(f"✓ Results saved to {output_file}")
    print("="*80)
