#!/usr/bin/env python3
"""
Analyze Bitcoin November 2022 Bottom
What indicators were present and how to catch it
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

def analyze_btc_nov_2022():
    """Analyze BTC around November 2022 bottom"""
    
    print("\n" + "="*80)
    print("BITCOIN NOVEMBER 2022 BOTTOM ANALYSIS")
    print("="*80 + "\n")
    
    # Download BTC data - need 2+ years before Nov 2022 for indicators
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(start="2020-11-01", end="2023-02-01")
    
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
    
    # Find the bottom (lowest price in Nov 2022)
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
    
    # Find entry point (the week of the bottom)
    entry_idx = df_weekly.index.get_loc(bottom_date)
    
    # Get data up to entry point
    df_entry = df_weekly.iloc[:entry_idx+1].copy()
    
    if len(df_entry) < 50:
        print("\n⚠️  Not enough historical data for full analysis")
        return
    
    # Calculate what happened after
    future_data = df_weekly.iloc[entry_idx+1:entry_idx+13]  # ~12 weeks after
    if len(future_data) > 0:
        max_future_price = future_data['Close'].max()
        max_future_date = future_data['Close'].idxmax()
        return_pct = ((max_future_price / bottom_price) - 1) * 100
        days_to_peak = (max_future_date - bottom_date).days
        
        print(f"\n📈 Recovery:")
        print(f"   Peak: {max_future_date.strftime('%Y-%m-%d')} @ ${max_future_price:,.2f}")
        print(f"   Return: {return_pct:.1f}% in {days_to_peak} days")
    
    # Calculate current system score
    print(f"\n{'='*80}")
    print("CURRENT SYSTEM ANALYSIS")
    print(f"{'='*80}\n")
    
    try:
        score_result = improved_scoring(df_entry, 'cryptocurrencies')
        score = score_result.get('score', 0)
        indicators = score_result.get('indicators', {})
        breakdown = score_result.get('breakdown', {})
        
        print(f"System Score: {score:.1f}")
        print(f"\nKey Indicators:")
        print(f"  RSI: {indicators.get('rsi', 'N/A')}")
        print(f"  ADX: {indicators.get('adx', 'N/A')}")
        print(f"  Momentum: {indicators.get('momentum', 'N/A')}%")
        print(f"  Price: ${df_entry['Close'].iloc[-1]:,.2f}")
        print(f"  EMA50: ${indicators.get('ema50', 'N/A')}")
        print(f"  EMA200: ${indicators.get('ema200', 'N/A')}")
        
        print(f"\nScore Breakdown:")
        for key, value in sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            sign = "+" if value > 0 else ""
            print(f"  {key:40s}: {sign}{value:+.1f}")
        
        # Analyze what was missing
        print(f"\n{'='*80}")
        print("WHAT WAS MISSING?")
        print(f"{'='*80}\n")
        
        rsi = indicators.get('rsi')
        adx = indicators.get('adx')
        momentum = indicators.get('momentum')
        
        issues = []
        
        if rsi and rsi > 30:
            issues.append(f"RSI was {rsi:.1f} (not <30 for explosive bottom)")
        
        if adx and adx < 25:
            issues.append(f"ADX was {adx:.1f} (not >25 for explosive bottom)")
        
        if momentum and momentum > -30:
            issues.append(f"Momentum was {momentum:.1f}% (not <-30% for capitulation)")
        
        if issues:
            print("Issues preventing explosive bottom detection:")
            for issue in issues:
                print(f"  ❌ {issue}")
        else:
            print("✅ All conditions should have been met!")
        
        # Check ADX trend
        if adx:
            adx_value, adx_series = calculate_adx(df_entry['High'], df_entry['Low'], df_entry['Close'])
            if adx_series is not None and len(adx_series) >= 5:
                adx_current = adx_series.iloc[-1]
                adx_5_ago = adx_series.iloc[-5] if len(adx_series) >= 5 else None
                if adx_5_ago:
                    adx_change = ((adx_current / adx_5_ago) - 1) * 100
                    print(f"\nADX Trend Analysis:")
                    print(f"  Current ADX: {adx_current:.1f}")
                    print(f"  5 weeks ago: {adx_5_ago:.1f}")
                    print(f"  Change: {adx_change:+.1f}%")
                    if adx_change > 5:
                        print(f"  ✅ ADX is RISING (trend starting)")
                    elif adx_change < -5:
                        print(f"  ⚠️  ADX is FALLING (trend weakening)")
        
        # Check price vs EMAs
        price = df_entry['Close'].iloc[-1]
        ema50 = indicators.get('ema50')
        ema200 = indicators.get('ema200')
        
        if ema50 and ema200:
            print(f"\nPrice vs Moving Averages:")
            print(f"  Price: ${price:,.2f}")
            print(f"  EMA50: ${ema50:,.2f}")
            print(f"  EMA200: ${ema200:,.2f}")
            
            if price < ema50 and price < ema200:
                print(f"  ✅ Price below both EMAs (potential bottom)")
                if ema50 < ema200:
                    print(f"  ✅ EMA50 below EMA200 (bearish, but could reverse)")
            elif price > ema50 and price < ema200:
                print(f"  ⚠️  Price above EMA50 but below EMA200")
            elif price > ema50 and price > ema200:
                print(f"  ⚠️  Price above both EMAs (already recovered)")
        
        # Check volume
        volume = df_entry['Volume']
        if len(volume) >= 20:
            avg_volume = volume.rolling(window=20).mean()
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume.iloc[-1] if len(avg_volume) > 0 else 1
            
            print(f"\nVolume Analysis:")
            print(f"  Current Volume: {current_volume:,.0f}")
            print(f"  20-week Average: {avg_volume.iloc[-1]:,.0f}")
            print(f"  Ratio: {volume_ratio:.2f}x")
            if volume_ratio > 1.5:
                print(f"  ✅ High volume (capitulation/accumulation)")
            elif volume_ratio > 1.2:
                print(f"  ⚠️  Above average volume")
            else:
                print(f"  ⚠️  Below average volume")
        
        # Recommendations
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS TO CATCH BTC BOTTOMS")
        print(f"{'='*80}\n")
        
        recommendations = []
        
        if rsi and 30 <= rsi <= 40:
            recommendations.append("1. Lower RSI threshold for BTC: 35 instead of 30 (RSI was {:.1f})".format(rsi))
        
        if adx and 20 <= adx < 25:
            recommendations.append("2. Lower ADX threshold for BTC: 20 instead of 25 (ADX was {:.1f})".format(adx))
        
        if momentum and -30 < momentum < -20:
            recommendations.append("3. Lower capitulation threshold for BTC: -20% instead of -30% (Momentum was {:.1f}%)".format(momentum))
        
        if adx and adx > 40:
            recommendations.append("4. Give bonus for very high ADX (>40) even without oversold RSI (ADX was {:.1f})".format(adx))
        
        if price and ema50 and price < ema50 * 0.8:
            recommendations.append("5. Give bonus when price is >20% below EMA50 (potential oversold)")
        
        if not recommendations:
            recommendations.append("All conditions should have been met - check why explosive bottom wasn't triggered")
        
        for rec in recommendations:
            print(f"  • {rec}")
        
    except Exception as e:
        print(f"Error calculating score: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_btc_nov_2022()
