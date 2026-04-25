#!/usr/bin/env python3
"""
Optimized visualization script for symbol scores
Creates a lightweight HTML file with color-coded scores
"""

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict

from visualization.build_options import VizBuildOptions
from visualization.perf_loader import load_performance_vs_spy

# ======================================================
# CONSTANTS
# ======================================================

# Score color spectrum (Great Buy → Great Sell) is in visualization_common; use get_score_color_common.

CALC_METHODS = ['ta_library', 'tradingview_library']
DENOMINATIONS = ['usd', 'gold', 'silver']

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

def sort_timeframes(timeframe: str) -> Tuple[int, int]:
    """
    Sort timeframes by period length: 4H, 1D, 2D, 1W, 2W, 1M, 2M, 6M
    
    Args:
        timeframe: Timeframe string (e.g., "4H", "1D", "2D", "1W", "2M", "1Y")
        
    Returns:
        Tuple for sorting: (unit_priority, numeric_value)
    """
    if timeframe == "4H":
        return (-1, 4)  # Hours first (before days)
    elif timeframe == "1D":
        return (0, 1)  # 1 day
    elif timeframe == "2D":
        return (0, 2)  # 2 days
    elif timeframe.endswith('D'):
        return (0, int(timeframe[:-1]))  # Other days
    elif timeframe.endswith('W'):
        return (1, int(timeframe[:-1]))  # Weeks second
    elif timeframe.endswith('M'):
        return (2, int(timeframe[:-1]))  # Months third
    elif timeframe.endswith('Y'):
        return (3, int(timeframe[:-1]))  # Years fourth
    elif timeframe.endswith('H'):
        return (-1, int(timeframe[:-1]))  # Hours (before days)
    else:
        return (4, 0)  # Unknown format last


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
    try:
        from config_loader import get_symbols_config
        config = get_symbols_config()
        if config:
            all_symbols = []
            for category_symbols in config.values():
                all_symbols.extend(category_symbols)
            return all_symbols, [], []
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
    try:
        from config_loader import get_symbols_config
        config = get_symbols_config()
        if config:
            category_order = []
            for category_symbols in config.values():
                category_order.extend(category_symbols)
            all_symbols = [s for s in category_order if s in data]
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
    """Generate the legend HTML from shared score color spectrum."""
    legend_items = [
        f'<span class="legend-item" style="background-color:{bg};color:{text};">{label}</span>'
        for _th, bg, text, label in SCORE_COLOR_SPECTRUM
    ]
    legend_items.append(
        f'<span class="legend-item" style="background-color:{SCORE_MISSING_COLOR};color:#333;">—</span>'
    )
    legend_html = f"""    <div class="legend">
        <h3>Score Legend (Great Buy → Great Sell):</h3>
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
    legend_html += _get_cme_legend_html()
    return legend_html


def _get_cme_legend_html() -> str:
    """CME Sunday 6pm ET box for all category pages (icon only, same context everywhere)."""
    cme = _get_cme_context()
    if not cme:
        return ""
    cme_items = []
    for sym, info in cme.items():
        icon = info.get("icon", "→")
        move = info.get("move_pct", info.get("gap_pct"))
        move_str = f" {move:+.2f}%" if move is not None else ""
        label = sym.replace("=F", " (fut)").replace("-USD", "")
        cme_items.append(f'<span class="cme-item" title="CME Sunday 6pm ET">{label}: <strong>{icon}</strong>{move_str}</span>')
    return (
        '    <div class="legend" style="margin-top: 15px; background: #f0f4f8; padding: 10px; border-left: 4px solid #2c3e50;">\n'
        '        <h3 style="margin-top: 0;">CME Sunday 6pm ET Open (market hand)</h3>\n'
        '        <p style="margin: 5px 0; color: #333;">Direction from CME open (first 24h or weekly gap). Icon only, not part of score.</p>\n'
        '        <p style="margin: 8px 0;">' + " &nbsp;|&nbsp; ".join(cme_items) + '</p>\n'
        '        <p style="margin: 5px 0; font-size: 0.85em; color: #666;">↑↑ strong up &nbsp; ↑ up &nbsp; → flat &nbsp; ↓ down &nbsp; ↓↓ strong down</p>\n'
        '    </div>\n'
    )


def generate_headers(viz_data: VisualizationData) -> str:
    """Generate table header HTML."""
    headers = []
    for timeframe in viz_data.timeframes:
        for source in viz_data.sources:
            for denomination in viz_data.denominations:
                if denomination == "gold":
                    denom_label = "Gold"
                elif denomination == "silver":
                    denom_label = "Silver"
                else:
                    denom_label = "USD"
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
        bg, text_color, _ = get_score_color_common(None)
        content = SCORE_MISSING_LABEL
        potential_info = ""
    else:
        bg, text_color, _ = get_score_color_common(score_info.score)
        content = str(score_info.score)
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
        f"<div class='score-cell' style='background-color:{bg};color:{text_color};'>"
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


def create_visualization(
    output_path: Optional[str] = None,
    category: Optional[str] = None,
    build: Optional[VizBuildOptions] = None,
) -> List[Path]:
    """
    Create HTML visualization(s) of scores. Uses all categories in result_scores/ for
    the index and aggregate pages; optional ``category`` limits per-category score HTML
    to one bucket (index still lists all when ``build.write_index`` is true).

    build (VizBuildOptions): no_network, skip_trending, only_index, write_index, max_workers, etc.
    """
    start_time = time.time()
    opts = build or VizBuildOptions()
    cat_key = (opts.category or category or "").strip() or None

    print("=" * 60)
    print("VISUALIZATION BENCHMARKING")
    print("=" * 60)

    find_start = time.time()
    all_result_files = find_results_files()
    file_find_time = time.time() - find_start

    if not all_result_files:
        raise FileNotFoundError(
            "Could not find any result files. Run technical_analysis.py first."
        )

    print(f"Found {len(all_result_files)} result file(s): {file_find_time*1000:.1f}ms")

    output_dir = Path("visualizations_output")
    output_dir.mkdir(exist_ok=True)

    if opts.only_index:
        if opts.write_index:
            cats = [c for c, _ in all_result_files]
            write_index_with_cme(cats, output_dir, all_result_files, build_options=opts)
        return []

    to_process = (
        all_result_files
        if not cat_key
        else [(c, p) for c, p in all_result_files if c == cat_key]
    )
    if not to_process:
        raise FileNotFoundError(
            f"Category '{cat_key}' not found in result files" if cat_key else "No categories to process"
        )

    loaded: List[Tuple[str, Dict[str, Any], float]] = []
    total_load_time = 0.0
    for category_name, result_path in to_process:
        t0 = time.time()
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        load_time = time.time() - t0
        total_load_time += load_time
        print(f"  Loaded {category_name} ({len(data)} symbols): {load_time:.2f}s")
        loaded.append((category_name, data, load_time))

    created_files: List[Path] = []
    total_process_time = 0.0
    w = max(1, min(opts.max_workers, len(loaded) or 1, 16))
    if w == 1 or len(loaded) == 1:
        for category_name, data, _ in loaded:
            t0 = time.time()
            created_files.append(
                create_visualization_for_category(category_name, data, output_dir)
            )
            total_process_time += time.time() - t0
    else:
        with ThreadPoolExecutor(max_workers=w) as ex:
            futs = {
                ex.submit(
                    create_visualization_for_category, cname, d, output_dir
                ): cname
                for cname, d, _ in loaded
            }
            for fut in as_completed(futs):
                t0 = time.time()
                created_files.append(fut.result())
                total_process_time += time.time() - t0

    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print("VISUALIZATION BENCHMARK SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total time: {total_time:.3f}s")
    print(
        f"  File find: {file_find_time*1000:.1f}ms "
        f"({file_find_time / total_time * 100 if total_time else 0:.1f}%)"
    )
    print(
        f"  JSON load: {total_load_time:.2f}s "
        f"({total_load_time / total_time * 100 if total_time else 0:.1f}%)"
    )
    print(
        f"  Processing: {total_process_time:.2f}s "
        f"({total_process_time / total_time * 100 if total_time else 0:.1f}%)"
    )
    print(f"{'=' * 60}")
    print(f"\n✓ Created {len(created_files)} visualization(s)")

    if not output_path and opts.write_index and all_result_files:
        index_cats = [c for c, _ in all_result_files]
        write_index_with_cme(index_cats, output_dir, all_result_files, build_options=opts)

    if output_path:
        created_files[0].rename(output_path)
        return [Path(output_path)]
    return created_files


# Use shared constants (single source of truth for tests and generation)
from visualization_common import (
    TOP_SCORER_TFS,
    TOP_SCORER_DENOMS,
    TOP_SCORER_BTC_ETH_KEYS,
    PERF_VS_KEYS,
    INDEX_SECTION_TOP_SCORERS_ID,
    INDEX_SECTION_TOP_SCORERS_HEADER,
    INDEX_SECTION_CATEGORY_HEADER,
    INDEX_TOP_SCORER_COLUMNS,
    PAGE_TOP_SCORES_BY_CATEGORY,
    PAGE_WEALTH_PHASE,
    PAGE_GOLD_PRESENTATION,
    PAGE_CME_SUNDAY_OPEN,
    PAGE_DIVIDEND_HOLDINGS,
    PAGE_CRYPTO_ALT_TRENDS,
    PAGE_TRENDING_INDUSTRIES,
    PAGE_HALAL_FUNDS,
    PAGE_HOT_PICK_PLAN,
    table_header_cells,
    UI_CSS_BASE,
    UI_CSS_INDEX,
    UI_CSS_TABLE,
    UI_CSS_MAIN_CARDS,
    UI_CSS_TABLE_PAGE,
    SHARED_CSS_FILENAME,
    write_shared_css,
    get_score_color as get_score_color_common,
    SCORE_MISSING_COLOR,
    SCORE_MISSING_LABEL,
    SCORE_COLOR_SPECTRUM,
    html_back_link,
    html_link_bar,
    html_card,
    html_table,
    html_page,
)


def _table_header_cells(headers: List[str]) -> str:
    """Build <th>...</th> cells for table header row (delegate to common)."""
    return table_header_cells(headers)


def _esg_score_to_rank(score: Optional[float]) -> Optional[str]:
    """Map numeric ESG score (0–100) to High / Medium / Low. Does not affect price score."""
    if score is None or (isinstance(score, float) and (score != score or score < 0)):
        return None
    v = float(score)
    if v >= 60:
        return "High"
    if v >= 30:
        return "Medium"
    return "Low"


def _load_esg_ratings(symbols: Set[str], cache_dir: Path, max_age_days: int = 7, allow_network: bool = True) -> Dict[str, Optional[str]]:
    """
    Fetch latest ESG ratings for tickers via yfinance sustainability; bucket as High / Medium / Low.
    Cached in result_scores/esg_ratings.json. Does not affect score (informational only).
    """
    cache_path = cache_dir / "esg_ratings.json"
    today = time.strftime("%Y-%m-%d")
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache = json.load(f)
            if cache.get("as_of") == today and cache.get("data"):
                return {k: v for k, v in cache["data"].items() if k in symbols}
            if not allow_network and cache.get("data"):
                return {k: (cache["data"].get(k)) for k in symbols}
        except Exception:
            pass
    if not allow_network:
        return {s: None for s in symbols}
    out: Dict[str, Optional[str]] = {}
    try:
        import yfinance as yf
    except ImportError:
        return {s: None for s in symbols}
    for sym in list(symbols)[:400]:
        try:
            ticker = yf.Ticker(sym)
            sus = getattr(ticker, "sustainability", None)
            score = None
            if sus is not None and hasattr(sus, "index") and len(sus) > 0:
                idx = list(sus.index) if hasattr(sus.index, "__iter__") else []
                vals = sus.iloc[:, 0] if len(sus.columns) > 0 else None
                for name in ["totalEsg", "totalESG", "overall", "esgScore"]:
                    for i, k in enumerate(idx):
                        if name.lower() in str(k).lower():
                            try:
                                v = float(vals.iloc[i]) if vals is not None else float("nan")
                                if 0 <= v <= 100:
                                    score = v
                                    break
                            except (TypeError, ValueError, IndexError):
                                pass
                    if score is not None:
                        break
                if score is None and vals is not None:
                    parts = []
                    for i, k in enumerate(idx):
                        sk = str(k).lower()
                        if "environment" in sk or "social" in sk or "governance" in sk:
                            try:
                                parts.append(float(vals.iloc[i]))
                            except (TypeError, ValueError, IndexError):
                                pass
                    if len(parts) >= 3:
                        try:
                            score = sum(parts[:3]) / 3.0
                            if not (0 <= score <= 100):
                                score = None
                        except (TypeError, ValueError):
                            pass
            out[sym] = _esg_score_to_rank(score)
        except Exception:
            out[sym] = None
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({"as_of": today, "data": out}, f, indent=0)
    return {k: v for k, v in out.items() if k in symbols}


def _perf_cell(pct: Optional[float]) -> str:
    """HTML cell for performance %: green if positive, red if negative, gray if None."""
    if pct is None:
        return '<td>—</td>'
    color = "#006400" if pct > 0 else "#b22222" if pct < 0 else "#666"
    sign = "+" if pct > 0 else ""
    return f'<td class="score-cell" style="background-color:{color};color:white;font-weight:bold;">{sign}{pct:.1f}%</td>'


def _load_market_caps(result_files: list, allow_network: bool = True) -> Dict[str, float]:
    """Load market cap for each symbol. Uses cache file; optionally fetches missing via yfinance."""
    cache_path = Path("result_scores") / "market_caps.json"
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache = json.load(f)
        except Exception:
            pass
    symbols_needed = set()
    for _cat, path in result_files:
        try:
            with open(path, "r") as f:
                data = json.load(f)
            symbols_needed.update(k for k in data if isinstance(data.get(k), dict))
        except Exception:
            continue
    missing = [s for s in symbols_needed if s not in cache or cache.get(s) is None]
    if missing and not allow_network:
        for s in missing:
            if s not in cache:
                cache[s] = 0
        return {s: float(cache.get(s) or 0) for s in symbols_needed}
    if missing:
        try:
            import yfinance as yf
            for sym in missing[:200]:
                try:
                    info = yf.Ticker(sym).info
                    mc = info.get("marketCap") or info.get("market_cap")
                    cache[sym] = float(mc) if mc is not None else 0
                except Exception:
                    cache[sym] = 0
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(cache, f, indent=0)
        except Exception:
            pass
    return cache


def _build_top_scorers_by_category(result_files: list, allow_network: bool = True) -> list:
    """
    Load all result files, extract scores for 1W, 2W, 1M and usd, gold, silver; add 1M/2W scores vs BTC/ETH (same framework); add ESG (informational).
    Return list of (category, [(symbol, market_cap, scores_dict), ...]) with each category sorted by market_cap desc.
    scores_dict includes "1M_btc", "2W_btc", "1M_eth", "2W_eth", "esg" (High/Medium/Low or None).
    """
    # category -> [(symbol, market_cap, scores)]
    by_category: Dict[str, List[Tuple[str, float, Dict[str, Any]]]] = defaultdict(list)
    market_caps = _load_market_caps(result_files, allow_network=allow_network)
    symbols_all: Set[str] = set()
    for _cat, path in result_files:
        if not path.exists():
            continue
        try:
            with open(path, "r") as f:
                data = json.load(f)
            symbols_all.update(k for k in data if isinstance(data.get(k), dict))
        except Exception:
            continue
    cache_dir = Path("result_scores")
    esg_ratings = _load_esg_ratings(symbols_all, cache_dir, allow_network=allow_network) if symbols_all else {}
    for category, path in result_files:
        if not path.exists():
            continue
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception:
            continue
        for symbol, symbol_data in data.items():
            if not isinstance(symbol_data, dict):
                continue
            scores: Dict[str, Optional[float]] = {f"{tf}_{d}": None for tf in TOP_SCORER_TFS for d in TOP_SCORER_DENOMS}
            for tf in TOP_SCORER_TFS:
                if tf not in symbol_data:
                    continue
                yf_data = symbol_data[tf].get("yfinance", {})
                for denom in TOP_SCORER_DENOMS:
                    if denom not in yf_data:
                        continue
                    ta = yf_data[denom].get("ta_library") or yf_data[denom].get("tradingview_library")
                    sc = ta.get("score") if isinstance(ta, dict) else None
                    scores[f"{tf}_{denom}"] = round(sc, 1) if sc is not None else None
            # BTC/ETH scores from same framework (btc_denominated / eth_denominated when available)
            for tf, key in [("1M", "1M_btc"), ("2W", "2W_btc"), ("1M", "1M_eth"), ("2W", "2W_eth")]:
                denom_key = "btc_denominated" if "btc" in key else "eth_denominated"
                yf_tf = symbol_data.get(tf, {}).get("yfinance", {})
                ta = (yf_tf.get(denom_key) or {}).get("ta_library") or (yf_tf.get(denom_key) or {}).get("tradingview_library")
                sc = ta.get("score") if isinstance(ta, dict) else None
                scores[key] = round(float(sc), 1) if sc is not None else None
            mc = market_caps.get(symbol)
            if mc is None:
                mc = 0
            scores["esg"] = esg_ratings.get(symbol)  # High / Medium / Low or None; does not affect score
            by_category[category].append((symbol, float(mc), scores))
    # Sort each category by market_cap descending, then symbol
    out = []
    for cat in sorted(by_category.keys()):
        rows = by_category[cat]
        rows.sort(key=lambda x: (-x[1], x[0]))
        out.append((cat, rows))
    return out


def _top_scorers_table_html(result_files: list, allow_network: bool = True) -> str:
    """Generate only the <table>...</table> for top scorers (for standalone page or section)."""
    if not result_files:
        return ""
    top = _build_top_scorers_by_category(result_files, allow_network=allow_network)
    header_row = _table_header_cells(INDEX_TOP_SCORER_COLUMNS)
    rows_html = []
    for category, symbol_list in top:
        cat_name = category.replace("_", " ").title()
        for symbol, mkt_cap, scores in symbol_list:
            mc_str = f"{mkt_cap/1e9:.2f}B" if mkt_cap >= 1e9 else f"{mkt_cap/1e6:.1f}M" if mkt_cap >= 1e6 else str(int(mkt_cap)) if mkt_cap else "—"
            cells = [f"<td>{cat_name}</td>", f"<td><strong>{symbol}</strong></td>", f"<td>{mc_str}</td>"]
            for tf in TOP_SCORER_TFS:
                for d in TOP_SCORER_DENOMS:
                    key = f"{tf}_{d}"
                    val = scores.get(key)
                    if val is None:
                        cells.append("<td>—</td>")
                    else:
                        bg, text, _ = get_score_color_common(val)
                        cells.append(f'<td class="score-cell" style="background-color:{bg};color:{text};font-weight:bold;">{val}</td>')
            for k in TOP_SCORER_BTC_ETH_KEYS:
                val = scores.get(k)
                if val is None:
                    cells.append("<td>—</td>")
                else:
                    bg, text, _ = get_score_color_common(val)
                    cells.append(f'<td class="score-cell" style="background-color:{bg};color:{text};font-weight:bold;">{val}</td>')
            esg = scores.get("esg")
            cells.append(f'<td class="esg-cell">{esg or "—"}</td>')
            rows_html.append("        <tr>\n            " + "\n            ".join(cells) + "\n        </tr>")
    table_body = "\n".join(rows_html)
    return f"""
        <table class="top-scorers-table" style="width:100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background: #4CAF50; color: white;">
            {header_row}
                </tr>
            </thead>
            <tbody>
{table_body}
            </tbody>
        </table>"""


def _top_scorers_html(result_files: list) -> str:
    """Generate HTML section for top scorers (wrapper with title + table)."""
    table = _top_scorers_table_html(result_files)
    if not table:
        return ""
    return (
        f'    <div class="top-scorers-section" id="{INDEX_SECTION_TOP_SCORERS_ID}" style="margin: 30px 0;">\n'
        f'        <h2 style="color: #333;">{INDEX_SECTION_TOP_SCORERS_HEADER}</h2>\n'
        '        <p style="color: #666;">Scores: 1M, 2W, 1W vs Gold, Silver, USD; then 1M/2W vs BTC and ETH (same framework); ESG = High/Medium/Low when available (informational, does not affect score). Grouped by industry, sorted by market cap.</p>\n'
        "        <div style=\"overflow-x: auto;\">\n"
        f"{table}\n"
        "        </div>\n"
        "    </div>"
    )


def _write_top_scores_page(
    result_files: list, output_dir: Path, allow_network: bool = True
) -> None:
    """Write top_scores_by_category.html with full table (standalone page)."""
    if not result_files:
        return
    table = _top_scorers_table_html(result_files, allow_network=allow_network)
    if not table:
        return
    extra_css = (
        UI_CSS_TABLE
        + "\n        body { max-width: 1400px; padding: 24px; }\n        .top-scorers-table td, .top-scorers-table th { padding: 8px; border: 1px solid #ddd; }"
    )
    body_content = f"""    <h1>📊 {INDEX_SECTION_TOP_SCORERS_HEADER}</h1>
    <p class="subtitle">Scores: 1M, 2W, 1W vs Gold, Silver, USD. Then 1M/2W performance % vs BTC and ETH.</p>
    <div style="overflow-x: auto;">
{table}
    </div>
