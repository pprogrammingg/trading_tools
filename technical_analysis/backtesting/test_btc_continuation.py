#!/usr/bin/env python3
"""
Test BTC continuation signals at Aug 2023 entry point
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
from scoring.improved_scoring import improved_scoring

# Download BTC data
ticker = yf.Ticker("BTC-USD")
df = ticker.history(start="2020-11-01", end="2025-01-20")

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

# Find Aug 2023 entry point
aug_2023 = df_weekly[(df_weekly.index >= '2023-08-01') & (df_weekly.index < '2023-09-01')]

if len(aug_2023) > 0:
    entry_date = aug_2023.index[0]
    entry_idx = df_weekly.index.get_loc(entry_date)
    entry_price = df_weekly['Close'].iloc[entry_idx]
    
    df_entry = df_weekly.iloc[:entry_idx+1].copy()
    
    print(f"\n{'='*80}")
    print(f"BTC AUGUST 2023 ENTRY POINT ANALYSIS")
    print(f"{'='*80}\n")
    print(f"Entry Date: {entry_date.strftime('%Y-%m-%d')}")
    print(f"Entry Price: ${entry_price:,.2f}")
    
    # Calculate score
    score_result = improved_scoring(df_entry, 'cryptocurrencies')
    score = score_result.get('score', 0)
    indicators = score_result.get('indicators', {})
    breakdown = score_result.get('breakdown', {})
    
    print(f"\nScore: {score:.1f}")
    print(f"\nIndicators:")
    print(f"  RSI: {indicators.get('rsi', 'N/A')}")
    print(f"  ADX: {indicators.get('adx', 'N/A')}")
    print(f"  Momentum: {indicators.get('momentum', 'N/A')}%")
    print(f"  EMA50: ${indicators.get('ema50', 'N/A')}")
    print(f"  EMA200: ${indicators.get('ema200', 'N/A')}")
    print(f"  Price: ${entry_price:,.2f}")
    
    # Check conditions
    price_above_ema50 = entry_price > indicators.get('ema50', 0) if indicators.get('ema50') else False
    price_above_ema200 = entry_price > indicators.get('ema200', 0) if indicators.get('ema200') else False
    adx = indicators.get('adx')
    adx_strong = adx and adx > 25
    
    print(f"\nContinuation Conditions:")
    print(f"  Price above EMA50: {price_above_ema50}")
    print(f"  Price above EMA200: {price_above_ema200}")
    print(f"  ADX > 25: {adx_strong} (ADX: {adx})")
    
    if price_above_ema50 and price_above_ema200 and adx_strong:
        print(f"  ✅ All continuation conditions met!")
    else:
        print(f"  ❌ Missing conditions:")
        if not price_above_ema50:
            print(f"    - Price not above EMA50")
        if not price_above_ema200:
            print(f"    - Price not above EMA200")
        if not adx_strong:
            print(f"    - ADX not strong enough ({adx} <= 25)")
    
    print(f"\nScore Breakdown:")
    for key, value in sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:15]:
        sign = "+" if value > 0 else ""
        print(f"  {key:40s}: {sign}{value:+.1f}")
    
    # Check what peak would have been
    future_data = df_weekly.iloc[entry_idx+1:]
    if len(future_data) > 0:
        peak_price = future_data['Close'].max()
        return_pct = ((peak_price / entry_price) - 1) * 100
        print(f"\n{'='*80}")
        print(f"Potential Return to Peak:")
        print(f"  Peak: ${peak_price:,.2f}")
        print(f"  Return: {return_pct:.1f}% ({peak_price/entry_price:.1f}x)")
        print(f"  Score at Entry: {score:.1f}")
