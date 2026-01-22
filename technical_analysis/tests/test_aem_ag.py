#!/usr/bin/env python3
"""
Test improved scoring on AEM and AG
Compare old vs new scores
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
from technical_analysis import compute_indicators_tv

def test_symbol(symbol):
    """Test scoring on a single symbol"""
    print(f"\n{'='*60}")
    print(f"Testing: {symbol}")
    print('='*60)
    
    # Download data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")
    if len(df) == 0:
        print(f"  ✗ No data for {symbol}")
        return None
    
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Resample to weekly
    df_weekly = df.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Rename to match expected format
    df_weekly.columns = [col.capitalize() for col in df_weekly.columns]
    df_weekly.rename(columns={'Close': 'Close', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Volume': 'Volume'}, inplace=True)
    
    if len(df_weekly) < 50:
        print(f"  ✗ Not enough data for {symbol}")
        return None
    
    # Calculate score
    result = compute_indicators_tv(df_weekly)
    
    # Display results
    print(f"\nCurrent Price: ${result['close']:.2f}")
    print(f"\nIndicators:")
    print(f"  RSI: {result.get('rsi', 'N/A')}")
    print(f"  ADX: {result.get('adx', 'N/A')}")
    print(f"  CCI: {result.get('cci', 'N/A')}")
    print(f"  Momentum: {result.get('momentum', 'N/A')}%")
    
    if result.get('ema50'):
        price_extension = ((result['close'] / result['ema50']) - 1) * 100
        print(f"  Price vs EMA50: {price_extension:.1f}% above")
    
    print(f"\nSCORE: {result['score']:.1f}")
    
    print(f"\nScore Breakdown:")
    for key, value in sorted(result['score_breakdown'].items(), key=lambda x: abs(x[1]), reverse=True):
        if abs(value) >= 0.5:  # Only show significant contributors
            print(f"  {key:35s}: {value:+.1f}")
    
    # Analysis
    print(f"\nAnalysis:")
    if result['score'] >= 6:
        print(f"  ✓ High score - Good entry potential")
    elif result['score'] >= 4:
        print(f"  ~ Medium score - Moderate potential")
    elif result['score'] >= 2:
        print(f"  ⚠ Low score - Wait for better setup")
    else:
        print(f"  ✗ Very low score - High risk, avoid")
    
    # Check for overextension
    if result.get('ema50') and result['close'] > result['ema50']:
        extension = ((result['close'] / result['ema50']) - 1) * 100
        if extension > 50:
            print(f"  ⚠ EXTREME OVEREXTENSION: Price {extension:.1f}% above EMA50")
        elif extension > 30:
            print(f"  ⚠ Overextension: Price {extension:.1f}% above EMA50")
    
    # Check for overbought
    overbought_signals = []
    if result.get('rsi') and result['rsi'] > 70:
        overbought_signals.append(f"RSI {result['rsi']:.1f}")
    if result.get('cci') and result['cci'] > 100:
        overbought_signals.append(f"CCI {result['cci']:.1f}")
    
    if overbought_signals:
        print(f"  ⚠ OVERBOUGHT: {', '.join(overbought_signals)}")
    
    return result

if __name__ == "__main__":
    print("="*60)
    print("AEM & AG SCORING TEST")
    print("="*60)
    print("\nTesting improved predictive scoring system...")
    
    aem_result = test_symbol("AEM")
    ag_result = test_symbol("AG")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if aem_result:
        print(f"\nAEM Score: {aem_result['score']:.1f}")
        print(f"  Expected: ~4.5 (was 8.0 before improvements)")
        if abs(aem_result['score'] - 4.5) < 2:
            print(f"  ✓ Score adjusted appropriately")
        else:
            print(f"  ⚠ Score may still need adjustment")
    
    if ag_result:
        print(f"\nAG Score: {ag_result['score']:.1f}")
        print(f"  Expected: ~3.0 (was 7.5 before improvements)")
        if abs(ag_result['score'] - 3.0) < 2:
            print(f"  ✓ Score adjusted appropriately")
        else:
            print(f"  ⚠ Score may still need adjustment")