"""
    full = html_page(INDEX_SECTION_TOP_SCORERS_HEADER, body_content, extra_css=extra_css, back_link=True)
    (output_dir / PAGE_TOP_SCORES_BY_CATEGORY).write_text(full, encoding="utf-8")


# Category -> wealth phase id (for performance-based hotness: phase temp = f(avg 1M or 1W vs SPY))
CATEGORY_TO_PHASE: Dict[str, str] = {
    "precious_metals": "metals",
    "silver_miners_esg": "metals",
    "agricultural_commodities": "commodities",
    "energy_commodities": "commodities",
    "industrial_metals": "commodities",
    "battery_storage": "commodities",
    "index_etfs": "index",
    "macro_trend": "index",
    "faang_hot_stocks": "hot",
    "ai_semiconductors": "hot",
    "tech_stocks": "hot",
    "consumer_discretionary": "hot",
    "next_gen_automotive": "hot",
    "real_estate": "hot",
    "financials": "hot",
    "healthcare": "hot",
    "utilities": "hot",
    "renewable_energy": "hot",
    "clean_energy_materials": "hot",
    "cryptocurrencies": "risk",
    "quantum": "risk",
    "miner_hpc": "risk",
}


def _phase_hotness_from_perf(avg_vs_spy_pct: Optional[float]) -> str:
    """Map average performance vs SPY (%) to temperature. Hot = outperforming SPY (e.g. metals when SPX drops)."""
    if avg_vs_spy_pct is None:
        return "neutral"
    if avg_vs_spy_pct >= 5:
        return "very_hot"
    if avg_vs_spy_pct >= 2:
        return "hot"
    if avg_vs_spy_pct >= 0:
        return "slightly_hot"
    if avg_vs_spy_pct >= -2:
        return "neutral"
    if avg_vs_spy_pct >= -5:
        return "slightly_cold"
    if avg_vs_spy_pct >= -10:
        return "cold"
    return "very_cold"


# Wealth transfer phases: order of money flow; temperature driven by performance vs SPY (Monthly/Weekly toggle)
WEALTH_PHASES = [
    {"id": "cash", "name": "Cash / Fiat", "icon": "💵", "desc": "Money in cash and short-term instruments. First refuge and base.", "order": 1},
    {"id": "metals", "name": "Metals", "icon": "🥇", "desc": "Gold, Silver. Store of value; hot when SPX drops vs metals.", "order": 2},
    {"id": "commodities", "name": "Commodities", "icon": "🌾", "desc": "Agricultural, Energy, Industrial. Real assets; next after metals in risk-on flow.", "order": 3},
    {"id": "index", "name": "Index / Top Companies", "icon": "📈", "desc": "SPY, QQQ, DIA. Broad market; capital moves to large caps as confidence builds.", "order": 4},
    {"id": "hot", "name": "Hot Stocks", "icon": "🔥", "desc": "FAANG, Semis, momentum. Higher risk–reward as cycle extends.", "order": 5},
    {"id": "risk", "name": "Highest Risk Curve", "icon": "🚀", "desc": "Emerging markets, Crypto, Quantum, AI/Robots. Last phase of wealth transfer.", "order": 6},
]
# Hue gradient: very_cold (blue) → very_hot (red) — hotness = performance vs SPY
TEMP_COLORS = {
    "very_cold": "#1a237e",
    "cold": "#1565c0",
    "slightly_cold": "#0288d1",
    "neutral": "#43a047",
    "slightly_hot": "#fb8c00",
    "hot": "#e65100",
    "very_hot": "#b71c1c",
}


def _compute_phase_perf(
    result_files: Optional[List[Tuple[str, Path]]],
    cache_dir: Path,
    allow_network: bool = True,
    perf_workers: int = 8,
) -> Dict[str, Dict[str, Any]]:
    """Aggregate 1M and 1W performance vs SPY by phase. Returns {phase_id: {temp_1m, temp_1w, avg_1m, avg_1w}}. Cash has no data -> neutral."""
    symbols_by_category: Dict[str, List[str]] = {}
    if result_files:
        for category, path in result_files:
            if not path.exists():
                continue
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                syms = [k for k in data if isinstance(data.get(k), dict)]
                if syms:
                    symbols_by_category[category] = syms
            except Exception:
                continue
    all_symbols: Set[str] = set()
    for syms in symbols_by_category.values():
        all_symbols.update(syms)
    perf = (
        load_performance_vs_spy(
            all_symbols, cache_dir, allow_network=allow_network, max_workers=perf_workers
        )
        if all_symbols
        else {}
    )
    phase_to_vals: Dict[str, List[Tuple[Optional[float], Optional[float]]]] = {p["id"]: [] for p in WEALTH_PHASES}
    for cat, syms in symbols_by_category.items():
        phase_id = CATEGORY_TO_PHASE.get(cat)
        if not phase_id:
            continue
        for s in syms:
            pv = perf.get(s) or {}
            phase_to_vals[phase_id].append((pv.get("1M_vs_spy"), pv.get("1W_vs_spy")))
    # Build list of (phase_id, avg_1m, avg_1w) for ranking
    phase_avgs: List[Tuple[str, Optional[float], Optional[float]]] = []
    for p in WEALTH_PHASES:
        pid = p["id"]
        pairs = phase_to_vals.get(pid) or []
        avg_1m = avg_1w = None
        if pairs:
            valid_1m = [x[0] for x in pairs if x[0] is not None]
            valid_1w = [x[1] for x in pairs if x[1] is not None]
            avg_1m = round(sum(valid_1m) / len(valid_1m), 2) if valid_1m else None
            avg_1w = round(sum(valid_1w) / len(valid_1w), 2) if valid_1w else None
        phase_avgs.append((pid, avg_1m, avg_1w))
    # Rank-based temperature: best performer = very_hot, worst = very_cold (relative to each other for current period)
    rank_temps = ["very_hot", "hot", "slightly_hot", "neutral", "slightly_cold", "very_cold"]
    def rank_temp_for_period(use_1m: bool) -> Dict[str, str]:
        key = 1 if use_1m else 2
        sorted_phases = sorted(phase_avgs, key=lambda x: (x[key] is None, -(x[key] or -999)), reverse=False)
        return {pid: rank_temps[i] for i, (pid, _, _) in enumerate(sorted_phases)}
    temp_1m_by_rank = rank_temp_for_period(True)
    temp_1w_by_rank = rank_temp_for_period(False)
    out: Dict[str, Dict[str, Any]] = {}
    has_any_perf = any(pa[1] is not None or pa[2] is not None for pa in phase_avgs)
    # Default gradient when no perf data (so cards always show different colors: cash cold → risk hot)
    default_temps = {"cash": "very_cold", "metals": "cold", "commodities": "slightly_cold", "index": "neutral", "hot": "slightly_hot", "risk": "very_hot"}
    for p in WEALTH_PHASES:
        pid = p["id"]
        pairs = phase_to_vals.get(pid) or []
        avg_1m = avg_1w = None
        if pairs:
            valid_1m = [x[0] for x in pairs if x[0] is not None]
            valid_1w = [x[1] for x in pairs if x[1] is not None]
            avg_1m = round(sum(valid_1m) / len(valid_1m), 2) if valid_1m else None
            avg_1w = round(sum(valid_1w) / len(valid_1w), 2) if valid_1w else None
        out[pid] = {
            "temp_1m": temp_1m_by_rank.get(pid, "neutral") if has_any_perf else default_temps.get(pid, "neutral"),
            "temp_1w": temp_1w_by_rank.get(pid, "neutral") if has_any_perf else default_temps.get(pid, "neutral"),
            "avg_1m": avg_1m,
            "avg_1w": avg_1w,
        }
    return out


def _write_wealth_phase_page(
    output_dir: Path,
    result_files: Optional[List[Tuple[str, Path]]] = None,
    allow_network: bool = True,
    perf_workers: int = 8,
) -> None:
    """Write wealth_phase.html: hotness from relative performance (Monthly/Weekly toggle). Colors = relative strength (SPX vs Metals, etc.)."""
    cache_dir = Path("result_scores")
    phase_perf = (
        _compute_phase_perf(
            result_files, cache_dir, allow_network=allow_network, perf_workers=perf_workers
        )
        if result_files
        else {}
    )
    # When no data, use default gradient so cards always show 6 different colors (cash cold → risk hot)
    if not phase_perf:
        default_temps = {"cash": "very_cold", "metals": "cold", "commodities": "slightly_cold", "index": "neutral", "hot": "slightly_hot", "risk": "very_hot"}
        phase_perf = {pid: {"temp_1m": t, "temp_1w": t, "avg_1m": None, "avg_1w": None} for pid, t in default_temps.items()}
    cards_html = []
    for p in WEALTH_PHASES:
        cid, name, icon, desc, order = p["id"], p["name"], p["icon"], p["desc"], p["order"]
        pp = phase_perf.get(cid) or {}
        temp_1m = pp.get("temp_1m") or "neutral"
        temp_1w = pp.get("temp_1w") or "neutral"
        avg_1m = pp.get("avg_1m")
        avg_1w = pp.get("avg_1w")
        avg_1m_s = f"{avg_1m:+.1f}%" if avg_1m is not None else "—"
        avg_1w_s = f"{avg_1w:+.1f}%" if avg_1w is not None else "—"
        color_1m = TEMP_COLORS.get(temp_1m, "#666")
        color_1w = TEMP_COLORS.get(temp_1w, "#666")
        prev_next = f"Phase {order}" + (" ← prev" if order > 1 else "") + (" | next →" if order < 6 else "")
        cards_html.append(
            f'        <div class="phase-card" id="phase-{cid}" data-temp-1m="{temp_1m}" data-temp-1w="{temp_1w}" '
            f'data-avg-1m="{avg_1m_s}" data-avg-1w="{avg_1w_s}" data-color-1m="{color_1m}" data-color-1w="{color_1w}">\n'
            f'            <div class="phase-order" style="font-size: 0.75em; margin-bottom: 4px;">{prev_next}</div>\n'
            f'            <div class="phase-icon phase-icon-default">{icon}</div>\n'
            f'            <h3 class="phase-name">{name}</h3>\n'
            f'            <p class="phase-temp" style="font-weight: bold; font-size: 0.8em; margin: 4px 0;"></p>\n'
            f'            <p class="phase-perf" style="font-size: 0.85em; margin: 2px 0;"></p>\n'
            f'            <p class="phase-desc">{desc}</p>\n'
            f'        </div>'
        )
    arrows = " &nbsp; → &nbsp; ".join([p["name"] for p in WEALTH_PHASES])
    grid = "\n".join(cards_html)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wealth Transfer Phase</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1100px; margin: 0 auto; padding: 24px; background: linear-gradient(135deg, #0f0f14 0%, #1a1a2e 100%); color: #e0e0e0; }}
        h1 {{ text-align: center; color: #fff; margin-bottom: 8px; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 16px; }}
        .flow-bar {{ text-align: center; color: #82b1ff; font-size: 0.9em; margin-bottom: 24px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; }}
        .toggle-bar {{ text-align: center; margin-bottom: 20px; }}
        .toggle-bar button {{ padding: 8px 20px; margin: 0 4px; border-radius: 8px; cursor: pointer; font-weight: bold; border: 2px solid #82b1ff; background: #1a1a2e; color: #82b1ff; }}
        .toggle-bar button.active {{ background: #82b1ff; color: #1a1a2e; }}
        a.back {{ display: inline-block; margin-bottom: 24px; color: #82b1ff; text-decoration: none; }}
        a.back:hover {{ text-decoration: underline; }}
        .phase-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; align-items: stretch; }}
        @media (max-width: 900px) {{ .phase-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
        @media (max-width: 500px) {{ .phase-grid {{ grid-template-columns: 1fr; }} }}
        .phase-card {{ min-height: 280px; border-radius: 12px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; align-items: center; text-align: center; }}
        .phase-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 28px rgba(0,0,0,0.4); }}
        .phase-icon {{ font-size: 48px; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }}
        .phase-name {{ font-size: 1em; color: #fff; margin: 0 0 4px 0; }}
        .phase-desc {{ font-size: 0.8em; color: #aaa; line-height: 1.35; margin: 0; flex-grow: 1; }}
    </style>
</head>
<body>
    <a href="index.html" class="back">← Back to Index</a>
    <h1>Phase of Wealth Transfer</h1>
    <p class="subtitle">Color = relative strength (e.g. SPX vs Metals, Commodities vs Metals, High risk vs normal). Toggle Monthly / Weekly:</p>
    <div class="toggle-bar">
        <button type="button" id="toggle-monthly" class="active">Monthly</button>
        <button type="button" id="toggle-weekly">Weekly</button>
    </div>
    <div class="flow-bar">{arrows}</div>
    <div class="phase-grid">
{grid}
    </div>
    <script>
    (function() {{
        var mode = '1m';
        function applyMode() {{
            document.querySelectorAll('.phase-card').forEach(function(card) {{
                var temp = mode === '1m' ? card.dataset.temp1m : card.dataset.temp1w;
                var color = mode === '1m' ? card.dataset.color1m : card.dataset.color1w;
                var avg = mode === '1m' ? card.dataset.avg1m : card.dataset.avg1w;
                card.style.borderLeftColor = color;
                card.style.background = 'linear-gradient(180deg, ' + color + '22 0%, ' + color + '55 50%, ' + color + '33 100%)';
                card.querySelector('.phase-temp').textContent = temp ? temp.replace(/_/g, ' ').replace(/\\b\\w/g, function(c) {{ return c.toUpperCase(); }}) : '—';
                card.querySelector('.phase-temp').style.color = color;
                card.querySelector('.phase-perf').textContent = (mode === '1m' ? '1M vs SPY: ' : '1W vs SPY: ') + avg;
                card.querySelector('.phase-icon').style.background = color + '44';
            }});
            document.getElementById('toggle-monthly').classList.toggle('active', mode === '1m');
            document.getElementById('toggle-weekly').classList.toggle('active', mode === '1w');
        }}
        document.getElementById('toggle-monthly').onclick = function() {{ mode = '1m'; applyMode(); }};
        document.getElementById('toggle-weekly').onclick = function() {{ mode = '1w'; applyMode(); }};
        applyMode();
    }})();
    </script>
</body>
</html>"""
    (output_dir / PAGE_WEALTH_PHASE).write_text(html, encoding="utf-8")


