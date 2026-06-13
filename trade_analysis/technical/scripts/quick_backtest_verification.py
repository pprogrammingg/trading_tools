#!/usr/bin/env python3
"""
Quick backtest to verify the explosive bottom bug fix
Tests that explosive bottom only triggers when RSI is oversold
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from collections import defaultdict

def verify_explosive_bottom_logic():
    """Verify that explosive bottom only triggers with oversold RSI"""
    
    result_dir = Path("result_scores")
    result_files = list(result_dir.glob("*_results.json"))
    
    issues = []
    correct_cases = 0
    total_cases = 0
    
    print("\n" + "="*80)
    print("🔍 VERIFYING EXPLOSIVE BOTTOM DETECTION LOGIC")
    print("="*80 + "\n")
    
    for result_file in sorted(result_files):
        category = result_file.name.replace("_results.json", "")
        
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            for symbol, symbol_data in data.items():
                if isinstance(symbol_data, dict):
                    for tf, tf_data in symbol_data.items():
                        if isinstance(tf_data, dict) and 'yfinance' in tf_data:
                            for denom in ['usd', 'gold', 'silver']:
                                if denom in tf_data['yfinance']:
                                    ta_data = tf_data['yfinance'][denom].get('ta_library', {})
                                    breakdown = ta_data.get('score_breakdown', {})
                                    
                                    if 'explosive_bottom_base' in breakdown:
                                        total_cases += 1
                                        rsi = ta_data.get('rsi')
                                        
                                        if rsi is not None:
                                            # Check if RSI is oversold (should be < 40 for most categories)
                                            # For silver_miners_esg, threshold is 40
                                            threshold = 40 if category == 'silver_miners_esg' else 40
                                            
                                            if rsi >= threshold:
                                                issues.append({
                                                    'symbol': symbol,
                                                    'category': category,
                                                    'timeframe': tf,
                                                    'denomination': denom,
                                                    'rsi': rsi,
                                                    'score': ta_data.get('score'),
                                                    'explosive_bottom_base': breakdown.get('explosive_bottom_base')
                                                })
                                            else:
                                                correct_cases += 1
        except Exception as e:
            print(f"Error reading {result_file.name}: {e}")
            continue
    
    print(f"Total explosive bottom cases found: {total_cases}")
    print(f"Correct cases (RSI < threshold): {correct_cases}")
    print(f"Issues found (RSI >= threshold): {len(issues)}\n")
    
    if issues:
        print("="*80)
        print("⚠️  ISSUES DETECTED - Explosive bottom triggered with non-oversold RSI:")
        print("="*80 + "\n")
        for i, issue in enumerate(issues[:10], 1):
            print(f"{i}. {issue['symbol']:12s} ({issue['category']:25s}) - {issue['timeframe']:4s} ({issue['denomination']:6s})")
            print(f"   RSI: {issue['rsi']:.2f} (should be < 40 for oversold)")
            print(f"   Score: {issue['score']:.1f}, Explosive bottom base: {issue['explosive_bottom_base']}")
            print()
        
        if len(issues) > 10:
            print(f"... and {len(issues) - 10} more issues\n")
        
        print("="*80)
        print("❌ BUG STILL EXISTS - Fix needs to be applied")
        print("="*80)
        return False
    else:
        print("="*80)
        print("✅ ALL CASES CORRECT - Explosive bottom only triggers with oversold RSI")
        print("="*80)
        return True


if __name__ == "__main__":
    verify_explosive_bottom_logic()
