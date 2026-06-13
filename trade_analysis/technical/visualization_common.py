"""
Shared constants and helpers for visualization and UI tests.
Single source of truth for section IDs, column names, page filenames, and reusable UI (CSS/HTML).
"""

from typing import List, Tuple, Optional, Any

# Top scorers: column order by denomination (Gold, Silver, USD), then 1M/2W/1W; then scores vs BTC/ETH (same framework)
TOP_SCORER_TFS = ["1M", "2W", "1W"]
TOP_SCORER_DENOMS = ["gold", "silver", "usd"]
TOP_SCORER_BTC_ETH_COLUMNS = ["1M BTC", "2W BTC", "1M ETH", "2W ETH"]
TOP_SCORER_BTC_ETH_KEYS = ["1M_btc", "2W_btc", "1M_eth", "2W_eth"]
PERF_VS_KEYS = ["1M_vs_btc", "2W_vs_btc", "1M_vs_eth", "2W_vs_eth"]

# Section IDs and headers (index and standalone pages)
INDEX_SECTION_TOP_SCORERS_ID = "top-scores-by-category"
INDEX_SECTION_TOP_SCORERS_HEADER = "Top scores grouped by industry/category of investment, sorted in each group by market cap"
INDEX_SECTION_CATEGORY_HEADER = "Industry / Category"

# Standalone page filenames (linked from index)
PAGE_TOP_SCORES_BY_CATEGORY = "top_scores_by_category.html"
PAGE_WEALTH_PHASE = "wealth_phase.html"
PAGE_GOLD_PRESENTATION = "gold_high_scores_presentation.html"
PAGE_CME_SUNDAY_OPEN = "cme_sunday_open.html"
PAGE_DIVIDEND_HOLDINGS = "dividend_holdings.html"
PAGE_CRYPTO_ALT_TRENDS = "crypto_alt_trends.html"
PAGE_TRENDING_INDUSTRIES = "trending_industries.html"
PAGE_HALAL_FUNDS = "halal_funds.html"
PAGE_HOT_PICK_PLAN = "hot_pick_plan.html"

# Table column headers (for generation and tests)
INDEX_TOP_SCORER_COLUMNS = (
    ["Category", "Symbol", "MktCap"]
    + [f"{tf} {('USD' if d == 'usd' else 'Gold' if d == 'gold' else 'Silver')}" for tf in TOP_SCORER_TFS for d in TOP_SCORER_DENOMS]
    + TOP_SCORER_BTC_ETH_COLUMNS
    + ["ESG"]
)


def table_header_cells(headers: List[str]) -> str:
    """Build <th>...</th> cells for table header row (caller wraps in <tr>)."""
    return "\n            ".join(f"<th>{h}</th>" for h in headers)


# ============== Score color spectrum (Great Buy → Great Sell) ==============
# Single source of truth for color-coding numeric scores in tables.
# Darker green = strongest buy, yellow/orange = neutral, darker red = strongest sell.
SCORE_COLOR_SPECTRUM = [
    (6.0, "#004d00", "#fff", "Great Buy"),       # Dark green
    (4.0, "#228B22", "#fff", "Strong Buy"),      # Forest green
    (2.0, "#32CD32", "#fff", "OK Buy"),          # Lime green
    (0.5, "#90EE90", "#1a1a1a", "Weak Buy"),     # Light green
    (0.0, "#FFD700", "#1a1a1a", "Neutral"),      # Yellow
    (-1.0, "#FFA500", "#1a1a1a", "Weak Sell"),   # Orange
    (-2.0, "#FF6347", "#fff", "OK Sell"),        # Tomato
    (float("-inf"), "#8B0000", "#fff", "Great Sell"),  # Dark red
]
SCORE_MISSING_COLOR = "#CCCCCC"
SCORE_MISSING_LABEL = "—"


def get_score_color(score: Optional[float]) -> Tuple[str, str, str]:
    """Return (bg_hex, text_hex, label) for a score. Use SCORE_MISSING_* when score is None."""
    if score is None:
        return SCORE_MISSING_COLOR, "#333", SCORE_MISSING_LABEL
    try:
        v = float(score)
    except (TypeError, ValueError):
        return SCORE_MISSING_COLOR, "#333", SCORE_MISSING_LABEL
    for threshold, bg, text, label in SCORE_COLOR_SPECTRUM:
        if v >= threshold:
            return bg, text, label
    return SCORE_MISSING_COLOR, "#333", SCORE_MISSING_LABEL


def score_legend_html() -> str:
    """Return a compact legend HTML for the score color spectrum (Great Buy → Great Sell)."""
    parts = []
    for _th, bg, text, label in SCORE_COLOR_SPECTRUM:
        parts.append(
            f'<span style="display:inline-block;background-color:{bg};color:{text};'
            f'padding:2px 8px;margin-right:6px;border-radius:4px;font-size:0.75rem;font-weight:600;">{label}</span>'
        )
    parts.append(
        f'<span style="display:inline-block;background-color:{SCORE_MISSING_COLOR};color:#333;'
        'padding:2px 8px;border-radius:4px;font-size:0.75rem;">—</span>'
    )
    return (
        '<p class="subtitle" style="margin-top:8px;margin-bottom:20px;">'
        'Score colors: ' + "".join(parts) + "</p>"
    )


