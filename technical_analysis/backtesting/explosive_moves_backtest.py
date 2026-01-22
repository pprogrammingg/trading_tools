#!/usr/bin/env python3
"""
Comprehensive Backtest: PI Indicator, Hash Ribbon, and Scoring System
Tests ability to identify explosive moves and validates scoring system
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import sys

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from technical_analysis import compute_indicators_tv, load_symbols_config
except ImportError:
    # Fallback if running from different directory
    import importlib.util
    spec = importlib.util.spec_from_file_location("technical_analysis", "technical_analysis.py")
    technical_analysis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(technical_analysis)
    compute_indicators_tv = technical_analysis.compute_indicators_tv
    load_symbols_config = technical_analysis.load_symbols_config

try:
    from advanced_indicators import (
        calculate_price_intensity, detect_explosive_move_setup,
        get_hash_ribbon_signal_for_stock, calculate_hash_ribbon
    )
except ImportError:
    # Import directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("advanced_indicators", "advanced_indicators.py")
    advanced_indicators = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(advanced_indicators)
    calculate_price_intensity = advanced_indicators.calculate_price_intensity
    detect_explosive_move_setup = advanced_indicators.detect_explosive_move_setup
    get_hash_ribbon_signal_for_stock = advanced_indicators.get_hash_ribbon_signal_for_stock
    calculate_hash_ribbon = advanced_indicators.calculate_hash_ribbon


def download_data(symbol, period="2y"):
    """Download historical data"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if len(df) == 0:
            return None
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        return df
    except Exception as e:
        return None


def resample_to_weekly(df):
    """Resample to weekly timeframe"""
    df_resampled = df.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    df_resampled.columns = [col.capitalize() for col in df_resampled.columns]
    return df_resampled


def find_explosive_moves(df, min_move_pct=30, lookback_days=60):
    """
    Find historical explosive moves (price increases > min_move_pct within lookback_days)
    Returns list of (date, entry_price, peak_price, peak_date, return_pct)
    """
    explosive_moves = []
    
    for i in range(lookback_days, len(df) - 10):
        current_price = df['close'].iloc[i]
        future_prices = df['close'].iloc[i+1:i+lookback_days+1]
        
        if len(future_prices) == 0:
            continue
        
        max_future_price = future_prices.max()
        max_future_idx = future_prices.idxmax()
        return_pct = ((max_future_price / current_price) - 1) * 100
        
        if return_pct >= min_move_pct:
            explosive_moves.append({
                'entry_date': df.index[i],
                'entry_price': current_price,
                'peak_date': max_future_idx,
                'peak_price': max_future_price,
                'return_pct': return_pct,
                'days_to_peak': (max_future_idx - df.index[i]).days
            })
    
    return explosive_moves


