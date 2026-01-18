#!/usr/bin/env python3
"""
Optimized visualization script for symbol scores
Creates a lightweight HTML file with color-coded scores
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict


# ======================================================
# CONSTANTS
# ======================================================

SCORE_THRESHOLDS = [
    (6, "#006400", "Great Buy"),      # Dark green - very strong signals
    (4, "#32CD32", "Strong Buy"),     # Medium green - strong signals
    (2, "#90EE90", "OK Buy"),         # Light green - moderate signals
    (0, "#FFD700", "Neutral"),        # Yellow - weak/neutral signals
    (-2, "#FFA500", "OK Sell"),       # Orange - moderate bearish signals
    (float('-inf'), "#FF4500", "Best Sell"),  # Red-orange - strong bearish signals
]

MISSING_DATA_COLOR = "#CCCCCC"
MISSING_DATA_LABEL = "N/A"

CALC_METHODS = ['ta_library', 'tradingview_library']
DENOMINATIONS = ['usd', 'gold']

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .score-cell {{
            text-align: center;
            font-weight: bold;
            color: white;
            border-radius: 4px;
            padding: 8px;
        }}
        .legend {{
            margin: 20px 0;
            padding: 15px;
            background-color: white;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: inline-block;
            margin: 5px 15px;
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>Stock Technical Analysis Scores</h1>
    
    {legend}
    
    <table>
        <thead>
            <tr>
                <th>Symbol</th>{headers}
            </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
    </table>
    
    <p style="text-align: center; color: #666; margin-top: 20px;">
        Generated from technical analysis indicators (RSI, ADX, CCI, MACD, OBV, A/D, EMA50/200, SMA50/200, GMMA, Volume, Momentum)
    </p>
</body>
</html>"""


# ======================================================
# DATA CLASSES
# ======================================================

@dataclass
class ScoreInfo:
    """Container for score information"""
    score: float
    timeframe: str
    source: str
    denomination: str
    upside_potential: Optional[float] = None
    downside_potential: Optional[float] = None


@dataclass
class VisualizationData:
    """Container for all visualization data"""
    symbols: List[str]
    timeframes: List[str]
    sources: List[str]
    denominations: List[str]
    symbol_scores: Dict[str, Dict[str, ScoreInfo]]
    raw_data: Dict[str, Any]


# ======================================================
# UTILITY FUNCTIONS
# ======================================================

def get_score_color(score: Optional[float]) -> Tuple[str, str]:
    """
    Determine color and label based on score.
    
    Args:
        score: The score value or None
        
    Returns:
        Tuple of (color_hex, label)
    """
    if score is None:
        return MISSING_DATA_COLOR, MISSING_DATA_LABEL
    
    # Check thresholds in order (highest to lowest)
    for threshold, color, label in SCORE_THRESHOLDS:
        if score >= threshold:
            return color, label
    
    # Fallback (should never reach here)
    return MISSING_DATA_COLOR, MISSING_DATA_LABEL


def sort_timeframes(timeframe: str) -> Tuple[int, int]:
    """
    Sort timeframes by period length.
    
    Args:
        timeframe: Timeframe string (e.g., "1W", "2M", "1Y")
        
    Returns:
        Tuple for sorting: (unit_priority, numeric_value)
    """
    if timeframe.endswith('W'):
        return (0, int(timeframe[:-1]))  # Weeks first
    elif timeframe.endswith('M'):
        return (1, int(timeframe[:-1]))  # Months second
    elif timeframe.endswith('Y'):
        return (2, int(timeframe[:-1]))  # Years third
    else:
        return (3, 0)  # Unknown format last


def find_results_files() -> list:
    """
    Find all result JSON files in result_scores directory or legacy locations.
    
    Returns:
        List of tuples (category_name, file_path)
    """
    current_dir = Path.cwd()
    results = []
    
    # Check result_scores directory (new structure)
    result_scores_dir = current_dir / 'result_scores'
    if result_scores_dir.exists():
        for result_file in result_scores_dir.glob('*_results.json'):
            category = result_file.stem.replace('_results', '')
            results.append((category, result_file))
    
    # Check legacy locations
    legacy_paths = [
        current_dir / 'all_results.json',
        current_dir.parent / 'all_results.json',
    ]
    
    for path in legacy_paths:
        if path.exists():
            results.append(('all', path))
            break
    
    return results


