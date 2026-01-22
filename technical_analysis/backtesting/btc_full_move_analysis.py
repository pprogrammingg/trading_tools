#!/usr/bin/env python3
"""
Analyze Bitcoin's full 7-8x move from Nov 2022 ($16K) to $120-130K
Fine-tune system to catch these massive moves
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scoring.improved_scoring import improved_scoring, calculate_price_intensity
from indicators.indicators_common import calculate_adx

def analyze_btc_full_move():
    """Analyze BTC's full move from Nov 2022 to $120-130K"""
    
    print("\n" + "="*80)
    print("BITCOIN FULL MOVE ANALYSIS: Nov 2022 ($16K) → $120-130K (7-8x)")
    print("="*80 + "\n")
    
    # Download BTC data from Nov 2022 to present
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(start="2020-11-01", end="2025-01-20")
    
    if len(df) == 0:
        print("No data available")
        return
    
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
    
    # Find the bottom (Nov 2022)
    nov_2022 = df_weekly[(df_weekly.index >= '2022-11-01') & (df_weekly.index < '2022-12-01')]
    
    if len(nov_2022) == 0:
        print("No November 2022 data found")
        return
    
    bottom_idx = nov_2022['Close'].idxmin()
    bottom_price = nov_2022['Close'].min()
    bottom_date = bottom_idx
    
    print(f"📉 BTC Bottom Found:")
    print(f"   Date: {bottom_date.strftime('%Y-%m-%d')}")
    print(f"   Price: ${bottom_price:,.2f}")
    
    # Find the peak ($120-130K range)
    recent_data = df_weekly[df_weekly.index >= '2024-01-01']
    if len(recent_data) > 0:
        peak_idx = recent_data['Close'].idxmax()
        peak_price = recent_data['Close'].max()
        peak_date = peak_idx
        
        print(f"\n📈 BTC Peak Found:")
        print(f"   Date: {peak_date.strftime('%Y-%m-%d')}")
        print(f"   Price: ${peak_price:,.2f}")
        
        return_pct = ((peak_price / bottom_price) - 1) * 100
        days_to_peak = (peak_date - bottom_date).days
        years_to_peak = days_to_peak / 365.25
        
        print(f"\n🚀 FULL MOVE:")
        print(f"   Return: {return_pct:.1f}% ({peak_price/bottom_price:.1f}x)")
        print(f"   Duration: {days_to_peak} days ({years_to_peak:.2f} years)")
    
    # Analyze multiple entry points along the way
    print(f"\n{'='*80}")
    print("ANALYZING ENTRY POINTS ALONG THE MOVE")
    print(f"{'='*80}\n")
    
    entry_points = []
    
    # Entry point 1: Bottom (Nov 2022)
    entry_idx = df_weekly.index.get_loc(bottom_date)
    df_entry = df_weekly.iloc[:entry_idx+1].copy()
    
    if len(df_entry) >= 50:
        try:
            score_result = improved_scoring(df_entry, 'cryptocurrencies')
            entry_points.append({
                'date': bottom_date,
                'price': bottom_price,
                'score': score_result.get('score', 0),
                'indicators': score_result.get('indicators', {}),
                'breakdown': score_result.get('breakdown', {})
            })
        except:
            pass
    
    # Entry points every 3 months after bottom
    for months_after in [3, 6, 9, 12, 18, 24]:
        target_date = bottom_date + pd.DateOffset(months=months_after)
        if target_date in df_weekly.index:
            entry_idx = df_weekly.index.get_loc(target_date)
            if entry_idx >= 50:
                df_entry = df_weekly.iloc[:entry_idx+1].copy()
                entry_price = df_weekly['Close'].iloc[entry_idx]
                
                try:
                    score_result = improved_scoring(df_entry, 'cryptocurrencies')
                    entry_points.append({
                        'date': target_date,
                        'price': entry_price,
                        'score': score_result.get('score', 0),
                        'indicators': score_result.get('indicators', {}),
                        'breakdown': score_result.get('breakdown', {})
                    })
                except:
                    pass
    
    # Show entry points
    if entry_points:
        print("Entry Points Analysis:")
        print(f"{'Date':<12} {'Price':<12} {'Score':<8} {'RSI':<8} {'ADX':<8} {'Momentum':<10}")
        print("-"*80)
        
        for ep in entry_points:
            rsi = ep['indicators'].get('rsi', 'N/A')
            adx = ep['indicators'].get('adx', 'N/A')
            momentum = ep['indicators'].get('momentum', 'N/A')
            
            print(f"{ep['date'].strftime('%Y-%m-%d'):<12} ${ep['price']:>10,.2f} {ep['score']:>7.1f} {rsi if isinstance(rsi, (int, float)) else 'N/A':>7.1f} {adx if isinstance(adx, (int, float)) else 'N/A':>7.1f} {momentum if isinstance(momentum, (int, float)) else 'N/A':>9.1f}%")
        
        # Calculate potential returns from each entry
        if len(recent_data) > 0:
            peak_price = recent_data['Close'].max()
            print(f"\n{'='*80}")
            print("POTENTIAL RETURNS TO PEAK ($" + f"{peak_price:,.2f}" + ")")
            print(f"{'='*80}\n")
            
            for ep in entry_points:
                return_pct = ((peak_price / ep['price']) - 1) * 100
                multiplier = peak_price / ep['price']
                print(f"{ep['date'].strftime('%Y-%m-%d')}: ${ep['price']:,.2f} → ${peak_price:,.2f}")
                print(f"  Return: {return_pct:.1f}% ({multiplier:.1f}x)")
                print(f"  Score at Entry: {ep['score']:.1f}")
                print()
    
    # Analyze what indicators were present during the move
    print(f"{'='*80}")
    print("INDICATOR ANALYSIS DURING THE MOVE")
    print(f"{'='*80}\n")
    
    # Analyze at bottom
    entry_idx = df_weekly.index.get_loc(bottom_date)
    df_entry = df_weekly.iloc[:entry_idx+1].copy()
    
    if len(df_entry) >= 50:
        try:
            score_result = improved_scoring(df_entry, 'cryptocurrencies')
            indicators = score_result.get('indicators', {})
            breakdown = score_result.get('breakdown', {})
            
            print("At Bottom (Nov 2022):")
            print(f"  Score: {score_result.get('score', 0):.1f}")
            print(f"  RSI: {indicators.get('rsi', 'N/A')}")
            print(f"  ADX: {indicators.get('adx', 'N/A')}")
            print(f"  Momentum: {indicators.get('momentum', 'N/A')}%")
            print(f"  Price vs EMA50: {((df_entry['Close'].iloc[-1] / indicators.get('ema50', 1)) - 1) * 100:.1f}%")
            
            print(f"\n  Key Signals:")
            for key, value in sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:8]:
                sign = "+" if value > 0 else ""
                print(f"    {key:40s}: {sign}{value:+.1f}")
            
            # Check what was missing
            print(f"\n  What Could Be Improved:")
            rsi = indicators.get('rsi')
            adx = indicators.get('adx')
            momentum = indicators.get('momentum')
            ema50 = indicators.get('ema50')
            price = df_entry['Close'].iloc[-1]
            
            improvements = []
            
            if adx and 20 <= adx < 25:
                improvements.append(f"ADX was {adx:.1f} - Lower threshold to 20 (already done)")
            
            if momentum and -30 < momentum < -20:
                improvements.append(f"Momentum was {momentum:.1f}% - Lower threshold to -20% (already done)")
            
            if ema50 and price:
                price_below_ema = ((price / ema50) - 1) * 100
                if price_below_ema < -20:
                    improvements.append(f"Price was {abs(price_below_ema):.1f}% below EMA50 - Extreme oversold bonus (already done)")
            
            # Check for trend continuation signals
            if adx and adx > 25:
                improvements.append(f"ADX was {adx:.1f} - Strong trend, should give continuation bonus")
            
            # Check for multi-timeframe alignment
            improvements.append("Multi-timeframe alignment - Check if 1W, 2W, 1M all bullish")
            
            # Check for halving cycle
            improvements.append("Bitcoin halving cycle - 2024 halving was a major catalyst")
            
            for imp in improvements:
                print(f"    • {imp}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Analyze continuation signals (3, 6, 12 months after bottom)
    print(f"\n{'='*80}")
    print("CONTINUATION SIGNALS (Why the Move Continued)")
    print(f"{'='*80}\n")
    
    for months_after in [3, 6, 12]:
        target_date = bottom_date + pd.DateOffset(months=months_after)
        if target_date in df_weekly.index:
            entry_idx = df_weekly.index.get_loc(target_date)
            if entry_idx >= 50:
                df_entry = df_weekly.iloc[:entry_idx+1].copy()
                entry_price = df_weekly['Close'].iloc[entry_idx]
                
                try:
                    score_result = improved_scoring(df_entry, 'cryptocurrencies')
                    indicators = score_result.get('indicators', {})
                    
                    print(f"{months_after} Months After Bottom ({target_date.strftime('%Y-%m-%d')}):")
                    print(f"  Price: ${entry_price:,.2f}")
                    print(f"  Score: {score_result.get('score', 0):.1f}")
                    print(f"  RSI: {indicators.get('rsi', 'N/A')}")
                    print(f"  ADX: {indicators.get('adx', 'N/A')}")
                    print(f"  Momentum: {indicators.get('momentum', 'N/A')}%")
                    
                    # Check if price is above EMAs
                    ema50 = indicators.get('ema50')
                    ema200 = indicators.get('ema200')
                    if ema50 and ema200 and entry_price:
                        if entry_price > ema50 and entry_price > ema200:
                            print(f"  ✅ Price above both EMAs (bullish continuation)")
                        elif entry_price > ema50:
                            print(f"  ⚠️  Price above EMA50 but below EMA200")
                        else:
                            print(f"  ⚠️  Price below both EMAs")
                    
                    print()
                except:
                    pass

if __name__ == "__main__":
    analyze_btc_full_move()