def backtest_symbol(symbol, category, min_move_pct=30):
    """
    Backtest a single symbol to find:
    1. Historical explosive moves
    2. What the score was at entry points
    3. Whether PI/Hash Ribbon would have predicted them
    """
    print(f"\n  Testing {symbol} ({category})...")
    
    # Download data
    df = download_data(symbol, period="2y")
    if df is None or len(df) < 100:
        print(f"    ✗ Insufficient data")
        return None
    
    # Resample to weekly
    df_weekly = resample_to_weekly(df)
    if len(df_weekly) < 50:
        print(f"    ✗ Insufficient data after resampling")
        return None
    
    # Find explosive moves
    explosive_moves = find_explosive_moves(df_weekly, min_move_pct=min_move_pct)
    
    if len(explosive_moves) == 0:
        print(f"    ✗ No explosive moves found (>{min_move_pct}% within 60 days)")
        return None
    
    print(f"    ✓ Found {len(explosive_moves)} explosive move(s)")
    
    results = []
    
    for move in explosive_moves:
        entry_date = move['entry_date']
        
        # Find the index in weekly data
        entry_idx = df_weekly.index.get_loc(entry_date)
        if entry_idx < 50:  # Need enough history for indicators
            continue
        
        # Get data up to entry point
        df_test = df_weekly.iloc[:entry_idx+1].copy()
        
        try:
            # Calculate score at entry point
            score_result = compute_indicators_tv(df_test, category=category)
            score = score_result.get("score", 0)
            
            # Calculate PI indicator
            pi_value = None
            if len(df_test) >= 28:
                pi_series = calculate_price_intensity(df_test['Close'], df_test['Volume'], period=14)
                if pi_series is not None and len(pi_series) > 0:
                    pi_value = pi_series.iloc[-1] if not pd.isna(pi_series.iloc[-1]) else None
            
            # Check Hash Ribbon signal (for BTC) or adapted version
            hash_ribbon_signal = False
            if symbol == "BTC-USD":
                signal_series, _ = calculate_hash_ribbon("BTC-USD", period="2y")
                if signal_series is not None and len(signal_series) > 0:
                    # Find signal near entry date
                    hash_ribbon_signal = signal_series.iloc[-1] if len(signal_series) > 0 else False
            else:
                signal_series, _ = get_hash_ribbon_signal_for_stock(symbol, period="2y")
                if signal_series is not None and len(signal_series) > 0:
                    hash_ribbon_signal = signal_series.iloc[-1] if len(signal_series) > 0 else False
            
            # Check explosive move setup
            explosive_setup = detect_explosive_move_setup(
                df_test['Close'], df_test['Volume'], pi_value
            )
            
            results.append({
                'symbol': symbol,
                'category': category,
                'entry_date': str(entry_date),
                'entry_price': move['entry_price'],
                'peak_date': str(move['peak_date']),
                'peak_price': move['peak_price'],
                'return_pct': move['return_pct'],
                'days_to_peak': move['days_to_peak'],
                'score_at_entry': score,
                'pi_value': pi_value,
                'hash_ribbon_signal': hash_ribbon_signal,
                'explosive_setup': explosive_setup,
                'indicators': {
                    'rsi': score_result.get('rsi'),
                    'adx': score_result.get('adx'),
                    'cci': score_result.get('cci'),
                    'momentum': score_result.get('momentum'),
                },
                'score_breakdown': score_result.get('score_breakdown', {})
            })
        except Exception as e:
            print(f"    Error analyzing move at {entry_date}: {e}")
            continue
    
    return results


def analyze_results(all_results):
    """Analyze backtest results"""
    analysis = {
        'total_explosive_moves': 0,
        'moves_with_high_score': 0,  # Score >= 6
        'moves_with_good_score': 0,  # Score >= 4
        'moves_with_pi_signal': 0,  # PI > 70
        'moves_with_hash_ribbon': 0,
        'moves_with_explosive_setup': 0,
        'avg_return_high_score': [],
        'avg_return_good_score': [],
        'avg_return_low_score': [],
        'best_opportunities': []
    }
    
    for result_list in all_results.values():
        if not result_list:
            continue
        
        for move in result_list:
            analysis['total_explosive_moves'] += 1
            
            score = move['score_at_entry']
            return_pct = move['return_pct']
            
            if score >= 6:
                analysis['moves_with_high_score'] += 1
                analysis['avg_return_high_score'].append(return_pct)
            elif score >= 4:
                analysis['moves_with_good_score'] += 1
                analysis['avg_return_good_score'].append(return_pct)
            else:
                analysis['avg_return_low_score'].append(return_pct)
            
            if move.get('pi_value') and move['pi_value'] > 70:
                analysis['moves_with_pi_signal'] += 1
            
            if move.get('hash_ribbon_signal'):
                analysis['moves_with_hash_ribbon'] += 1
            
            if move.get('explosive_setup'):
                analysis['moves_with_explosive_setup'] += 1
            
            # Track best opportunities (high score + high return)
            if score >= 4:
                analysis['best_opportunities'].append(move)
    
    # Sort best opportunities by return
    analysis['best_opportunities'].sort(key=lambda x: x['return_pct'], reverse=True)
    
    return analysis


