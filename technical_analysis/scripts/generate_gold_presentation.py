#!/usr/bin/env python3
"""
Generate beautiful presentation page for tickers scoring 6-7 and 7+ against Gold
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def generate_gold_presentation():
    """Generate HTML presentation of high-scoring tickers vs Gold"""
    
    result_dir = Path("result_scores")
    result_files = list(result_dir.glob("*_results.json"))
    
    # Timeframes to check (monthly or lower)
    relevant_timeframes = ['1M', '2M', '1W', '2W', '2D']
    
    # Score ranges
    score_6_7 = []  # Scores 6.0 to 6.9
    score_7_plus = []  # Scores 7.0 and above
    
    for result_file in sorted(result_files):
        category = result_file.name.replace("_results.json", "")
        
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            for symbol, symbol_data in data.items():
                if isinstance(symbol_data, dict):
                    for tf in relevant_timeframes:
                        if tf in symbol_data:
                            tf_data = symbol_data[tf]
                            
                            # Get scores
                            usd_score = None
                            gold_score = None
                            silver_score = None
                            
                            if 'yfinance' in tf_data:
                                if 'usd' in tf_data['yfinance'] and 'ta_library' in tf_data['yfinance']['usd']:
                                    usd_score = tf_data['yfinance']['usd']['ta_library'].get('score')
                                
                                if 'gold' in tf_data['yfinance'] and 'ta_library' in tf_data['yfinance']['gold']:
                                    gold_score = tf_data['yfinance']['gold']['ta_library'].get('score')
                                
                                if 'silver' in tf_data['yfinance'] and 'ta_library' in tf_data['yfinance']['silver']:
                                    silver_score = tf_data['yfinance']['silver']['ta_library'].get('score')
                            
                            # Categorize by gold score
                            if gold_score is not None:
                                entry = {
                                    'symbol': symbol,
                                    'category': category,
                                    'timeframe': tf,
                                    'gold_score': gold_score,
                                    'usd_score': usd_score,
                                    'silver_score': silver_score
                                }
                                
                                if 6.0 <= gold_score < 7.0:
                                    score_6_7.append(entry)
                                elif gold_score >= 7.0:
                                    score_7_plus.append(entry)
        except Exception as e:
            print(f"Error reading {result_file.name}: {e}")
            continue
    
    # Sort by score
    score_6_7.sort(key=lambda x: x['gold_score'], reverse=True)
    score_7_plus.sort(key=lambda x: x['gold_score'], reverse=True)
    
    # Generate HTML
    html_content = generate_html(score_6_7, score_7_plus)
    
    # Save HTML file
    output_file = Path("visualizations_output/gold_high_scores_presentation.html")
    output_file.write_text(html_content, encoding='utf-8')
    
    print(f"\n✅ Gold presentation generated: {output_file}")
    print(f"   Score 6-7: {len(score_6_7)} tickers")
    print(f"   Score 7+: {len(score_7_plus)} tickers")
    
    return output_file


def generate_html(score_6_7, score_7_plus):
    """Generate HTML content"""
    
    def format_score(score):
        if score is None:
            return '<span class="na">N/A</span>'
        color = "#006400" if score >= 6 else "#32CD32" if score >= 4 else "#90EE90" if score >= 2 else "#FFD700" if score >= 0 else "#FFA500" if score >= -2 else "#FF4500"
        return f'<span style="color: {color}; font-weight: bold;">{score:.1f}</span>'
    
    def generate_table(entries, title, id_name):
        if not entries:
            return f'<div class="section"><h2>{title}</h2><p class="empty">No tickers found in this range.</p></div>'
        
        html = f'''
        <div class="section" id="{id_name}">
            <h2>{title} <span class="count">({len(entries)} tickers)</span></h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Symbol</th>
                            <th>Category</th>
                            <th>Timeframe</th>
                            <th>Gold Score</th>
                            <th>USD Score</th>
                            <th>Silver Score</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for i, entry in enumerate(entries, 1):
            category_display = entry['category'].replace('_', ' ').title()
            html += f'''
                        <tr>
                            <td class="rank">{i}</td>
                            <td class="symbol"><strong>{entry['symbol']}</strong></td>
                            <td class="category">{category_display}</td>
                            <td class="timeframe">{entry['timeframe']}</td>
                            <td class="score gold">{format_score(entry['gold_score'])}</td>
                            <td class="score usd">{format_score(entry['usd_score'])}</td>
                            <td class="score silver">{format_score(entry['silver_score'])}</td>
                        </tr>
            '''
        
        html += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
        return html
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High-Scoring Tickers vs Gold</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .timestamp {{
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .nav {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .nav a {{
            padding: 10px 20px;
            background: white;
            border: 2px solid #667eea;
            border-radius: 25px;
            text-decoration: none;
            color: #667eea;
            font-weight: 600;
            transition: all 0.3s;
        }}
        
        .nav a:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            font-size: 2em;
            margin-bottom: 25px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .count {{
            font-size: 0.6em;
            color: #666;
            font-weight: normal;
        }}
        
        .table-container {{
            overflow-x: auto;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tbody tr:hover {{
            background: #f8f9fa;
            transform: scale(1.01);
            transition: all 0.2s;
        }}
        
        .rank {{
            font-weight: bold;
            color: #667eea;
            text-align: center;
            width: 60px;
        }}
        
        .symbol {{
            font-size: 1.1em;
        }}
        
        .category {{
            color: #666;
            text-transform: capitalize;
        }}
        
        .timeframe {{
            text-align: center;
            font-weight: 600;
            color: #495057;
        }}
        
        .score {{
            text-align: center;
            font-size: 1.1em;
            font-weight: bold;
        }}
        
        .score.gold {{
            color: #FFD700;
        }}
        
        .na {{
            color: #999;
            font-style: italic;
        }}
        
        .empty {{
            padding: 40px;
            text-align: center;
            color: #999;
            font-size: 1.2em;
        }}
        
        .summary {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 40px;
            text-align: center;
        }}
        
        .summary h2 {{
            border: none;
            color: white;
            margin-bottom: 20px;
        }}
        
        .summary-stats {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .stat {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 10px;
            min-width: 150px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            th, td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 High-Scoring Tickers vs Gold</h1>
            <p>Premium Buy Opportunities (Gold-Denominated Scores)</p>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>
        
        <div class="nav">
            <a href="#summary">Summary</a>
            <a href="#score_7_plus">Score 7+ (Excellent)</a>
            <a href="#score_6_7">Score 6-7 (Great)</a>
        </div>
        
        <div class="content">
            <div class="summary" id="summary">
                <h2>📊 Summary Statistics</h2>
                <div class="summary-stats">
                    <div class="stat">
                        <div class="stat-value">{len(score_7_plus)}</div>
                        <div class="stat-label">Score 7+ (Excellent)</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len(score_6_7)}</div>
                        <div class="stat-label">Score 6-7 (Great)</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len(score_7_plus) + len(score_6_7)}</div>
                        <div class="stat-label">Total Opportunities</div>
                    </div>
                </div>
            </div>
            
            {generate_table(score_7_plus, "🌟 Score 7.0+ (Excellent Buy Opportunities)", "score_7_plus")}
            {generate_table(score_6_7, "⭐ Score 6.0-6.9 (Great Buy Opportunities)", "score_6_7")}
        </div>
    </div>
</body>
</html>
'''
    
    return html


if __name__ == "__main__":
    generate_gold_presentation()