def load_symbol_categories() -> Tuple[List[str], ...]:
    """
    Load symbol categories from technical_analysis module or config.
    
    Returns:
        Tuple of (tech_stocks, cryptocurrencies, precious_metals)
    """
    # Try loading from config file first
    config_path = Path('symbols_config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Flatten categories for backward compatibility
            all_symbols = []
            for category_symbols in config.values():
                all_symbols.extend(category_symbols)
            return all_symbols, [], []  # Return as single list for compatibility
        except Exception:
            pass
    
    # Fallback to module import
    try:
        from technical_analysis import TECH_STOCKS, CRYPTOCURRENCIES, PRECIOUS_METALS
        return TECH_STOCKS, CRYPTOCURRENCIES, PRECIOUS_METALS
    except ImportError:
        return [], [], []


# ======================================================
# DATA PROCESSING
# ======================================================

def extract_scores_from_data(data: Dict[str, Any]) -> Tuple[
    Dict[str, Dict[str, ScoreInfo]],
    Set[str],
    Set[str],
    Set[str]
]:
    """
    Extract scores and detect structure from data.
    
    Args:
        data: The loaded JSON data
        
    Returns:
        Tuple of (symbol_scores, timeframes, sources, denominations)
    """
    symbol_scores: Dict[str, Dict[str, ScoreInfo]] = defaultdict(dict)
    timeframes: Set[str] = set()
    sources: Set[str] = set()
    denominations: Set[str] = set()
    
    for symbol, symbol_data in data.items():
        for timeframe, timeframe_data in symbol_data.items():
            if not isinstance(timeframe_data, dict):
                continue
                
            timeframes.add(timeframe)
            
            for source, source_data in timeframe_data.items():
                if not isinstance(source_data, dict):
                    continue
                    
                sources.add(source)
                
                # Check for USD and Gold pairs
                for denomination in DENOMINATIONS:
                    if denomination not in source_data:
                        continue
                        
                    denominations.add(denomination)
                    denom_data = source_data[denomination]
                    
                    if not isinstance(denom_data, dict):
                        continue
                    
                    # Get scores from both calculation methods
                    scores = []
                    for calc_method in CALC_METHODS:
                        if calc_method in denom_data:
                            score = denom_data[calc_method].get('score')
                            if score is not None:
                                scores.append(score)
                    
                    if scores:
                        # Use maximum score (best of both methods)
                        max_score = max(scores)
                        key = f"{timeframe}_{source}_{denomination}"
                        
                        # Extract potential info if available
                        potential = denom_data.get('ta_library', {}).get('relative_potential', {})
                        upside = potential.get('upside_potential_pct')
                        downside = potential.get('downside_potential_pct')
                        
                        symbol_scores[symbol][key] = ScoreInfo(
                            score=round(max_score, 1),
                            timeframe=timeframe,
                            source=source,
                            denomination=denomination,
                            upside_potential=upside,
                            downside_potential=downside
                        )
    
    return symbol_scores, timeframes, sources, denominations


def organize_symbols(data: Dict[str, Any]) -> List[str]:
    """
    Organize symbols by category order.
    
    Args:
        data: The loaded JSON data
        
    Returns:
        Ordered list of symbols
    """
    # Try loading from config file
    config_path = Path('symbols_config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Flatten all categories in order
            category_order = []
            for category_symbols in config.values():
                category_order.extend(category_symbols)
            
            # Filter to only symbols that exist in data, maintaining category order
            all_symbols = [s for s in category_order if s in data]
            
            # Add any remaining symbols not in categories (sorted)
            remaining = sorted(set(data.keys()) - set(all_symbols))
            all_symbols.extend(remaining)
            
            return all_symbols
        except Exception:
            pass
    
    # Fallback to module import
    tech_stocks, cryptocurrencies, precious_metals = load_symbol_categories()
    
    if not any([tech_stocks, cryptocurrencies, precious_metals]):
        # Final fallback: just sort alphabetically
        return sorted(data.keys())
    
    # Create ordered list: tech stocks, then crypto, then metals
    category_order = tech_stocks + cryptocurrencies + precious_metals
    
    # Filter to only symbols that exist in data, maintaining category order
    all_symbols = [s for s in category_order if s in data]
    
    # Add any remaining symbols not in categories (sorted)
    remaining = sorted(set(data.keys()) - set(all_symbols))
    all_symbols.extend(remaining)
    
    return all_symbols


def prepare_visualization_data(data: Dict[str, Any]) -> VisualizationData:
    """
    Prepare all data needed for visualization.
    
    Args:
        data: The loaded JSON data
        
    Returns:
        VisualizationData object with all processed data
    """
    # Extract scores and structure
    symbol_scores, timeframes, sources, denominations = extract_scores_from_data(data)
    
    # Organize symbols
    symbols = organize_symbols(data)
    
    # Sort collections
    sorted_timeframes = sorted(timeframes, key=sort_timeframes)
    sorted_sources = sorted(sources)
    sorted_denominations = sorted(denominations)
    
    return VisualizationData(
        symbols=symbols,
        timeframes=sorted_timeframes,
        sources=sorted_sources,
        denominations=sorted_denominations,
        symbol_scores=dict(symbol_scores),
        raw_data=data
    )


# ======================================================
# HTML GENERATION
# ======================================================

def generate_legend() -> str:
    """Generate the legend HTML."""
    legend_items = [
        '<span class="legend-item" style="background-color: #006400;">&gt;=6: Great Buy</span>',
        '<span class="legend-item" style="background-color: #32CD32;">4-5: Strong Buy</span>',
        '<span class="legend-item" style="background-color: #90EE90;">2-3: OK Buy</span>',
        '<span class="legend-item" style="background-color: #FFD700; color: #333;">0-1: Neutral</span>',
        '<span class="legend-item" style="background-color: #FFA500;">-2 to -1: OK Sell</span>',
        '<span class="legend-item" style="background-color: #FF4500;">&lt;-2: Best Sell</span>',
    ]
    
    legend_html = f"""    <div class="legend">
        <h3>Score Legend:</h3>
        {''.join(legend_items)}
        <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
            Enhanced scoring includes: RSI (context-aware), ADX (trend strength), CCI (commodities), MACD, OBV, A/D (volume), EMA50/200, SMA50/200 (Golden Cross), GMMA, Volume, Momentum
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
    </div>"""
    
    return legend_html


def generate_headers(viz_data: VisualizationData) -> str:
    """Generate table header HTML."""
    headers = []
    for timeframe in viz_data.timeframes:
        for source in viz_data.sources:
            for denomination in viz_data.denominations:
                denom_label = "Gold" if denomination == "gold" else "USD"
                headers.append(
                    f'\n                <th>{timeframe} ({source})<br><small>{denom_label}</small></th>'
                )
    return ''.join(headers)


def generate_cell_content(score_info: Optional[ScoreInfo]) -> str:
    """
    Generate HTML content for a single cell.
    
    Args:
        score_info: ScoreInfo object or None
        
    Returns:
        HTML string for the cell
    """
    if score_info is None:
        color = MISSING_DATA_COLOR
        content = MISSING_DATA_LABEL
        potential_info = ""
    else:
        color, _ = get_score_color(score_info.score)
        content = str(score_info.score)
        
        # Add potential info if available
        if score_info.upside_potential is not None and score_info.downside_potential is not None:
            potential_info = (
                f"<br><small style='font-size: 0.75em; opacity: 0.8;'>"
                f"&uarr;{score_info.upside_potential:.1f}% "
                f"&darr;{score_info.downside_potential:.1f}%</small>"
            )
        else:
            potential_info = ""
    
    return (
        f"                <td>"
        f"<div class='score-cell' style='background-color: {color};'>"
        f"{content}{potential_info}</div></td>"
    )


def generate_rows(viz_data: VisualizationData) -> str:
    """Generate table row HTML."""
    rows = []
    
    for symbol in viz_data.symbols:
        row_cells = [f"            <tr>\n                <td><strong>{symbol}</strong></td>\n"]
        
        # Add scores for each timeframe/source/denomination combination
        for timeframe in viz_data.timeframes:
            for source in viz_data.sources:
                for denomination in viz_data.denominations:
                    key = f"{timeframe}_{source}_{denomination}"
                    score_info = viz_data.symbol_scores.get(symbol, {}).get(key)
                    row_cells.append(generate_cell_content(score_info) + "\n")
        
        row_cells.append("            </tr>")
        rows.append(''.join(row_cells))
    
    return '\n'.join(rows)


def generate_html(viz_data: VisualizationData, category_name: str = "All Categories") -> str:
    """
    Generate the complete HTML visualization.
    
    Args:
        viz_data: VisualizationData object
        category_name: Name of the category for the title
        
    Returns:
        Complete HTML string
    """
    legend = generate_legend()
    headers = generate_headers(viz_data)
    rows = generate_rows(viz_data)
    title = f"Stock Scores Visualization - {category_name.title()}"
    
    # Update h1 with category name
    html_content = HTML_TEMPLATE.format(
        title=title,
        legend=legend,
        headers=headers,
        rows=rows
    )
    # Replace h1 with category-specific title
    html_content = html_content.replace(
        "<h1>Stock Technical Analysis Scores</h1>",
        f"<h1>Stock Technical Analysis Scores - {category_name.title()}</h1>"
    )
    return html_content


# ======================================================
# MAIN FUNCTION
# ======================================================

def create_visualization_for_category(category_name: str, data: Dict[str, Any], output_dir: Path) -> Path:
    """
    Create HTML visualization for a specific category.
    
    Args:
        category_name: Name of the category
        data: The loaded JSON data for this category
        output_dir: Directory to save HTML file
        
    Returns:
        Path to the created HTML file
    """
    start_time = time.time()
    timings = {
        'data_prep': 0,
        'html_gen': 0,
        'html_write': 0,
    }
    
    print(f"\n  Processing {category_name}...")
    
    # Prepare visualization data
    prep_start = time.time()
    viz_data = prepare_visualization_data(data)
    timings['data_prep'] = time.time() - prep_start
    
    # Generate HTML
    html_start = time.time()
    html_content = generate_html(viz_data, category_name)
    timings['html_gen'] = time.time() - html_start
    
    # Save HTML file
    output_file = output_dir / f"{category_name}_scores.html"
    write_start = time.time()
    output_file.write_text(html_content, encoding='utf-8')
    timings['html_write'] = time.time() - write_start
    
    total_time = time.time() - start_time
    print(f"    ✓ Generated {output_file.name} ({len(html_content)} chars, {total_time:.2f}s)")
    
    return output_file


def create_visualization(output_path: Optional[str] = None, category: Optional[str] = None) -> List[Path]:
    """
    Create HTML visualization(s) of scores.
    
    Args:
        output_path: Optional path for output file (legacy mode - single file)
        category: Optional category name to process only one category
        
    Returns:
        List of paths to created HTML files
        
    Raises:
        FileNotFoundError: If results files cannot be found
        IOError: If HTML files cannot be written
    """
    start_time = time.time()
    
    print("=" * 60)
    print("VISUALIZATION BENCHMARKING")
    print("=" * 60)
    
    # Find result files
    find_start = time.time()
    result_files = find_results_files()
    file_find_time = time.time() - find_start
    
    if not result_files:
        raise FileNotFoundError(
            "Could not find any result files. Run technical_analysis.py first."
        )
    
    print(f"Found {len(result_files)} result file(s): {file_find_time*1000:.1f}ms")
    
    # Filter by category if specified
    if category:
        result_files = [(cat, path) for cat, path in result_files if cat == category]
        if not result_files:
            raise FileNotFoundError(f"Category '{category}' not found in result files")
    
    # Create output directory
    output_dir = Path('visualizations_output')
    output_dir.mkdir(exist_ok=True)
    
    # Process each result file
    created_files = []
    total_load_time = 0
    total_process_time = 0
    
    for category_name, result_path in result_files:
        load_start = time.time()
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        load_time = time.time() - load_start
        total_load_time += load_time
        
        print(f"  Loaded {category_name} ({len(data)} symbols): {load_time:.2f}s")
        
        html_path = create_visualization_for_category(category_name, data, output_dir)
        created_files.append(html_path)
        total_process_time += time.time() - load_start
    
    total_time = time.time() - start_time
    
    print(f"\n{'=' * 60}")
    print("VISUALIZATION BENCHMARK SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total time: {total_time:.3f}s")
    print(f"  File find: {file_find_time*1000:.1f}ms ({file_find_time/total_time*100:.1f}%)")
    print(f"  JSON load: {total_load_time:.2f}s ({total_load_time/total_time*100:.1f}%)")
    print(f"  Processing: {total_process_time:.2f}s ({total_process_time/total_time*100:.1f}%)")
    print(f"{'=' * 60}")
    
    print(f"\n✓ Created {len(created_files)} visualization(s):")
    for path in created_files:
        print(f"  - {path}")
    
    # Legacy mode: if single file requested, return first file path
    if output_path:
        created_files[0].rename(output_path)
        return [Path(output_path)]
    
    return created_files


if __name__ == "__main__":
    create_visualization()
