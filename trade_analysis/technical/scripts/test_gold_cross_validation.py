#!/usr/bin/env python3
"""
Test script to verify gold-denominated score cross-validation fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from scoring.improved_scoring import improved_scoring

def test_gold_cross_validation():
    """Test that gold scores are reduced when USD scores are low"""
    
    print("\n" + "="*80)
    print("🧪 TESTING GOLD SCORE CROSS-VALIDATION FIX")
    print("="*80 + "\n")
    
    # Create test data simulating SOL scenario:
    # - Falling price in gold terms (gold rising faster)
    # - Low USD score (underperforming)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # Simulate falling price in gold terms (oversold conditions)
    gold_terms_df = pd.DataFrame({
        'Close': np.linspace(0.05, 0.02, 100),  # Falling (oversold)
        'High': np.linspace(0.052, 0.022, 100),
        'Low': np.linspace(0.048, 0.018, 100),
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    # Test 1: Low USD score (< 2.0) - should heavily reduce gold score
    print("Test 1: Low USD Score (< 2.0)")
    print("-" * 80)
    result_low_usd = improved_scoring(
        gold_terms_df, 
        category='cryptocurrencies',
        timeframe='1M',
        is_gold_denominated=True,
        usd_score=1.5  # Low USD score
    )
    
    score_low_usd = result_low_usd.get('score', 0)
    breakdown_low = result_low_usd.get('breakdown', {})
    explosive_base_low = breakdown_low.get('explosive_bottom_base', 0)
    
    print(f"  Gold Score: {score_low_usd:.1f}")
    print(f"  Explosive Bottom Base: {explosive_base_low:.1f}")
    print(f"  Expected: Explosive bottom should be reduced by 70% (multiplier 0.3)")
    
    if explosive_base_low > 2.0:
        print(f"  ❌ FAIL: Explosive bottom too high ({explosive_base_low:.1f}), should be ~1.8 (6.0 * 0.3)")
    else:
        print(f"  ✅ PASS: Explosive bottom correctly reduced")
    
    # Test 2: Moderate USD score (2.0-4.0) - should moderately reduce gold score
    print("\nTest 2: Moderate USD Score (2.0-4.0)")
    print("-" * 80)
    result_mod_usd = improved_scoring(
        gold_terms_df, 
        category='cryptocurrencies',
        timeframe='1M',
        is_gold_denominated=True,
        usd_score=3.0  # Moderate USD score
    )
    
    score_mod_usd = result_mod_usd.get('score', 0)
    breakdown_mod = result_mod_usd.get('breakdown', {})
    explosive_base_mod = breakdown_mod.get('explosive_bottom_base', 0)
    
    print(f"  Gold Score: {score_mod_usd:.1f}")
    print(f"  Explosive Bottom Base: {explosive_base_mod:.1f}")
    print(f"  Expected: Explosive bottom should be reduced by 40% (multiplier 0.6)")
    
    if explosive_base_mod > 4.0:
        print(f"  ❌ FAIL: Explosive bottom too high ({explosive_base_mod:.1f}), should be ~3.6 (6.0 * 0.6)")
    else:
        print(f"  ✅ PASS: Explosive bottom correctly reduced")
    
    # Test 3: Good USD score (>= 4.0) - should not reduce gold score
    print("\nTest 3: Good USD Score (>= 4.0)")
    print("-" * 80)
    result_good_usd = improved_scoring(
        gold_terms_df, 
        category='cryptocurrencies',
        timeframe='1M',
        is_gold_denominated=True,
        usd_score=5.0  # Good USD score
    )
    
    score_good_usd = result_good_usd.get('score', 0)
    breakdown_good = result_good_usd.get('breakdown', {})
    explosive_base_good = breakdown_good.get('explosive_bottom_base', 0)
    
    print(f"  Gold Score: {score_good_usd:.1f}")
    print(f"  Explosive Bottom Base: {explosive_base_good:.1f}")
    print(f"  Expected: Explosive bottom should NOT be reduced (multiplier 1.0)")
    
    if explosive_base_good < 5.0:
        print(f"  ⚠️  WARNING: Explosive bottom lower than expected ({explosive_base_good:.1f})")
    else:
        print(f"  ✅ PASS: Explosive bottom not reduced (as expected)")
    
    # Test 4: No USD score provided - should work normally
    print("\nTest 4: No USD Score Provided")
    print("-" * 80)
    result_no_usd = improved_scoring(
        gold_terms_df, 
        category='cryptocurrencies',
        timeframe='1M',
        is_gold_denominated=True,
        usd_score=None  # No USD score
    )
    
    score_no_usd = result_no_usd.get('score', 0)
    breakdown_no = result_no_usd.get('breakdown', {})
    explosive_base_no = breakdown_no.get('explosive_bottom_base', 0)
    
    print(f"  Gold Score: {score_no_usd:.1f}")
    print(f"  Explosive Bottom Base: {explosive_base_no:.1f}")
    print(f"  Expected: Should work normally (no reduction)")
    
    print("\n" + "="*80)
    print("✅ CROSS-VALIDATION TEST COMPLETE")
    print("="*80)
    print("\nSummary:")
    print(f"  Low USD (<2.0):   Score {score_low_usd:.1f}, Explosive Base {explosive_base_low:.1f}")
    print(f"  Mod USD (2-4):    Score {score_mod_usd:.1f}, Explosive Base {explosive_base_mod:.1f}")
    print(f"  Good USD (>=4.0): Score {score_good_usd:.1f}, Explosive Base {explosive_base_good:.1f}")
    print(f"  No USD score:     Score {score_no_usd:.1f}, Explosive Base {explosive_base_no:.1f}")
    print("\nThe fix should reduce gold scores when USD scores are low,")
    print("preventing false positives from gold outperformance.")
    print("="*80)

if __name__ == "__main__":
    test_gold_cross_validation()
