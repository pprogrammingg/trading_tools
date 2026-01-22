#!/usr/bin/env python3
"""
Comprehensive Backtest Across All Categories
Tests both explosive bottoms and trend continuation signals
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
from technical_analysis import load_symbols_config

def find_explosive_moves(symbol, min_move_pct=30, lookback_weeks=8):
    """Find explosive moves in historical data"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="2y")
    
    if len(df) == 0:
        return []
    
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Resample to weekly
    df_weekly = df.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    df_weekly.columns = [col.capitalize() for col in df_weekly.columns]
    
    explosive_moves = []
    
    # Find moves >30% within lookback_weeks
    for i in range(lookback_weeks, len(df_weekly) - 5):
        current_price = df_weekly['Close'].iloc[i]
        future_prices = df_weekly['Close'].iloc[i+1:i+lookback_weeks+1]
        
        if len(future_prices) == 0:
            continue
        
        max_future_price = future_prices.max()
        return_pct = ((max_future_price / current_price) - 1) * 100
        
        if return_pct >= min_move_pct:
            entry_date = df_weekly.index[i]
            peak_idx = future_prices.idxmax()
            peak_date = df_weekly.index[df_weekly.index.get_loc(peak_idx)]
            
            # Calculate score at entry
            df_test = df_weekly.iloc[:i+1].copy()
            if len(df_test) < 50:
                continue
            
            try:
                # Determine category from symbol
                if 'USD' in symbol or symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
                    test_category = 'cryptocurrencies'
                else:
                    # Try to find category in config
                    test_category = category  # Use the category being tested
                
                score_result = improved_scoring(df_test, test_category)
                score = score_result.get('score', 0)
                indicators = score_result.get('indicators', {})
                breakdown = score_result.get('breakdown', {})
                
                explosive_moves.append({
                    'entry_date': entry_date,
                    'entry_price': current_price,
                    'peak_date': peak_date,
                    'peak_price': max_future_price,
                    'return_pct': return_pct,
                    'days_to_peak': (peak_date - entry_date).days,
                    'score_at_entry': score,
                    'rsi': indicators.get('rsi'),
                    'adx': indicators.get('adx'),
                    'momentum': indicators.get('momentum'),
                    'breakdown': breakdown
                })
            except:
                continue
    
    return explosive_moves

def backtest_category(category, symbols, max_symbols=5):
    """Backtest a category"""
    results = []
    
    for symbol in symbols[:max_symbols]:
        moves = find_explosive_moves(symbol)
        for move in moves:
            move['symbol'] = symbol
            move['category'] = category
            results.append(move)
    
    return results

def analyze_results(all_results):
    """Analyze backtest results"""
    analysis = {
        'total_moves': len(all_results),
        'by_category': defaultdict(lambda: {
            'total': 0,
            'high_score': 0,
            'good_score': 0,
            'ok_score': 0,
            'low_score': 0,
            'explosive_bottom': 0,
            'trend_continuation': 0,
        }),
        'by_score_level': {
            'high': {'count': 0, 'avg_return': []},
            'good': {'count': 0, 'avg_return': []},
            'ok': {'count': 0, 'avg_return': []},
            'low': {'count': 0, 'avg_return': []},
        }
    }
    
    for move in all_results:
        category = move['category']
        score = move['score_at_entry']
        return_pct = move['return_pct']
        breakdown = move.get('breakdown', {})
        
        analysis['by_category'][category]['total'] += 1
        
        # Check for explosive bottom
        if 'explosive_bottom_base' in breakdown:
            analysis['by_category'][category]['explosive_bottom'] += 1
        
        # Check for trend continuation
        if 'trend_continuation_strong' in breakdown or 'trend_continuation_very_strong' in breakdown:
            analysis['by_category'][category]['trend_continuation'] += 1
        
        # Score buckets
        if score >= 6:
            analysis['by_category'][category]['high_score'] += 1
            analysis['by_score_level']['high']['count'] += 1
            analysis['by_score_level']['high']['avg_return'].append(return_pct)
        elif score >= 4:
            analysis['by_category'][category]['good_score'] += 1
            analysis['by_score_level']['good']['count'] += 1
            analysis['by_score_level']['good']['avg_return'].append(return_pct)
        elif score >= 2:
            analysis['by_category'][category]['ok_score'] += 1
            analysis['by_score_level']['ok']['count'] += 1
            analysis['by_score_level']['ok']['avg_return'].append(return_pct)
        else:
            analysis['by_category'][category]['low_score'] += 1
            analysis['by_score_level']['low']['count'] += 1
            analysis['by_score_level']['low']['avg_return'].append(return_pct)
    
    # Calculate averages
    for level in analysis['by_score_level']:
        if analysis['by_score_level'][level]['avg_return']:
            analysis['by_score_level'][level]['avg_return'] = sum(analysis['by_score_level'][level]['avg_return']) / len(analysis['by_score_level'][level]['avg_return'])
        else:
            analysis['by_score_level'][level]['avg_return'] = 0
    
    return analysis

def main():
    """Run comprehensive backtest"""
    print("\n" + "="*80)
    print("COMPREHENSIVE CATEGORY BACKTEST")
    print("Testing Explosive Bottoms + Trend Continuation")
    print("="*80 + "\n")
    
    symbols_config = load_symbols_config()
    all_results = []
    
    # Test all categories
    for category, symbols in symbols_config.items():
        print(f"Testing {category}...")
        results = backtest_category(category, symbols, max_symbols=3)
        all_results.extend(results)
        print(f"  Found {len(results)} explosive moves")
    
    print(f"\nTotal explosive moves found: {len(all_results)}\n")
    
    # Analyze results
    analysis = analyze_results(all_results)
    
    # Print summary
    print("="*80)
    print("BACKTEST RESULTS SUMMARY")
    print("="*80 + "\n")
    
    print(f"Total Explosive Moves: {analysis['total_moves']}")
    print(f"\nBy Score Level:")
    for level, data in analysis['by_score_level'].items():
        if data['count'] > 0:
            pct = data['count'] / analysis['total_moves'] * 100
            avg_return = data['avg_return']
            print(f"  {level.capitalize()} (>=6/4/2): {data['count']} ({pct:.1f}%) - Avg Return: {avg_return:.1f}%")
    
    print(f"\nBy Category:")
    for category, data in sorted(analysis['by_category'].items()):
        if data['total'] > 0:
            high_pct = data['high_score'] / data['total'] * 100
            good_pct = data['good_score'] / data['total'] * 100
            explosive_pct = data['explosive_bottom'] / data['total'] * 100
            continuation_pct = data['trend_continuation'] / data['total'] * 100
            
            print(f"\n  {category}:")
            print(f"    Total: {data['total']}")
            print(f"    High Score: {data['high_score']} ({high_pct:.1f}%)")
            print(f"    Good Score: {data['good_score']} ({good_pct:.1f}%)")
            print(f"    Explosive Bottom: {data['explosive_bottom']} ({explosive_pct:.1f}%)")
            print(f"    Trend Continuation: {data['trend_continuation']} ({continuation_pct:.1f}%)")
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'analysis': analysis,
        'sample_moves': sorted(all_results, key=lambda x: x['return_pct'], reverse=True)[:20]
    }
    
    with open('comprehensive_category_backtest_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to comprehensive_category_backtest_results.json")

if __name__ == "__main__":
    main()
