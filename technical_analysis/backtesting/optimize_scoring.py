#!/usr/bin/env python3
"""
Scoring Optimization Using Backtesting
Uses backtest framework to optimize scoring parameters
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.backtest_framework import BacktestFramework
from scoring.improved_scoring import improved_scoring
from technical_analysis import load_symbols_config


def load_symbols_config():
    """Load symbols from config"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'symbols_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def optimize_scoring():
    """Optimize scoring system using backtesting"""
    print("="*80)
    print("SCORING SYSTEM OPTIMIZATION")
    print("="*80)
    
    # Load symbols
    symbols_config = load_symbols_config()
    
    # Create backtest framework
    framework = BacktestFramework(improved_scoring, symbols_config)
    
    # Run backtest
    print("\nRunning comprehensive backtest...")
    all_results = framework.run_backtest(
        categories=None,  # All categories
        symbols_per_category=3,
        min_move_pct=30
    )
    
    # Analyze results
    print("\nAnalyzing results...")
    analysis = framework.analyze_results(all_results)
    
    # Print analysis
    framework.print_analysis(analysis)
    
    # Save results
    filename = framework.save_results(analysis, all_results, "optimized_backtest_results.json")
    print(f"\n✓ Results saved to {filename}")
    
    # Calculate optimization metrics
    total = analysis['total_explosive_moves']
    if total > 0:
        high_score_pct = analysis['moves_with_high_score'] / total * 100
        good_score_pct = analysis['moves_with_good_score'] / total * 100
        
        print("\n" + "="*80)
        print("OPTIMIZATION METRICS")
        print("="*80)
        print(f"High Score Catch Rate: {high_score_pct:.1f}%")
        print(f"Good Score Catch Rate: {good_score_pct:.1f}%")
        print(f"Target: 50-70% catch rate")
        
        if high_score_pct < 50:
            print("\n⚠️  Still below target. Consider:")
            print("  - Adjusting explosive bottom detection thresholds")
            print("  - Category-specific parameter tuning")
            print("  - Additional indicator combinations")
    
    return analysis


if __name__ == "__main__":
    optimize_scoring()
