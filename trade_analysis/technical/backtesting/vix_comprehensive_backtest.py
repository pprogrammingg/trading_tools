#!/usr/bin/env python3
"""
VIX Comprehensive Backtest
Tests whether explosive buy/sell opportunities are caught on different timeframes
with VIX adjustments considered
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from scoring.improved_scoring import improved_scoring
from indicators.market_context import get_market_context
from technical_analysis import load_symbols_config

def get_historical_vix(date):
    """Get VIX value for a specific historical date"""
    try:
        vix = yf.Ticker("^VIX")
        # Get data around the date (1 month window)
        start_date = date - timedelta(days=30)
        end_date = date + timedelta(days=5)
        vix_df = vix.history(start=start_date, end=end_date)
        
        if len(vix_df) == 0:
            return None
        
        # Find closest date
        vix_df = vix_df.sort_index()
        closest_date = vix_df.index[vix_df.index <= date]
        
        if len(closest_date) == 0:
            return None
        
        return float(vix_df.loc[closest_date[-1], 'Close'])
    except:
        return None

def get_historical_market_context(date):
    """Get market context for a specific historical date"""
    try:
        # Get SPX data
        spx = yf.Ticker("^GSPC")
        spx_df = spx.history(start=date - timedelta(days=365), end=date + timedelta(days=5))
        
        # Get Gold data
        gold = yf.Ticker("GC=F")
        gold_df = gold.history(start=date - timedelta(days=365), end=date + timedelta(days=5))
        
        # Get VIX data
        vix_value = get_historical_vix(date)
        
        if len(spx_df) == 0 or len(gold_df) == 0:
            return None
        
        # Align dates
        common_dates = spx_df.index.intersection(gold_df.index)
        if len(common_dates) == 0:
            return None
        
        spx_aligned = spx_df.loc[common_dates]['Close']
        gold_aligned = gold_df.loc[common_dates]['Close']
        
        # Calculate ratio
        ratio = spx_aligned / gold_aligned
        current_ratio = ratio.iloc[-1] if len(ratio) > 0 else None
        
        if current_ratio is None:
            return None
        
        # Calculate trend
        market_adjustment = 0.0
        market_bearish = False
        trend = 'neutral'
        
        if len(ratio) >= 20:
            ratio_ma20 = ratio.rolling(20).mean()
            ratio_slope = (ratio_ma20.iloc[-1] - ratio_ma20.iloc[-20]) / ratio_ma20.iloc[-20] * 100
            
            if ratio_slope < -5:
                trend = 'crashing'
                market_bearish = True
                market_adjustment = -2.0
            elif ratio_slope < -2:
                trend = 'declining'
                market_bearish = True
                market_adjustment = -1.0
            elif ratio_slope < 2:
                trend = 'neutral'
            else:
                trend = 'rising'
        
        # Check if near low
        if len(ratio) >= 60:
            recent_low = ratio.iloc[-60:].min()
            distance_from_low = ((current_ratio / recent_low) - 1) * 100
            if distance_from_low < 5:
                market_adjustment -= 1.0
                trend = 'near_low'
        
        # Process VIX
        vix_level = 'unknown'
        vix_trend = 'unknown'
        vix_adjustment = 0.0
        
        if vix_value is not None:
            if vix_value < 20:
                vix_level = 'low'
                vix_adjustment = 0.0
            elif vix_value < 29:
                vix_level = 'moderate'
                vix_adjustment = -0.5
            else:
                vix_level = 'high'
                vix_adjustment = -1.5
            
            # Get VIX trend (simplified - would need more data for full trend)
            # For now, just use level
        
        return {
            'spx_gold_ratio': float(current_ratio),
            'spx_gold_trend': trend,
            'market_bearish': market_bearish,
            'market_adjustment': market_adjustment,
            'vix': vix_value,
            'vix_level': vix_level,
            'vix_trend': vix_trend,
            'vix_adjustment': vix_adjustment,
        }
    except Exception as e:
        return None

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

def find_explosive_moves(symbol, category, timeframe, min_move_pct=30, lookback_periods=8, test_sells=False):
    """Find explosive moves (both up and down) for a specific timeframe"""
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
        
        # Find moves >min_move_pct within lookback_periods
        for i in range(lookback_periods, len(df_resampled) - 5):
            current_price = df_resampled['Close'].iloc[i]
            future_prices = df_resampled['Close'].iloc[i+1:i+lookback_periods+1]
            
            if len(future_prices) == 0:
                continue
            
            # Check for explosive moves UP (buy opportunities)
            max_future_price = future_prices.max()
            return_pct_up = ((max_future_price / current_price) - 1) * 100
            
            # Check for explosive moves DOWN (sell opportunities)
            min_future_price = future_prices.min()
            return_pct_down = ((min_future_price / current_price) - 1) * 100
            
            # Process explosive moves UP
            if return_pct_up >= min_move_pct:
                entry_date = df_resampled.index[i]
                peak_idx = future_prices.idxmax()
                peak_date = df_resampled.index[df_resampled.index.get_loc(peak_idx)]
                
                # Get historical market context
                market_context = get_historical_market_context(entry_date)
                
                # Calculate score at entry
                df_test = df_resampled.iloc[:i+1].copy()
                
                try:
                    # Score WITH VIX
                    score_result = improved_scoring(df_test, category, timeframe=timeframe, market_context=market_context)
                    score_with_vix = score_result.get('score', 0)
                    
                    # Score WITHOUT VIX (set vix_adjustment to 0)
                    market_context_no_vix = market_context.copy() if market_context else None
                    if market_context_no_vix:
                        market_context_no_vix['vix_adjustment'] = 0.0
                        # Also remove VIX multiplier effects
                    score_result_no_vix = improved_scoring(df_test, category, timeframe=timeframe, market_context=market_context_no_vix)
                    score_without_vix = score_result_no_vix.get('score', 0)
                    
                    indicators = score_result.get('indicators', {})
                    breakdown = score_result.get('breakdown', {})
                    
                    explosive_moves.append({
                        'symbol': symbol,
                        'category': category,
                        'timeframe': timeframe,
                        'move_type': 'buy',
                        'entry_date': entry_date.strftime('%Y-%m-%d'),
                        'entry_price': float(current_price),
                        'peak_date': peak_date.strftime('%Y-%m-%d'),
                        'peak_price': float(max_future_price),
                        'return_pct': float(return_pct_up),
                        'days_to_peak': (peak_date - entry_date).days,
                        'score_with_vix': float(score_with_vix),
                        'score_without_vix': float(score_without_vix),
                        'vix_at_entry': market_context.get('vix') if market_context else None,
                        'vix_level': market_context.get('vix_level', 'unknown') if market_context else 'unknown',
                        'rsi': indicators.get('rsi'),
                        'adx': indicators.get('adx'),
                        'breakdown': breakdown,
                        'has_explosive_bottom': 'explosive_bottom_base' in breakdown,
                        'has_continuation': 'trend_continuation_strong' in breakdown or 'trend_continuation_moderate' in breakdown,
                    })
                except Exception as e:
                    continue
            
            # Process explosive moves DOWN (sell opportunities)
            if test_sells and return_pct_down <= -min_move_pct:
                entry_date = df_resampled.index[i]
                bottom_idx = future_prices.idxmin()
                bottom_date = df_resampled.index[df_resampled.index.get_loc(bottom_idx)]
                
                # Get historical market context
                market_context = get_historical_market_context(entry_date)
                
                # Calculate score at entry
                df_test = df_resampled.iloc[:i+1].copy()
                
                try:
                    # Score WITH VIX
                    score_result = improved_scoring(df_test, category, timeframe=timeframe, market_context=market_context)
                    score_with_vix = score_result.get('score', 0)
                    
                    # Score WITHOUT VIX
                    market_context_no_vix = market_context.copy() if market_context else None
                    if market_context_no_vix:
                        market_context_no_vix['vix_adjustment'] = 0.0
                    score_result_no_vix = improved_scoring(df_test, category, timeframe=timeframe, market_context=market_context_no_vix)
                    score_without_vix = score_result_no_vix.get('score', 0)
                    
                    indicators = score_result.get('indicators', {})
                    breakdown = score_result.get('breakdown', {})
                    
                    explosive_moves.append({
                        'symbol': symbol,
                        'category': category,
                        'timeframe': timeframe,
                        'move_type': 'sell',
                        'entry_date': entry_date.strftime('%Y-%m-%d'),
                        'entry_price': float(current_price),
                        'bottom_date': bottom_date.strftime('%Y-%m-%d'),
                        'bottom_price': float(min_future_price),
                        'return_pct': float(return_pct_down),
                        'days_to_bottom': (bottom_date - entry_date).days,
                        'score_with_vix': float(score_with_vix),
                        'score_without_vix': float(score_without_vix),
                        'vix_at_entry': market_context.get('vix') if market_context else None,
                        'vix_level': market_context.get('vix_level', 'unknown') if market_context else 'unknown',
                        'rsi': indicators.get('rsi'),
                        'adx': indicators.get('adx'),
                        'breakdown': breakdown,
                    })
                except Exception as e:
                    continue
    except Exception as e:
        return []
    
    return explosive_moves

def main():
    """Run comprehensive VIX backtest"""
    print("\n" + "="*80)
    print("VIX COMPREHENSIVE BACKTEST")
    print("Testing explosive buy/sell opportunities with VIX adjustments")
    print("="*80 + "\n")
    
    # Load symbols
    symbols_config = load_symbols_config()
    
    # Timeframes to test
    timeframes = ["2D", "1W", "2W", "1M"]
    
    # Collect all explosive moves
    all_moves = []
    
    # Test each category
    for category, symbols in symbols_config.items():
        print(f"Testing {category} ({len(symbols)} symbols)...")
        
        for symbol in symbols[:10]:  # Limit to 10 per category for speed
            for timeframe in timeframes:
                moves = find_explosive_moves(symbol, category, timeframe, min_move_pct=30, test_sells=True)
                all_moves.extend(moves)
                if moves:
                    print(f"  {symbol} ({timeframe}): {len(moves)} moves")
    
    print(f"\nTotal explosive moves found: {len(all_moves)}")
    
    # Analyze results
    results = {
        'total_moves': len(all_moves),
        'by_timeframe': defaultdict(lambda: {'total': 0, 'buys': 0, 'sells': 0}),
        'by_vix_level': defaultdict(lambda: {'total': 0, 'high_score_with_vix': 0, 'high_score_without_vix': 0, 'caught_with_vix': 0, 'caught_without_vix': 0}),
        'by_timeframe_vix': defaultdict(lambda: defaultdict(lambda: {'total': 0, 'caught_with_vix': 0, 'caught_without_vix': 0})),
        'detailed_moves': all_moves,
    }
    
    # Analyze by timeframe
    for move in all_moves:
        tf = move['timeframe']
        results['by_timeframe'][tf]['total'] += 1
        if move['move_type'] == 'buy':
            results['by_timeframe'][tf]['buys'] += 1
        else:
            results['by_timeframe'][tf]['sells'] += 1
    
    # Analyze by VIX level
    for move in all_moves:
        vix_level = move.get('vix_level', 'unknown')
        if vix_level == 'unknown':
            continue
        
        results['by_vix_level'][vix_level]['total'] += 1
        
        # High score threshold (>=6)
        if move['score_with_vix'] >= 6:
            results['by_vix_level'][vix_level]['high_score_with_vix'] += 1
            results['by_vix_level'][vix_level]['caught_with_vix'] += 1
        
        if move['score_without_vix'] >= 6:
            results['by_vix_level'][vix_level]['high_score_without_vix'] += 1
            results['by_vix_level'][vix_level]['caught_without_vix'] += 1
    
    # Analyze by timeframe + VIX level
    for move in all_moves:
        tf = move['timeframe']
        vix_level = move.get('vix_level', 'unknown')
        if vix_level == 'unknown':
            continue
        
        results['by_timeframe_vix'][tf][vix_level]['total'] += 1
        
        if move['score_with_vix'] >= 6:
            results['by_timeframe_vix'][tf][vix_level]['caught_with_vix'] += 1
        
        if move['score_without_vix'] >= 6:
            results['by_timeframe_vix'][tf][vix_level]['caught_without_vix'] += 1
    
    # Print results
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80 + "\n")
    
    print("By Timeframe:")
    for tf in timeframes:
        data = results['by_timeframe'][tf]
        if data['total'] > 0:
            print(f"  {tf:3s}: {data['total']:4d} moves ({data['buys']:3d} buys, {data['sells']:3d} sells)")
    
    print("\nBy VIX Level (Buy Opportunities):")
    for vix_level in ['low', 'moderate', 'high']:
        data = results['by_vix_level'][vix_level]
        if data['total'] > 0:
            catch_rate_with = (data['caught_with_vix'] / data['total'] * 100) if data['total'] > 0 else 0
            catch_rate_without = (data['caught_without_vix'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {vix_level:8s}: {data['total']:4d} moves")
            print(f"    Caught WITH VIX:    {data['caught_with_vix']:3d} ({catch_rate_with:5.1f}%)")
            print(f"    Caught WITHOUT VIX: {data['caught_without_vix']:3d} ({catch_rate_without:5.1f}%)")
            print(f"    VIX Impact: {catch_rate_with - catch_rate_without:+.1f}%")
    
    print("\nBy Timeframe + VIX Level:")
    for tf in timeframes:
        print(f"\n  {tf}:")
        for vix_level in ['low', 'moderate', 'high']:
            data = results['by_timeframe_vix'][tf][vix_level]
            if data['total'] > 0:
                catch_rate_with = (data['caught_with_vix'] / data['total'] * 100) if data['total'] > 0 else 0
                catch_rate_without = (data['caught_without_vix'] / data['total'] * 100) if data['total'] > 0 else 0
                print(f"    {vix_level:8s}: {data['total']:3d} moves, "
                      f"With VIX: {catch_rate_with:5.1f}%, "
                      f"Without: {catch_rate_without:5.1f}%")
    
    # Save results
    output_file = 'vix_comprehensive_backtest_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
