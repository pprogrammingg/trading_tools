#!/usr/bin/env python3
"""
Generate report of good buy opportunities against Gold and Silver
on monthly or lower timeframes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from datetime import datetime

def generate_gold_silver_report():
    """Generate report of assets with good buy scores vs Gold and Silver"""
    
    result_dir = Path("result_scores")
    result_files = list(result_dir.glob("*_results.json"))
    
    # Timeframes to check (monthly or lower)
    relevant_timeframes = ['1M', '2M', '1W', '2W', '2D']
    
    # Good buy threshold
    good_buy_threshold = 4.0  # Score >= 4.0 is considered a good buy
    
    print("\n" + "="*80)
    print("📊 GOOD BUY OPPORTUNITIES vs GOLD & SILVER")
    print("="*80 + "\n")
    print(f"Timeframes analyzed: {', '.join(relevant_timeframes)}")
    print(f"Minimum score threshold: {good_buy_threshold}")
    print()
    
    good_buys_gold = []
    good_buys_silver = []
    
    for result_file in sorted(result_files):
        category = result_file.name.replace("_results.json", "")
        
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            for symbol, symbol_data in data.items():
                if isinstance(symbol_data, dict):
                    # Check for timeframes
                    for tf in relevant_timeframes:
                        if tf in symbol_data:
                            tf_data = symbol_data[tf]
                            
                            # Check USD score
                            usd_score = None
                            if 'yfinance' in tf_data and 'usd' in tf_data['yfinance']:
                                if 'ta_library' in tf_data['yfinance']['usd']:
                                    usd_score = tf_data['yfinance']['usd']['ta_library'].get('score')
                            
                            # Check Gold-denominated score
                            gold_score = None
                            if 'yfinance' in tf_data and 'gold' in tf_data['yfinance']:
                                if 'ta_library' in tf_data['yfinance']['gold']:
                                    gold_score = tf_data['yfinance']['gold']['ta_library'].get('score')
                            
                            # Check Silver-denominated score
                            silver_score = None
                            if 'yfinance' in tf_data and 'silver' in tf_data['yfinance']:
                                if 'ta_library' in tf_data['yfinance']['silver']:
                                    silver_score = tf_data['yfinance']['silver']['ta_library'].get('score')
                            
                            # Add to good buys if score is high enough
                            if gold_score is not None and gold_score >= good_buy_threshold:
                                good_buys_gold.append({
                                    'symbol': symbol,
                                    'category': category,
                                    'timeframe': tf,
                                    'score': gold_score,
                                    'usd_score': usd_score
                                })
                            
                            if silver_score is not None and silver_score >= good_buy_threshold:
                                good_buys_silver.append({
                                    'symbol': symbol,
                                    'category': category,
                                    'timeframe': tf,
                                    'score': silver_score,
                                    'usd_score': usd_score
                                })
        except Exception as e:
            print(f"Error reading {result_file.name}: {e}")
            continue
    
    # Sort by score
    good_buys_gold.sort(key=lambda x: x['score'], reverse=True)
    good_buys_silver.sort(key=lambda x: x['score'], reverse=True)
    
    # Print report
    print("="*80)
    print("🟡 GOOD BUYS vs GOLD (Gold-Denominated Scores)")
    print("="*80 + "\n")
    
    if good_buys_gold:
        print(f"Found {len(good_buys_gold)} good buy opportunities:\n")
        for i, buy in enumerate(good_buys_gold[:20], 1):  # Top 20
            usd_score_str = f"{buy['usd_score']:.1f}" if buy['usd_score'] is not None else "N/A"
            print(f"{i:2d}. {buy['symbol']:12s} ({buy['category']:25s}) - {buy['timeframe']:4s}: "
                  f"Score={buy['score']:5.1f} (USD: {usd_score_str})")
        if len(good_buys_gold) > 20:
            print(f"\n... and {len(good_buys_gold) - 20} more")
    else:
        print("No good buy opportunities found vs Gold")
    
    print("\n" + "="*80)
    print("⚪ GOOD BUYS vs SILVER (Silver-Denominated Scores)")
    print("="*80 + "\n")
    
    if good_buys_silver:
        print(f"Found {len(good_buys_silver)} good buy opportunities:\n")
        for i, buy in enumerate(good_buys_silver[:20], 1):  # Top 20
            usd_score_str = f"{buy['usd_score']:.1f}" if buy['usd_score'] is not None else "N/A"
            print(f"{i:2d}. {buy['symbol']:12s} ({buy['category']:25s}) - {buy['timeframe']:4s}: "
                  f"Score={buy['score']:5.1f} (USD: {usd_score_str})")
        if len(good_buys_silver) > 20:
            print(f"\n... and {len(good_buys_silver) - 20} more")
    else:
        print("No good buy opportunities found vs Silver")
    
    # Save to file
    report = {
        'timestamp': datetime.now().isoformat(),
        'threshold': good_buy_threshold,
        'timeframes': relevant_timeframes,
        'good_buys_vs_gold': good_buys_gold,
        'good_buys_vs_silver': good_buys_silver
    }
    
    report_file = Path("backtesting/gold_silver_buy_opportunities.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print(f"✅ Report saved to: {report_file}")
    print("="*80)
    
    return report

if __name__ == "__main__":
    generate_gold_silver_report()
