#!/usr/bin/env python3
"""
Backtest explosive moves in BTC, ETH, SOL
Check if system would have predicted major moves
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from scoring.improved_scoring import improved_scoring

def find_explosive_moves(symbol, min_move_pct=30, lookback_days=60):
    """Find explosive moves in historical data"""
    print(f"\n{'='*80}")
    print(f"Analyzing {symbol}")
    print(f"{'='*80}")
    
    # Download 2 years of data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="2y")
    
    if len(df) == 0:
        print(f"No data for {symbol}")
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
    
    # Find moves >30% within 60 days
    for i in range(60, len(df_weekly) - 10):
        current_price = df_weekly['Close'].iloc[i]
        future_prices = df_weekly['Close'].iloc[i+1:i+9]  # ~8 weeks = 60 days
        
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
                score_result = improved_scoring(df_test, 'cryptocurrencies')
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
            except Exception as e:
                continue
    
    return explosive_moves

def analyze_crypto_explosive_moves():
    """Analyze BTC, ETH, SOL explosive moves"""
    
    cryptos = {
        'BTC-USD': 'Bitcoin',
        'ETH-USD': 'Ethereum',
        'SOL-USD': 'Solana'
    }
    
    all_results = {}
    
    for symbol, name in cryptos.items():
        moves = find_explosive_moves(symbol, min_move_pct=30)
        all_results[symbol] = {
            'name': name,
            'moves': moves
        }
        
        if moves:
            print(f"\n{name} - Found {len(moves)} explosive moves (>30% in 60 days)")
            
            # Show top moves
            moves_sorted = sorted(moves, key=lambda x: x['return_pct'], reverse=True)
            print(f"\nTop 5 Moves:")
            for i, move in enumerate(moves_sorted[:5], 1):
                print(f"\n{i}. Entry: {move['entry_date'].strftime('%Y-%m-%d')} @ ${move['entry_price']:,.2f}")
                print(f"   Peak: {move['peak_date'].strftime('%Y-%m-%d')} @ ${move['peak_price']:,.2f}")
                print(f"   Return: {move['return_pct']:.1f}% in {move['days_to_peak']} days")
                print(f"   Score at Entry: {move['score_at_entry']:.1f}")
                print(f"   RSI: {move['rsi']:.1f} | ADX: {move['adx']:.1f} | Momentum: {move['momentum']:.1f}%")
                
                # Show key signals
                breakdown = move['breakdown']
                if 'explosive_bottom_base' in breakdown:
                    print(f"   ✅ Explosive Bottom Detected: +{breakdown['explosive_bottom_base']:.1f}")
                if 'explosive_bottom_capitulation' in breakdown:
                    print(f"   ✅ Capitulation: +{breakdown['explosive_bottom_capitulation']:.1f}")
                if 'adx_rising_strong' in breakdown or 'adx_rising_from_low' in breakdown:
                    key = 'adx_rising_strong' if 'adx_rising_strong' in breakdown else 'adx_rising_from_low'
                    print(f"   ✅ ADX Rising: +{breakdown[key]:.1f}")
        else:
            print(f"\n{name} - No explosive moves found in recent 2 years")
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}\n")
    
    for symbol, data in all_results.items():
        moves = data['moves']
        if moves:
            high_score = sum(1 for m in moves if m['score_at_entry'] >= 6)
            good_score = sum(1 for m in moves if m['score_at_entry'] >= 4)
            total = len(moves)
            
            print(f"{data['name']}:")
            print(f"  Total Explosive Moves: {total}")
            print(f"  High Score (>=6): {high_score} ({high_score/total*100:.1f}%)")
            print(f"  Good Score (>=4): {good_score} ({good_score/total*100:.1f}%)")
            
            avg_return_high = sum(m['return_pct'] for m in moves if m['score_at_entry'] >= 6) / high_score if high_score > 0 else 0
            avg_return_all = sum(m['return_pct'] for m in moves) / total
            
            print(f"  Avg Return (High Score): {avg_return_high:.1f}%")
            print(f"  Avg Return (All Moves): {avg_return_all:.1f}%")
            print()

if __name__ == "__main__":
    analyze_crypto_explosive_moves()
