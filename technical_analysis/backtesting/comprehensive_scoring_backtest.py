#!/usr/bin/env python3
"""
Comprehensive Scoring Backtest
Tests improved scoring with:
1. Timeframe-specific scoring
2. Market context (SPX/Gold ratio)
3. Bottoming structure detection
4. Elliott Wave analysis
5. Continuation signals
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
from technical_analysis import load_symbols_config

def resample_to_timeframe(df, timeframe):
    """Resample data to specified timeframe"""
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    if timeframe == "2D":
        df_resampled = df.resample('2D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == "1W":
        df_resampled = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == "2W":
        df_resampled = df.resample('2W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == "1M":
        df_resampled = df.resample('ME').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    else:
        df_resampled = df
    
    df_resampled.columns = [col.capitalize() for col in df_resampled.columns]
    return df_resampled

def find_explosive_moves(symbol, category, timeframe, min_move_pct=30, lookback_periods=8):
    """Find explosive moves for a specific timeframe"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        
        if len(df) == 0:
            return []
        
        # Resample to timeframe
        df_resampled = resample_to_timeframe(df, timeframe)
        
        if len(df_resampled) < 50:
            return []
        
        explosive_moves = []
        
        # Get market context (use current for all historical points)
        market_context = get_market_context()
        
        # Find moves >30% within lookback_periods
        for i in range(lookback_periods, len(df_resampled) - 5):
            current_price = df_resampled['Close'].iloc[i]
            future_prices = df_resampled['Close'].iloc[i+1:i+lookback_periods+1]
            
            if len(future_prices) == 0:
                continue
            
            max_future_price = future_prices.max()
            return_pct = ((max_future_price / current_price) - 1) * 100
            
            if return_pct >= min_move_pct:
                entry_date = df_resampled.index[i]
                peak_idx = future_prices.idxmax()
                peak_date = df_resampled.index[df_resampled.index.get_loc(peak_idx)]
                
                # Calculate score at entry
                df_test = df_resampled.iloc[:i+1].copy()
                
                try:
                    score_result = improved_scoring(df_test, category, timeframe=timeframe, market_context=market_context)
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
                        'breakdown': breakdown,
                        'has_explosive_bottom': 'explosive_bottom_base' in breakdown,
                        'has_continuation': 'trend_continuation_strong' in breakdown or 'trend_continuation_moderate' in breakdown,
                        'has_bottoming_pattern': 'bottoming_pattern' in breakdown,
                        'has_elliott_wave': 'elliott_wave_correction' in breakdown,
                    })
                except:
                    continue
    except:
        return []
    
    return explosive_moves

def main():
    """Run comprehensive backtest"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SCORING BACKTEST")
    print("Testing: Timeframe-Specific + Market Context + Bottoming + Elliott Wave")
    print("="*80 + "\n")
    
    # Get market context
    print("Getting market context (SPX/Gold ratio)...")
    market_context = get_market_context()
    print(f"  SPX/Gold Ratio: {market_context.get('spx_gold_ratio', 'N/A')}")
    print(f"  Trend: {market_context.get('spx_gold_trend', 'N/A')}")
    print(f"  Market Adjustment: {market_context.get('market_adjustment', 0.0):.1f}")
    print()
    
    symbols_config = load_symbols_config()
    timeframes = ["2D", "1W", "2W", "1M"]
    
    all_results = defaultdict(lambda: defaultdict(list))
    
    # Test each timeframe
    for timeframe in timeframes:
        print(f"Testing {timeframe} timeframe...")
        
        for category, symbols in symbols_config.items():
            for symbol in symbols[:3]:  # Test 3 symbols per category
                moves = find_explosive_moves(symbol, category, timeframe)
                for move in moves:
                    move['symbol'] = symbol
                    move['category'] = category
                    move['timeframe'] = timeframe
                    all_results[timeframe][category].append(move)
        
        total = sum(len(moves) for moves in all_results[timeframe].values())
        print(f"  Found {total} explosive moves")
    
    # Analyze results
    print(f"\n{'='*80}")
    print("BACKTEST RESULTS - IMPROVED SCORING")
    print(f"{'='*80}\n")
    
    for timeframe in timeframes:
        timeframe_moves = []
        for category_moves in all_results[timeframe].values():
            timeframe_moves.extend(category_moves)
        
        if len(timeframe_moves) == 0:
            print(f"{timeframe}: No moves found")
            continue
        
        high_score = sum(1 for m in timeframe_moves if m['score_at_entry'] >= 6)
        good_score = sum(1 for m in timeframe_moves if m['score_at_entry'] >= 4)
        ok_score = sum(1 for m in timeframe_moves if m['score_at_entry'] >= 2)
        
        explosive_bottom = sum(1 for m in timeframe_moves if m.get('has_explosive_bottom'))
        continuation = sum(1 for m in timeframe_moves if m.get('has_continuation'))
        bottoming_pattern = sum(1 for m in timeframe_moves if m.get('has_bottoming_pattern'))
        elliott_wave = sum(1 for m in timeframe_moves if m.get('has_elliott_wave'))
        
        avg_return_high = sum(m['return_pct'] for m in timeframe_moves if m['score_at_entry'] >= 6) / high_score if high_score > 0 else 0
        avg_return_all = sum(m['return_pct'] for m in timeframe_moves) / len(timeframe_moves)
        
        print(f"{timeframe}:")
        print(f"  Total Moves: {len(timeframe_moves)}")
        print(f"  High Score (>=6): {high_score} ({high_score/len(timeframe_moves)*100:.1f}%)")
        print(f"  Good Score (>=4): {good_score} ({good_score/len(timeframe_moves)*100:.1f}%)")
        print(f"  OK Score (>=2): {ok_score} ({ok_score/len(timeframe_moves)*100:.1f}%)")
        print(f"  Explosive Bottom: {explosive_bottom} ({explosive_bottom/len(timeframe_moves)*100:.1f}%)")
        print(f"  Trend Continuation: {continuation} ({continuation/len(timeframe_moves)*100:.1f}%)")
        print(f"  Bottoming Pattern: {bottoming_pattern} ({bottoming_pattern/len(timeframe_moves)*100:.1f}%)")
        print(f"  Elliott Wave: {elliott_wave} ({elliott_wave/len(timeframe_moves)*100:.1f}%)")
        print(f"  Avg Return (High Score): {avg_return_high:.1f}%")
        print(f"  Avg Return (All): {avg_return_all:.1f}%")
        print()
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'market_context': market_context,
        'timeframe_results': {
            tf: {
                'total_moves': sum(len(moves) for moves in all_results[tf].values()),
                'high_score_count': sum(1 for moves in all_results[tf].values() for m in moves if m['score_at_entry'] >= 6),
                'good_score_count': sum(1 for moves in all_results[tf].values() for m in moves if m['score_at_entry'] >= 4),
            }
            for tf in timeframes
        }
    }
    
    with open('comprehensive_scoring_backtest_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"✓ Results saved to comprehensive_scoring_backtest_results.json")

if __name__ == "__main__":
    main()