def score_cell_html(score: Any, format_str: str = "{:.1f}") -> str:
    """Return <td> HTML for a score cell with background/text color. Use for numeric score columns."""
    if score is None:
        bg, text, _ = get_score_color(None)
        return f'<td style="background-color:{bg};color:{text};font-weight:500;">—</td>'
    try:
        v = float(score)
    except (TypeError, ValueError):
        bg, text, _ = get_score_color(None)
        return f'<td style="background-color:{bg};color:{text};">—</td>'
    bg, text, _ = get_score_color(v)
    formatted = format_str.format(v) if isinstance(format_str, str) else str(v)
    return f'<td style="background-color:{bg};color:{text};font-weight:500;">{formatted}</td>'


# ============== Reusable UI: CSS ==============

UI_CSS_BASE = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        h2 { color: #333; margin-top: 48px; margin-bottom: 16px; }
        p.subtitle { text-align: center; color: #666; margin-bottom: 12px; }
        a.back { display: inline-block; margin-bottom: 16px; color: #0066cc; text-decoration: none; }
        a.back:hover { text-decoration: underline; }
"""

UI_CSS_INDEX = """
        .category-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }
        .category-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; }
        .category-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
        .category-card a { text-decoration: none; color: #0066cc; font-weight: 500; font-size: 16px; display: block; }
        .category-card a:hover { color: #0052a3; text-decoration: underline; }
        .category-name { text-transform: capitalize; margin-bottom: 10px; color: #333; }
        .link-bar { text-align: center; margin: 30px 0; display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
        .link-bar a { display: inline-block; padding: 15px 30px; color: white; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 1.2em; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: transform 0.2s; }
        .link-bar a:hover { transform: translateY(-2px); }
        .cme-item { margin-right: 12px; }
"""

UI_CSS_TABLE = """
        table { width: 100%; border-collapse: collapse; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }
        th { padding: 8px 12px; text-align: left; font-weight: bold; border-bottom: 2px solid #ddd; }
        td { padding: 8px 12px; border-bottom: 1px solid #eee; }
        tr:hover { background-color: #f9f9f9; }
"""

# Two main cards on index (hero section)
UI_CSS_MAIN_CARDS = """
        .main-cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; margin: 24px 0 40px; max-width: 900px; margin-left: auto; margin-right: auto; }
        .main-card { border-radius: 16px; padding: 28px 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); transition: transform 0.2s ease, box-shadow 0.2s ease; text-decoration: none; color: inherit; display: block; border: 1px solid rgba(0,0,0,0.06); min-height: 140px; }
        .main-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.12); }
        .main-card .main-card-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }
        .main-card .main-card-desc { font-size: 0.9rem; color: #555; line-height: 1.45; }
        .main-card--trending { background: linear-gradient(145deg, #f0f9ff 0%, #e0f2fe 50%, #fff 100%); }
        .main-card--halal { background: linear-gradient(145deg, #f0fdf4 0%, #dcfce7 50%, #fff 100%); }
        .main-card--hot { background: linear-gradient(145deg, #fff7ed 0%, #ffedd5 50%, #fff 100%); }
"""

# Styled tables: body override for table pages (use class="page-table" on body)
UI_CSS_TABLE_PAGE_BODY = """
        .page-table { max-width: 1600px; padding: 28px; background: #f8fafc; }
"""
# Table/section styles (shared by trending_industries and halal_funds)
UI_CSS_TABLE_PAGE_CONTENT = """
        .data-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin: 16px 0 32px; }
        .data-table thead { background: linear-gradient(180deg, #334155 0%, #1e293b 100%); color: #fff; }
        .data-table th { padding: 12px 14px; text-align: left; font-weight: 600; font-size: 0.85rem; }
        .data-table td { padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }
        .data-table tbody tr:nth-child(even) { background: #f8fafc; }
        .data-table tbody tr:hover { background: #e0f2fe; }
        .data-table tbody tr:last-child td { border-bottom: none; }
        .section-block { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }
        .section-block h2 { margin-top: 0; margin-bottom: 12px; font-size: 1.35rem; color: #1e293b; }
        .section-block h3 { margin: 0 0 8px; font-size: 1.15rem; color: #334155; }
        .section-block p { margin: 0 0 12px; color: #64748b; font-size: 0.9rem; }
"""
# Legacy: full table page CSS (body + content) for inline use when shared.css not used
UI_CSS_TABLE_PAGE = (
    "\n        body { max-width: 1600px; padding: 28px; background: #f8fafc; }\n"
    + UI_CSS_TABLE_PAGE_CONTENT
)

# Single shared stylesheet: all pages link to this (no duplicated CSS)
SHARED_CSS_FILENAME = "shared.css"


def get_shared_css_content() -> str:
    """Return full content for shared.css (base + index + main cards + table page body + table content)."""
    return "".join([
        UI_CSS_BASE,
        UI_CSS_INDEX,
        UI_CSS_MAIN_CARDS,
        UI_CSS_TABLE_PAGE_BODY,
        UI_CSS_TABLE_PAGE_CONTENT,
    ]).strip() + "\n"


def write_shared_css(output_dir: "Path") -> None:
    """Write shared.css into output_dir so all pages can link to it."""
    try:
        from pathlib import Path
        p = Path(output_dir) / SHARED_CSS_FILENAME
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(get_shared_css_content(), encoding="utf-8")
    except Exception:
        pass


# Index nav links: (href, label, style) — style is full CSS for the link (include "background:" for gradients)
INDEX_NAV_LINKS: List[Tuple[str, str, str]] = [
    (PAGE_GOLD_PRESENTATION, "🏆 Top Scorers vs Gold & USD (Monthly)", "background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"),
    (PAGE_HOT_PICK_PLAN, "🔥 Hot pick plan (3–24 mo by horizon)", "background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%)"),
    (PAGE_TOP_SCORES_BY_CATEGORY, "📊 Top scores by industry/category", "background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%)"),
    (PAGE_WEALTH_PHASE, "Which phase of wealth transfer? →", "background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%)"),
    (PAGE_CME_SUNDAY_OPEN, "CME Sunday 6pm ET Open (table)", "background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%)"),
    (PAGE_DIVIDEND_HOLDINGS, "💰 Dividend / Staking Holdings", "background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%)"),
    (PAGE_CRYPTO_ALT_TRENDS, "🔥 Crypto Alt Trends (Micro/Mid Cap)", "background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"),
]


# ============== Reusable UI: HTML builders ==============

def html_back_link(href: str = "index.html", label: str = "← Back to Index") -> str:
    """Return back-to-index link HTML."""
    return f'    <a href="{href}" class="back">{label}</a>\n'


def html_link_bar(links: Optional[List[Tuple[str, str, str]]] = None) -> str:
    """Return link bar HTML. links = [(href, label, style)] where style is full CSS for the link (e.g. background: ...). Default INDEX_NAV_LINKS."""
    links = links or INDEX_NAV_LINKS
    items = []
    for href, label, style in links:
        esc_label = label.replace("&", "&amp;")
        items.append(f'        <a href="{href}" style="{style}" class="link-bar-item">{esc_label}</a>')
    return '    <div class="link-bar">\n' + "\n".join(items) + "\n    </div>\n"


def html_card(title: str, body_html: str, card_id: str = "", extra_style: str = "") -> str:
    """Return a card div: title + body. Use card_id for anchor, extra_style for inline style."""
    id_attr = f' id="{card_id}"' if card_id else ""
    style_attr = f' style="{extra_style}"' if extra_style else ""
    return f'    <div class="category-card"{id_attr}{style_attr}>\n        <div class="category-name">{title}</div>\n        {body_html}\n    </div>\n'


def html_table(headers: List[str], rows: List[List[str]], th_style: str = "", td_style: str = "") -> str:
    """Build a simple table: headers in <thead>, rows in <tbody>. Optional th_style/td_style for inline styles."""
    th_open = f'<th style="{th_style}"' if th_style else "<th"
    out = ["    <table>", "        <thead><tr>"]
    for h in headers:
        out.append(f"            <th>{h}</th>")
    out.append("        </tr></thead>")
    out.append("        <tbody>")
    for row in rows:
        out.append("        <tr>")
        for i, cell in enumerate(row):
            style = td_style if not th_style else ""
            align = ' style="text-align:right;"' if i == len(headers) - 1 and headers and "%" in (headers[-1] or "") else ""
            out.append(f"            <td{align}>{cell}</td>")
        out.append("        </tr>")
    out.append("        </tbody>")
    out.append("    </table>")
    return "\n".join(out)


def html_page(
    title: str,
    body_content: str,
    extra_css: str = "",
    back_link: bool = True,
    back_href: str = "index.html",
    use_shared_css: bool = False,
    body_class: str = "",
) -> str:
    """Return full HTML page. If use_shared_css=True, link to shared.css (no inline CSS duplication). body_class e.g. 'page-table' for table pages."""
    back = html_back_link(back_href) if back_link else ""
    body_attr = f' class="{body_class}"' if body_class else ""
    if use_shared_css:
        link = f'    <link href="{SHARED_CSS_FILENAME}" rel="stylesheet">'
        style_block = f'\n    <style>\n{extra_css}\n    </style>' if extra_css else ""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{link}{style_block}
</head>
<body{body_attr}>
{back}
{body_content}
</body>
</html>"""
    css = UI_CSS_BASE + (extra_css or "")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
{back}
{body_content}
</body>
</html>"""
