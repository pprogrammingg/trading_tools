#!/usr/bin/env python3
"""
Full Category Backtest with Trend Continuation
Tests all categories with improved continuation signals
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

def find_explosive_moves(symbol, category, min_move_pct=30, lookback_weeks=8):
    """Find explosive moves in historical data"""
    try:
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
                    score_result = improved_scoring(df_test, category)
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
                        'has_continuation': 'trend_continuation_strong' in breakdown or 'trend_continuation_moderate' in breakdown or 'trend_continuation_very_strong' in breakdown,
                    })
                except:
                    continue
    except:
        return []
    
    return explosive_moves

def main():
    """Run full category backtest"""
    print("\n" + "="*80)
    print("FULL CATEGORY BACKTEST - Explosive Bottoms + Trend Continuation")
    print("="*80 + "\n")
    
    symbols_config = load_symbols_config()
    all_results = []
    
    # Test all categories
    for category, symbols in symbols_config.items():
        print(f"Testing {category} ({len(symbols)} symbols)...")
        category_results = []
        
        for symbol in symbols[:5]:  # Test up to 5 symbols per category
            moves = find_explosive_moves(symbol, category)
            for move in moves:
                move['symbol'] = symbol
                move['category'] = category
                category_results.append(move)
        
        all_results.extend(category_results)
        print(f"  Found {len(category_results)} explosive moves")
    
    print(f"\nTotal explosive moves found: {len(all_results)}\n")
    
    # Analyze results
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
            'avg_return_high': [],
            'avg_return_good': [],
        }),
        'by_score_level': {
            'high': {'count': 0, 'returns': []},
            'good': {'count': 0, 'returns': []},
            'ok': {'count': 0, 'returns': []},
            'low': {'count': 0, 'returns': []},
        }
    }
    
    for move in all_results:
        category = move['category']
        score = move['score_at_entry']
        return_pct = move['return_pct']
        
        analysis['by_category'][category]['total'] += 1
        
        if move.get('has_explosive_bottom'):
            analysis['by_category'][category]['explosive_bottom'] += 1
        
        if move.get('has_continuation'):
            analysis['by_category'][category]['trend_continuation'] += 1
        
        # Score buckets
        if score >= 6:
            analysis['by_category'][category]['high_score'] += 1
            analysis['by_category'][category]['avg_return_high'].append(return_pct)
            analysis['by_score_level']['high']['count'] += 1
            analysis['by_score_level']['high']['returns'].append(return_pct)
        elif score >= 4:
            analysis['by_category'][category]['good_score'] += 1
            analysis['by_category'][category]['avg_return_good'].append(return_pct)
            analysis['by_score_level']['good']['count'] += 1
            analysis['by_score_level']['good']['returns'].append(return_pct)
        elif score >= 2:
            analysis['by_category'][category]['ok_score'] += 1
            analysis['by_score_level']['ok']['count'] += 1
            analysis['by_score_level']['ok']['returns'].append(return_pct)
        else:
            analysis['by_category'][category]['low_score'] += 1
            analysis['by_score_level']['low']['count'] += 1
            analysis['by_score_level']['low']['returns'].append(return_pct)
    
    # Calculate averages
    for level in analysis['by_score_level']:
        if analysis['by_score_level'][level]['returns']:
            analysis['by_score_level'][level]['avg_return'] = sum(analysis['by_score_level'][level]['returns']) / len(analysis['by_score_level'][level]['returns'])
        else:
            analysis['by_score_level'][level]['avg_return'] = 0
    
    for category in analysis['by_category']:
        data = analysis['by_category'][category]
        if data['avg_return_high']:
            data['avg_return_high'] = sum(data['avg_return_high']) / len(data['avg_return_high'])
        else:
            data['avg_return_high'] = 0
        if data['avg_return_good']:
            data['avg_return_good'] = sum(data['avg_return_good']) / len(data['avg_return_good'])
        else:
            data['avg_return_good'] = 0
    
    # Print summary
    print("="*80)
    print("BACKTEST RESULTS SUMMARY")
    print("="*80 + "\n")
    
    print(f"Total Explosive Moves: {analysis['total_moves']}")
    print(f"\nBy Score Level:")
    for level, data in analysis['by_score_level'].items():
        if data['count'] > 0:
            pct = data['count'] / analysis['total_moves'] * 100
            avg_return = data.get('avg_return', 0)
            print(f"  {level.capitalize()} (>=6/4/2/<2): {data['count']} ({pct:.1f}%) - Avg Return: {avg_return:.1f}%")
    
    print(f"\nBy Category:")
    for category, data in sorted(analysis['by_category'].items()):
        if data['total'] > 0:
            high_pct = data['high_score'] / data['total'] * 100
            good_pct = data['good_score'] / data['total'] * 100
            explosive_pct = data['explosive_bottom'] / data['total'] * 100
            continuation_pct = data['trend_continuation'] / data['total'] * 100
            
            print(f"\n  {category}:")
            print(f"    Total: {data['total']}")
            print(f"    High Score (>=6): {data['high_score']} ({high_pct:.1f}%)")
            print(f"    Good Score (>=4): {data['good_score']} ({good_pct:.1f}%)")
            print(f"    Explosive Bottom: {data['explosive_bottom']} ({explosive_pct:.1f}%)")
            print(f"    Trend Continuation: {data['trend_continuation']} ({continuation_pct:.1f}%)")
            if data['avg_return_high'] > 0:
                print(f"    Avg Return (High Score): {data['avg_return_high']:.1f}%")
            if data['avg_return_good'] > 0:
                print(f"    Avg Return (Good Score): {data['avg_return_good']:.1f}%")
    
    # Show top opportunities
    print(f"\n{'='*80}")
    print("TOP 10 OPPORTUNITIES")
    print(f"{'='*80}\n")
    
    top_moves = sorted(all_results, key=lambda x: x['return_pct'], reverse=True)[:10]
    for i, move in enumerate(top_moves, 1):
        print(f"{i}. {move['symbol']} ({move['category']})")
        print(f"   Entry: {move['entry_date'].strftime('%Y-%m-%d')} @ ${move['entry_price']:,.2f}")
        print(f"   Peak: {move['peak_date'].strftime('%Y-%m-%d')} @ ${move['peak_price']:,.2f}")
        print(f"   Return: {move['return_pct']:.1f}% ({move['peak_price']/move['entry_price']:.1f}x) in {move['days_to_peak']} days")
        print(f"   Score: {move['score_at_entry']:.1f}")
        if move.get('has_explosive_bottom'):
            print(f"   ✅ Explosive Bottom Detected")
        if move.get('has_continuation'):
            print(f"   ✅ Trend Continuation Detected")
        print()
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'analysis': {
            'total_moves': analysis['total_moves'],
            'by_category': dict(analysis['by_category']),
            'by_score_level': {
                k: {'count': v['count'], 'avg_return': v.get('avg_return', 0)}
                for k, v in analysis['by_score_level'].items()
            }
        },
        'top_opportunities': top_moves[:20]
    }
    
    with open('full_category_backtest_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"✓ Results saved to full_category_backtest_results.json")

if __name__ == "__main__":
    main()