def _get_cme_context() -> Dict[str, Any]:
    """Load CME Sunday 6pm ET direction for display (icon only). Returns symbol -> {icon, move_pct, ...}."""
    try:
        from indicators.cme_sunday_open import get_cme_direction_all
        return get_cme_direction_all(use_1h_first=True)
    except Exception:
        try:
            from technical_analysis.indicators.cme_sunday_open import get_cme_direction_all
            return get_cme_direction_all(use_1h_first=True)
        except Exception:
            return {}


def _write_cme_page(output_dir: Path) -> None:
    """Write cme_sunday_open.html: CME Sunday 6pm ET Open in tabular format. Updated after 6 PM EST on Sunday."""
    cme = _get_cme_context()
    rows = []
    for sym, info in sorted(cme.items()):
        label = sym.replace("=F", " (fut)").replace("-USD", "")
        icon = info.get("icon", "→")
        move = info.get("move_pct", info.get("gap_pct"))
        move_str = f"{move:+.2f}%" if move is not None else "—"
        strength = (info.get("strength_label") or "flat").replace("_", " ").title()
        rows.append(f"        <tr><td>{sym}</td><td>{label}</td><td><strong>{icon}</strong></td><td>{move_str}</td><td>{strength}</td></tr>")
    table_body = "\n".join(rows) if rows else "        <tr><td colspan=\"5\">No CME data available.</td></tr>"
    table_html = f"""
        <table class="cme-table" style="width:100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background: #2c3e50; color: white;">
                    <th style="padding: 10px;">Symbol</th>
                    <th style="padding: 10px;">Label</th>
                    <th style="padding: 10px;">Direction</th>
                    <th style="padding: 10px;">Move %</th>
                    <th style="padding: 10px;">Strength</th>
                </tr>
            </thead>
            <tbody>
{table_body}
            </tbody>
        </table>"""
    full = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CME Sunday 6pm ET Open</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 24px; background: #f5f5f5; }}
        h1 {{ color: #2c3e50; margin-bottom: 8px; }}
        .cme-table td, .cme-table th {{ padding: 10px; border: 1px solid #ddd; }}
        a.back {{ display: inline-block; margin-bottom: 16px; color: #0066cc; text-decoration: none; }}
        a.back:hover {{ text-decoration: underline; }}
        .note {{ margin-top: 16px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <a href="index.html" class="back">← Back to Index</a>
    <h1>CME Sunday 6pm ET Open (market hand)</h1>
    <p style="color: #333;">Direction and strength of the move from CME open (first 24h or weekly gap). Icon only – not part of score.</p>
    <div style="overflow-x: auto;">
{table_html}
    </div>
    <p class="note">↑↑ strong up &nbsp; ↑ up &nbsp; → flat &nbsp; ↓ down &nbsp; ↓↓ strong down. <strong>Updated after 6 PM EST on Sunday.</strong></p>
</body>
</html>"""
    (output_dir / PAGE_CME_SUNDAY_OPEN).write_text(full, encoding="utf-8")


# Dividend / staking holdings: (industry, ticker, source_service, type, annual yield %)
# Sources: Kraken (kraken.com/features/staking, Auto Earn), Coinbase (coinbase.com/earn), Binance (binance.com/earn),
# Lido (lido.fi), Rocket Pool (rocketpool.net), ETF providers. Indicative only; rates subject to change.
DIVIDEND_HOLDINGS_DATA = [
    # Cryptocurrencies — Source/Service, Type, yield (on-chain → liquid staking → exchanges → ETF)
    ("Cryptocurrencies", "ETH", "Ethereum network", "On-chain staking", "~3–4%"),
    ("Cryptocurrencies", "ETH", "Lido (stETH)", "Liquid staking", "~3.2%"),
    ("Cryptocurrencies", "ETH", "Rocket Pool (rETH)", "Liquid staking", "~3.4%"),
    ("Cryptocurrencies", "ETH", "Kraken", "Exchange", "~2.84% (Flexible 1–3%; Bonded 2–5%)"),
    ("Cryptocurrencies", "ETH", "Coinbase", "Exchange", "~1.86–4%"),
    ("Cryptocurrencies", "ETH", "Binance", "Exchange", "~3%"),
    ("Cryptocurrencies", "SOL", "Solana network", "On-chain staking", "~6–7%"),
    ("Cryptocurrencies", "SOL", "Kraken", "Exchange", "~5.87% (Flexible); 6–8% Bonded"),
    ("Cryptocurrencies", "SOL", "Coinbase", "Exchange", "~4.25%"),
    ("Cryptocurrencies", "SOL", "Binance", "Exchange", "~5%"),
    ("Cryptocurrencies", "ADA", "Cardano network", "On-chain staking", "~4–5%"),
    ("Cryptocurrencies", "ADA", "Kraken", "Exchange", "~3.26% (2–5% Flexible)"),
    ("Cryptocurrencies", "ADA", "Coinbase", "Exchange", "~2–5%"),
    ("Cryptocurrencies", "ADA", "Binance", "Exchange", "~2.4%"),
    ("Cryptocurrencies", "DOT", "Polkadot network", "On-chain staking", "~12–14%"),
    ("Cryptocurrencies", "DOT", "Kraken", "Exchange", "~4–8% Flexible; 10–16% Bonded"),
    ("Cryptocurrencies", "ATOM", "Cosmos network", "On-chain staking", "~18–20%"),
    ("Cryptocurrencies", "ATOM", "Kraken", "Exchange", "~20.78% (7–11% Flex; 14–20% Bonded)"),
    ("Cryptocurrencies", "AVAX", "Avalanche network", "On-chain staking", "~7–8%"),
    ("Cryptocurrencies", "MATIC/POL", "Polygon network", "On-chain staking", "~4%"),
    ("Cryptocurrencies", "BTC", "iShares, Fidelity, Grayscale (IBIT, FBTC, GBTC)", "ETF US", "0%"),
    ("Cryptocurrencies", "BTC", "Purpose, CI Galaxy (BTCC-B.TO, BTCX-B.TO)", "ETF Canada", "0%"),
    ("Cryptocurrencies", "ETH", "iShares, Grayscale (ETHA, ETHE)", "ETF US", "0%"),
    ("Cryptocurrencies", "ETH", "CI Galaxy (ETHX-B.TO)", "ETF Canada", "0%"),
    # Other industries — Source = issuer; Type = Dividend
    ("Financials", "JPM", "JPMorgan Chase", "Dividend", "~2.1%"),
    ("Financials", "BAC", "Bank of America", "Dividend", "~2.5%"),
    ("Financials", "WFC", "Wells Fargo", "Dividend", "~2.5%"),
    ("Utilities", "DUK", "Duke Energy", "Dividend", "~3.5%"),
    ("Utilities", "SO", "Southern Company", "Dividend", "~3.2%"),
    ("Utilities", "D", "Dominion Energy", "Dividend", "~3.8%"),
    ("Healthcare", "JNJ", "Johnson & Johnson", "Dividend", "~3.2%"),
    ("Healthcare", "UNH", "UnitedHealth", "Dividend", "~0.5%"),
    ("Healthcare", "PFE", "Pfizer", "Dividend", "~3.5%"),
    ("Real Estate", "VNQ", "Vanguard REIT", "Dividend (REIT)", "~3.5%"),
    ("Real Estate", "SCHH", "Schwab REIT", "Dividend (REIT)", "~3%"),
    ("Real Estate", "IYR", "iShares REIT", "Dividend (REIT)", "~3.2%"),
    ("Index ETFs", "SPY", "State Street S&P 500", "Dividend", "~1.3%"),
    ("Index ETFs", "QQQ", "Invesco Nasdaq 100", "Dividend", "~0.5%"),
    ("Index ETFs", "IWM", "iShares Russell 2000", "Dividend", "~1.2%"),
    ("Consumer Discretionary", "HD", "Home Depot", "Dividend", "~2.5%"),
    ("Consumer Discretionary", "NKE", "Nike", "Dividend", "~1.5%"),
    ("Consumer Discretionary", "SBUX", "Starbucks", "Dividend", "~2.2%"),
]


def _dividend_holdings_table_rows() -> Tuple[List[str], List[List[str]]]:
    """Build (headers, rows) for dividend_holdings table from DIVIDEND_HOLDINGS_DATA. Columns: Industry, Ticker, Source/Service, Type, Annual yield %."""
    rows_by_industry: Dict[str, List[Tuple[str, str, str, str]]] = {}
    for industry, ticker, source_service, type_, yield_pct in DIVIDEND_HOLDINGS_DATA:
        rows_by_industry.setdefault(industry, []).append((ticker, source_service, type_, yield_pct))
    rows = []
    for industry, items in rows_by_industry.items():
        for i, (ticker, source_service, type_, yield_pct) in enumerate(items):
            industry_cell = industry if i == 0 else ""
            rows.append([industry_cell, ticker, source_service, type_, yield_pct])
    headers = ["Industry", "Ticker / Product", "Source / Service", "Type", "Annual yield %"]
    return headers, rows


def _write_dividend_holdings_page(output_dir: Path) -> None:
    """Write standalone dividend_holdings.html with full table (linked from index link bar)."""
    headers, rows = _dividend_holdings_table_rows()
    table_html = html_table(headers, rows)
    extra_css = UI_CSS_TABLE + "\n        body { max-width: 1000px; }\n"
    body_content = f"""    <h1>💰 Dividend / Staking Holdings</h1>
    <p class="subtitle">Staking or dividend yield (annual). Source/Service = earn provider: Lido, Rocket Pool, Kraken, Coinbase, Binance, ETF issuers. Rates indicative; subject to change.</p>
    <p class="subtitle" style="font-size: 0.9em;">Crypto sources: Lido (lido.fi), Rocket Pool (rocketpool.net), Kraken (kraken.com/features/staking, Auto Earn), Coinbase (coinbase.com/earn), Binance (binance.com/earn). ETF: iShares, Fidelity, Grayscale, Purpose, CI Galaxy.</p>
    <div style="overflow-x: auto;">
{table_html}
    </div>
"""
    full = html_page("Dividend / Staking Holdings", body_content, extra_css=extra_css.strip(), back_link=True)
    (output_dir / PAGE_DIVIDEND_HOLDINGS).write_text(full, encoding="utf-8")


def _build_dividend_holdings_html() -> str:
    """Build HTML for index: section with a card linking to dividend_holdings page (table is on that page)."""
    return (
        '    <h2>Dividend / Staking Holdings</h2>\n'
        '    <p class="subtitle">Staking or dividend yield by industry. Click the button above or the card below to view the table.</p>\n'
        + html_card(
            "dividend_holdings",
            f'\n        <a href="{PAGE_DIVIDEND_HOLDINGS}" target="_blank">View Dividend / Staking table →</a>\n',
            card_id="dividend_holdings",
            extra_style="margin-bottom: 24px;",
        )
    )


def _write_halal_funds_page(output_dir: Path) -> None:
    """Generate halal_funds.html from halal_funds_data.json (Halal/Islamic ETFs and mutual funds with holdings and ESG notes)."""
    data_path = Path(__file__).resolve().parent / "halal_funds_data.json"
    if not data_path.exists():
        html = html_page(
            "Halal Index & Mutual Funds",
            "    <p>Data file halal_funds_data.json not found. Add it to technical_analysis/ with keys: sources, funds (name, ticker, provider, type, holdings with ticker, weight_pct, esg).</p>",
            back_link=True,
        )
        (output_dir / PAGE_HALAL_FUNDS).write_text(html, encoding="utf-8")
        return
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    funds = data.get("funds") or []
    sections = []
    for fund in funds:
        name = fund.get("name") or ""
        ticker = fund.get("ticker") or ""
        provider = fund.get("provider") or ""
        ftype = fund.get("type") or ""
        holdings = fund.get("holdings") or []
        rows = []
        for h in holdings:
            tk = h.get("ticker") or ""
            wt = h.get("weight_pct")
            wt_str = f"{wt}%" if wt is not None else "—"
            esg = h.get("esg") or fund.get("esg_notes") or "—"
            rows.append(f"        <tr><td>{tk}</td><td>{wt_str}</td><td>{esg}</td></tr>")
        tbody = "\n".join(rows) if rows else "        <tr><td colspan=\"3\">—</td></tr>"
        sections.append(f"""
    <div class="section-block">
    <h3>{name} ({ticker})</h3>
    <p><strong>Provider:</strong> {provider} &nbsp; <strong>Type:</strong> {ftype}</p>
    <table class="data-table">
        <thead><tr><th>Ticker</th><th>Weight %</th><th>ESG / Notes</th></tr></thead>
        <tbody>
{tbody}
        </tbody>
    </table>
    </div>""")
    body = "\n".join(sections)
    if data.get("sources"):
        body += '\n    <p class="subtitle" style="margin-top:24px">Useful links: ' + ", ".join(f'<a href="{s}" target="_blank" rel="noopener">source</a>' for s in data["sources"][:3]) + "</p>"
    full = html_page("Halal Index & Mutual Funds", body, back_link=True, use_shared_css=True, body_class="page-table")
    (output_dir / PAGE_HALAL_FUNDS).write_text(full, encoding="utf-8")


def _write_modular_landing_assets(output_dir: Path) -> None:
    """index_landing + hot_pick_plan static CSS/JS; hot_pick_plan.html (modular, generated from ui_assets)."""
    from ui_assets import write_landing_artifacts
    write_landing_artifacts(output_dir, SHARED_CSS_FILENAME, PAGE_HOT_PICK_PLAN)


def write_index_with_cme(
    categories: List[str],
    output_dir: Path,
    result_files: Optional[List[Tuple[str, Path]]] = None,
    build_options: Optional[VizBuildOptions] = None,
) -> None:
    """Generate index.html with category grid, CME + dividend + halal + top scorers + optional trending."""
    opts = build_options or VizBuildOptions()
    allow_net = not opts.no_network
    write_shared_css(output_dir)
    _write_modular_landing_assets(output_dir)
    cme = _get_cme_context()
    category_cards = []
    for cat in categories:
        name = cat.replace("_", " ").title()
        fname = f"{cat}_scores.html"
        category_cards.append(
            f'        <div class="category-card">\n'
            f'            <div class="category-name">{name}</div>\n'
            f'            <a href="{fname}" target="_blank">View Analysis →</a>\n'
            f'        </div>'
        )
    grid_html = "\n".join(category_cards)

    # CME box removed from index; link in bar goes to cme_sunday_open.html (table)
    cme_html = ""

    if result_files:
        try:
            _write_top_scores_page(result_files, output_dir, allow_network=allow_net)
        except Exception:
            pass

    _write_wealth_phase_page(
        output_dir,
        result_files,
        allow_network=allow_net,
        perf_workers=opts.max_workers * 2 if opts.max_workers else 8,
    )
    _write_cme_page(output_dir)
    _write_dividend_holdings_page(output_dir)
    _write_halal_funds_page(output_dir)
    if not opts.skip_trending:
        try:
            from scripts.build_trending_industries import main as build_trending_main
            build_trending_main()
        except Exception:
            pass
    dividend_holdings_html = _build_dividend_holdings_html()
    link_bar_html = html_link_bar()
    main_cards_block = (
        f'        <a href="{PAGE_TRENDING_INDUSTRIES}" target="_blank" class="main-card main-card--trending">\n'
        '            <div class="main-card-title">📈 Top trending industries</div>\n'
        '            <div class="main-card-desc">Per-industry top 5–10 tickers with scores vs Gold, BTC, SPX, Silver (M&amp;W), ESG, horizon and special notes. Includes Index Funds.</div>\n'
        '        </a>\n'
        f'        <a href="{PAGE_HALAL_FUNDS}" target="_blank" class="main-card main-card--halal">\n'
        '            <div class="main-card-title">☪ Halal index &amp; mutual funds</div>\n'
        '            <div class="main-card-desc">Halal ETFs and mutual funds (HLAL, SPUS, UMMA, Amana, Iman) with holdings, weights and ESG notes.</div>\n'
        '        </a>\n'
        f'        <a href="{PAGE_HOT_PICK_PLAN}" target="_blank" class="main-card main-card--hot">\n'
        '            <div class="main-card-title">🔥 Hot pick plan</div>\n'
        '            <div class="main-card-desc">Horizon tables (3–24 mo): three picks per industry niche and crypto with ticker, USD price, fundies, technicals. Excludes defense, alcohol, gambling, and “savings yield” laggards—replace rows with your pipeline as needed.</div>\n'
        '        </a>\n'
    )
    index_toc = """    <nav class="index-toc" aria-label="On this page">
        <span class="index-toc__label">Jump to</span>
        <a href="#section-main">Main views</a>
        <a href="#section-other">Other views</a>
        <a href="#section-categories">By industry (category pages)</a>
    </nav>
    <p class="index-fold__toolbar">
        <button type="button" id="index-fold-expand">Expand all</button>
        <button type="button" id="index-fold-collapse">Collapse all</button>
    </p>
"""
    index_body = f"""    <h1>📊 Technical Analysis Visualizations</h1>
    <p class="subtitle">Start here: <strong>Jump to</strong> a section, expand or collapse a block, or use the main cards and category grid.</p>
{index_toc}
    <div class="index-landing">
    <details class="index-fold" id="section-main" open>
        <summary>Main views</summary>
        <div class="index-fold__body">
        <p class="subtitle">Three entry points: per-industry trending, Halal funds, and a horizon hot-pick plan (3, 6, 9, 12, 15, 18, 21, 24 months).</p>
    <div class="main-cards-grid main-cards-grid--three">
{main_cards_block}    </div>
        </div>
    </details>
    <details class="index-fold" id="section-other" open>
        <summary>Other views &amp; quick links</summary>
        <div class="index-fold__body">
        <p class="subtitle">CME open, dividend holdings, crypto trends, top scorers, wealth phase, hot pick plan, and more.</p>
{link_bar_html}        </div>
    </details>
    <details class="index-fold" id="section-categories" open>
        <summary>{INDEX_SECTION_CATEGORY_HEADER}</summary>
        <div class="index-fold__body">
        <p class="subtitle">Open a category to view the score page: <strong>{INDEX_SECTION_CATEGORY_HEADER}</strong> pages below (each symbol, market cap, scores, ESG, etc.).</p>
    <div class="category-grid">
{grid_html}
    </div>
        </div>
    </details>
    </div>
    <script src="index_landing.js" defer></script>
"""
    index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technical Analysis Visualizations - Index</title>
    <link href="{SHARED_CSS_FILENAME}" rel="stylesheet">
    <link href="index_landing.css" rel="stylesheet">
</head>
<body>
{index_body}
</body>
</html>"""
    index_path = output_dir / "index.html"
    index_path.write_text(index_content, encoding="utf-8")
    print(f"  ✓ Updated {index_path.name}")
    print(
        f"  ✓ Updated {PAGE_TOP_SCORES_BY_CATEGORY}, {PAGE_WEALTH_PHASE}, {PAGE_DIVIDEND_HOLDINGS}, {PAGE_HOT_PICK_PLAN}"
    )


def _parse_viz_args() -> VizBuildOptions:
    p = argparse.ArgumentParser(description="Generate score HTML from result_scores JSON.")
    p.add_argument("--category", type=str, default=None, help="Regenerate one category’s *_scores.html only.")
    p.add_argument(
        "--index-only",
        action="store_true",
        help="Regenerate index + aggregate pages; skip per-category score HTML (needs existing result JSON).",
    )
    p.add_argument(
        "--no-index",
        action="store_true",
        help="Only write per-category pages; do not run index/aggregate (halal, wealth, ...).",
    )
    p.add_argument(
        "--no-network",
        action="store_true",
        help="Cache-only: do not use yfinance for ESG, market cap refresh, or SPY-relative perf (uses disk cache).",
    )
    p.add_argument(
        "--skip-trending",
        action="store_true",
        help="Skip build_trending_industries (avoids yfinance in that step).",
    )
    p.add_argument(
        "--max-workers", type=int, default=4, help="Thread pool for category HTML (default: 4)."
    )
    ns, _ = p.parse_known_args()
    return VizBuildOptions(
        category=(ns.category or None),
        only_index=bool(ns.index_only),
        write_index=not ns.no_index,
        no_network=bool(ns.no_network),
        skip_trending=bool(ns.skip_trending),
        max_workers=max(1, min(ns.max_workers, 32)),
    )


if __name__ == "__main__":
    create_visualization(build=_parse_viz_args())
