#!/usr/bin/env python3
"""
Simple visualization script for symbol scores
Creates a lightweight HTML file with color-coded scores
"""

import json
import os

def get_score_color(score):
    """Determine color based on score
    Improved thresholds based on enhanced scoring system (max score ~8-10)
    """
    if score is None:
        return "#CCCCCC", "N/A"  # Gray for missing data
    
    # Updated thresholds for enhanced scoring (max ~8-10)
    if score >= 6:
        return "#006400", "Great Buy"  # Dark green - very strong signals
    elif score >= 4:
        return "#32CD32", "Strong Buy"  # Medium green - strong signals
    elif score >= 2:
        return "#90EE90", "OK Buy"  # Light green - moderate signals
    elif score >= 0:
        return "#FFD700", "Neutral"  # Yellow - weak/neutral signals
    elif score >= -2:
        return "#FFA500", "OK Sell"  # Orange - moderate bearish signals
    else:  # score < -2
        return "#FF4500", "Best Sell"  # Red-orange - strong bearish signals

def create_visualization():
    """Create HTML visualization of scores - dynamically reads config from data"""
    
    # Load results (look in parent directory if not found locally)
    import os
    results_path = 'all_results.json'
    if not os.path.exists(results_path):
        results_path = '../all_results.json'
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # Dynamically detect all symbols, timeframes, and sources
    # Group symbols by category (if available from investment_score_sheet.py)
    try:
        from investment_score_sheet import TECH_STOCKS, CRYPTOCURRENCIES, PRECIOUS_METALS
        # Create ordered list: tech stocks, then crypto, then metals
        category_order = TECH_STOCKS + CRYPTOCURRENCIES + PRECIOUS_METALS
        # Filter to only symbols that exist in data, maintaining category order
        all_symbols = [s for s in category_order if s in data.keys()]
        # Add any remaining symbols not in categories (sorted)
        remaining = sorted(set(data.keys()) - set(all_symbols))
        all_symbols.extend(remaining)
    except ImportError:
        # Fallback: just sort alphabetically if can't import categories
        all_symbols = sorted(data.keys())
    
    all_timeframes = set()
    all_sources = set()
    all_denominations = set()  # USD, Gold
    
    # Collect all scores and detect structure
    symbol_scores = {}
    
    for symbol in data:
        symbol_scores[symbol] = {}
        
        for timeframe in data[symbol]:
            all_timeframes.add(timeframe)
            
            for source in data[symbol][timeframe]:
                if isinstance(data[symbol][timeframe][source], dict):
                    all_sources.add(source)
                    
                    # Check for USD and Gold pairs
                    for denomination in ['usd', 'gold']:
                        if denomination in data[symbol][timeframe][source]:
                            all_denominations.add(denomination)
                            
                            # Get scores from both calculation methods
                            scores = []
                            for calc_method in ['ta_library', 'tradingview_library']:
                                if calc_method in data[symbol][timeframe][source][denomination]:
                                    score = data[symbol][timeframe][source][denomination][calc_method].get('score')
                                    if score is not None:
                                        scores.append(score)
                            
                            if scores:
                                # Use maximum score (best of both methods) instead of average
                                # This ensures we show a score if at least one method has a non-negative value
                                max_score = max(scores)
                                # Include all scores (positive and negative)
                                key = f"{timeframe}_{source}_{denomination}"
                                symbol_scores[symbol][key] = {
                                    'score': round(max_score, 1),
                                    'timeframe': timeframe,
                                    'source': source,
                                    'denomination': denomination
                                }
    
    # Sort timeframes from smallest to largest period
    # Custom sort order: 1W, 2W, 1M, 2M, 6M, etc.
    def sort_timeframes(tf):
        """Sort timeframes by period length"""
        # Extract number and unit
        if tf.endswith('W'):
            return (0, int(tf[:-1]))  # Weeks first
        elif tf.endswith('M'):
            return (1, int(tf[:-1]))  # Months second
        elif tf.endswith('Y'):
            return (2, int(tf[:-1]))  # Years third
        else:
            return (3, 0)  # Unknown format last
    
    all_timeframes = sorted(all_timeframes, key=sort_timeframes)
    all_sources = sorted(all_sources)
    all_denominations = sorted(all_denominations)  # ['gold', 'usd']
    
    # Generate HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Stock Scores Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        th {
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .score-cell {
            text-align: center;
            font-weight: bold;
            color: white;
            border-radius: 4px;
            padding: 8px;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background-color: white;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend-item {
            display: inline-block;
            margin: 5px 15px;
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Stock Technical Analysis Scores</h1>
    
    <div class="legend">
        <h3>Score Legend:</h3>
        <span class="legend-item" style="background-color: #006400;">&gt;=6: Great Buy</span>
        <span class="legend-item" style="background-color: #32CD32;">4-5: Strong Buy</span>
        <span class="legend-item" style="background-color: #90EE90;">2-3: OK Buy</span>
        <span class="legend-item" style="background-color: #FFD700; color: #333;">0-1: Neutral</span>
        <span class="legend-item" style="background-color: #FFA500;">-2 to -1: OK Sell</span>
        <span class="legend-item" style="background-color: #FF4500;">&lt;-2: Best Sell</span>
        <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
            Enhanced scoring includes: RSI, StochRSI, MACD, Volume, Momentum, EMA50, GMMA, ATR, Support levels
        </p>
    </div>
    
    <div class="legend" style="margin-top: 15px; background-color: #f0f8ff; padding: 10px; border-left: 4px solid #3498db;">
        <h3 style="margin-top: 0;">Potential Indicators:</h3>
        <p style="margin: 5px 0; color: #333;">
            <strong>&uarr;X%</strong> = Upside potential (distance to 52-week high)<br>
            <strong>&darr;X%</strong> = Downside potential (distance to 52-week low)
        </p>
        <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
            Potential percentages show how far price could move to reach recent highs/lows based on 52-week range (252 trading days).
        </p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Symbol</th>"""
    
    # Dynamically generate column headers: timeframe -> source -> denomination
    for timeframe in all_timeframes:
        for source in all_sources:
            for denomination in all_denominations:
                denom_label = "Gold" if denomination == "gold" else "USD"
                html += f"\n                <th>{timeframe} ({source})<br><small>{denom_label}</small></th>"
    
    html += """
            </tr>
        </thead>
        <tbody>
"""
    
    # Generate table rows dynamically
    for symbol in all_symbols:
        html += f"            <tr>\n                <td><strong>{symbol}</strong></td>\n"
        
        # Add scores for each timeframe/source/denomination combination (in same order as headers)
        for timeframe in all_timeframes:
            for source in all_sources:
                for denomination in all_denominations:
                    key = f"{timeframe}_{source}_{denomination}"
                    if key in symbol_scores[symbol]:
                        score = symbol_scores[symbol][key]['score']
                        color, label = get_score_color(score)
                        
                        # Get relative potential if available
                        potential_info = ""
                        try:
                            if symbol in data and timeframe in data[symbol] and source in data[symbol][timeframe]:
                                source_data = data[symbol][timeframe][source]
                                if denomination in source_data and 'ta_library' in source_data[denomination]:
                                    potential = source_data[denomination]['ta_library'].get('relative_potential', {})
                                    upside = potential.get('upside_potential_pct')
                                    downside = potential.get('downside_potential_pct')
                                    if upside is not None and downside is not None:
                                        potential_info = f"<br><small style='font-size: 0.75em; opacity: 0.8;'>&uarr;{upside:.1f}% &darr;{downside:.1f}%</small>"
                        except:
                            pass
                        
                        html += f"                <td><div class='score-cell' style='background-color: {color};'>{score}{potential_info}</div></td>\n"
                    else:
                        html += f"                <td><div class='score-cell' style='background-color: #CCCCCC;'>N/A</div></td>\n"
        
        html += "            </tr>\n"
    
    html += """        </tbody>
    </table>
    
    <p style="text-align: center; color: #666; margin-top: 20px;">
        Generated from technical analysis indicators (RSI, StochRSI, EMA50, GMMA, ATR)
    </p>
</body>
</html>"""
    
    # Save HTML file (in current directory)
    html_path = 'scores_visualization.html'
    with open(html_path, 'w') as f:
        f.write(html)
    
    print("✓ Visualization created: scores_visualization.html")
    print("  Open it in your browser to view!")

if __name__ == "__main__":
    create_visualization()
