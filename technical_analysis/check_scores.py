#!/usr/bin/env python3
"""
Sanity check script for scores
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_scores():
    """Analyze score distribution and flag anomalies"""
    result_dir = Path("result_scores")
    
    all_scores = []
    score_breakdowns = defaultdict(list)
    
    for json_file in result_dir.glob("*_results.json"):
        with open(json_file) as f:
            data = json.load(f)
        
        for symbol, timeframes in data.items():
            for timeframe, sources in timeframes.items():
                for source, denominations in sources.items():
                    for denom, methods in denominations.items():
                        for method, indicators in methods.items():
                            if "score" in indicators:
                                score = indicators["score"]
                                all_scores.append((symbol, timeframe, denom, method, score))
                                
                                if "score_breakdown" in indicators:
                                    breakdown = indicators["score_breakdown"]
                                    for key, value in breakdown.items():
                                        score_breakdowns[key].append(value)
    
    print("=" * 60)
    print("SCORE DISTRIBUTION ANALYSIS")
    print("=" * 60)
    
    scores_only = [s[4] for s in all_scores]
    print(f"\nTotal scores analyzed: {len(scores_only)}")
    print(f"Min score: {min(scores_only):.1f}")
    print(f"Max score: {max(scores_only):.1f}")
    print(f"Average score: {sum(scores_only)/len(scores_only):.2f}")
    print(f"Median score: {sorted(scores_only)[len(scores_only)//2]:.2f}")
    
    # Score ranges
    ranges = {
        "Very High (8+)": sum(1 for s in scores_only if s >= 8),
        "High (6-8)": sum(1 for s in scores_only if 6 <= s < 8),
        "Medium (4-6)": sum(1 for s in scores_only if 4 <= s < 6),
        "Low (2-4)": sum(1 for s in scores_only if 2 <= s < 4),
        "Neutral (0-2)": sum(1 for s in scores_only if 0 <= s < 2),
        "Negative (<0)": sum(1 for s in scores_only if s < 0),
    }
    
    print("\nScore Distribution:")
    for range_name, count in ranges.items():
        pct = (count / len(scores_only)) * 100
        print(f"  {range_name}: {count} ({pct:.1f}%)")
    
    # Top and bottom scores
    print("\n" + "=" * 60)
    print("TOP 10 SCORES")
    print("=" * 60)
    sorted_scores = sorted(all_scores, key=lambda x: x[4], reverse=True)
    for i, (symbol, tf, denom, method, score) in enumerate(sorted_scores[:10], 1):
        print(f"{i:2d}. {symbol:10s} {tf:3s} {denom:4s} {method:20s} Score: {score:5.1f}")
    
    print("\n" + "=" * 60)
    print("BOTTOM 10 SCORES")
    print("=" * 60)
    for i, (symbol, tf, denom, method, score) in enumerate(sorted_scores[-10:], 1):
        print(f"{i:2d}. {symbol:10s} {tf:3s} {denom:4s} {method:20s} Score: {score:5.1f}")
    
    # Score breakdown analysis
    print("\n" + "=" * 60)
    print("SCORE BREAKDOWN CONTRIBUTIONS")
    print("=" * 60)
    for key, values in sorted(score_breakdowns.items(), key=lambda x: abs(sum(x[1])), reverse=True)[:15]:
        total = sum(values)
        count = len(values)
        avg = total / count if count > 0 else 0
        print(f"{key:35s} Total: {total:7.1f}  Count: {count:4d}  Avg: {avg:6.2f}")
    
    # Check for potential issues
    print("\n" + "=" * 60)
    print("POTENTIAL ISSUES")
    print("=" * 60)
    
    # Check if any single indicator dominates
    max_contributions = {}
    for key, values in score_breakdowns.items():
        max_contributions[key] = max(abs(v) for v in values) if values else 0
    
    high_contributors = [(k, v) for k, v in max_contributions.items() if v >= 2.0]
    if high_contributors:
        print("\nHigh-contributing indicators (>= 2.0 points):")
        for key, max_val in sorted(high_contributors, key=lambda x: x[1], reverse=True):
            print(f"  {key:35s} Max contribution: {max_val:.1f}")
    
    # Check score consistency
    print("\nScore consistency check:")
    very_high_count = ranges["Very High (8+)"]
    if very_high_count > len(scores_only) * 0.1:  # More than 10% with 8+
        print(f"  ⚠️  Warning: {very_high_count} scores >= 8 ({very_high_count/len(scores_only)*100:.1f}%)")
        print("     This might indicate score inflation")
    else:
        print(f"  ✓ High scores (8+) are {very_high_count/len(scores_only)*100:.1f}% - reasonable")
    
    if ranges["Negative (<0)"] == 0:
        print("  ⚠️  Warning: No negative scores found - might indicate scoring bias")
    else:
        print(f"  ✓ Negative scores present: {ranges['Negative (<0)']} ({ranges['Negative (<0)']/len(scores_only)*100:.1f}%)")

if __name__ == "__main__":
    analyze_scores()