def print_analysis(analysis):
    """Print comprehensive analysis"""
    print("\n" + "="*80)
    print("EXPLOSIVE MOVES BACKTEST ANALYSIS")
    print("="*80)
    
    total = analysis['total_explosive_moves']
    if total == 0:
        print("\nNo explosive moves found in test period.")
        return
    
    print(f"\nTotal Explosive Moves Found: {total}")
    print(f"  Moves with High Score (>=6): {analysis['moves_with_high_score']} ({analysis['moves_with_high_score']/total*100:.1f}%)")
    print(f"  Moves with Good Score (>=4): {analysis['moves_with_good_score']} ({analysis['moves_with_good_score']/total*100:.1f}%)")
    print(f"  Moves with PI Signal (>70): {analysis['moves_with_pi_signal']} ({analysis['moves_with_pi_signal']/total*100:.1f}%)")
    print(f"  Moves with Hash Ribbon Signal: {analysis['moves_with_hash_ribbon']} ({analysis['moves_with_hash_ribbon']/total*100:.1f}%)")
    print(f"  Moves with Explosive Setup: {analysis['moves_with_explosive_setup']} ({analysis['moves_with_explosive_setup']/total*100:.1f}%)")
    
    if analysis['avg_return_high_score']:
        print(f"\nAverage Return - High Score (>=6): {np.mean(analysis['avg_return_high_score']):.2f}%")
    if analysis['avg_return_good_score']:
        print(f"Average Return - Good Score (>=4): {np.mean(analysis['avg_return_good_score']):.2f}%")
    if analysis['avg_return_low_score']:
        print(f"Average Return - Low Score (<4): {np.mean(analysis['avg_return_low_score']):.2f}%")
    
    print("\n" + "="*80)
    print("TOP 10 BEST BUY OPPORTUNITIES (High Score + High Return)")
    print("="*80)
    
    for i, opp in enumerate(analysis['best_opportunities'][:10], 1):
        print(f"\n{i}. {opp['symbol']} ({opp['category']})")
        print(f"   Entry Date: {opp['entry_date']}")
        print(f"   Entry Price: ${opp['entry_price']:.2f}")
        print(f"   Peak Price: ${opp['peak_price']:.2f} (on {opp['peak_date']})")
        print(f"   Return: {opp['return_pct']:.2f}% in {opp['days_to_peak']} days")
        print(f"   Score at Entry: {opp['score_at_entry']:.1f}")
        print(f"   PI Value: {opp.get('pi_value', 'N/A')}")
        print(f"   Hash Ribbon: {'Yes' if opp.get('hash_ribbon_signal') else 'No'}")
        print(f"   Explosive Setup: {'Yes' if opp.get('explosive_setup') else 'No'}")
        print(f"   Key Indicators: RSI={opp['indicators'].get('rsi', 'N/A')}, ADX={opp['indicators'].get('adx', 'N/A')}")


def main():
    """Run comprehensive backtest"""
    print("="*80)
    print("EXPLOSIVE MOVES BACKTEST")
    print("Testing PI Indicator, Hash Ribbon, and Scoring System")
    print("="*80)
    
    # Load symbols
    symbols_config = load_symbols_config()
    
    all_results = {}
    
    # Test one stock per category (best scoring stock)
    for category, symbols in symbols_config.items():
        if len(symbols) == 0:
            continue
        
        print(f"\n{category.upper()}:")
        # Test first few symbols in each category
        for symbol in symbols[:3]:  # Test up to 3 per category
            results = backtest_symbol(symbol, category, min_move_pct=30)
            if results:
                all_results[(symbol, category)] = results
    
    # Analyze results
    analysis = analyze_results(all_results)
    print_analysis(analysis)
    
    # Save results
    output_file = Path("explosive_moves_backtest_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'total_explosive_moves': analysis['total_explosive_moves'],
                'moves_with_high_score': analysis['moves_with_high_score'],
                'moves_with_good_score': analysis['moves_with_good_score'],
                'moves_with_pi_signal': analysis['moves_with_pi_signal'],
                'moves_with_hash_ribbon': analysis['moves_with_hash_ribbon'],
                'avg_return_high_score': np.mean(analysis['avg_return_high_score']) if analysis['avg_return_high_score'] else None,
                'avg_return_good_score': np.mean(analysis['avg_return_good_score']) if analysis['avg_return_good_score'] else None,
            },
            'best_opportunities': analysis['best_opportunities'][:20],
            'all_moves': [
                move for results in all_results.values() for move in results
            ]
        }, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to {output_file}")
    
    return analysis


if __name__ == "__main__":
    main()
