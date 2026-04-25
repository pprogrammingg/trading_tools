#!/usr/bin/env python3
"""
Build trending_industries.html from result_scores: per-industry top 5-10 tickers with
scores vs Gold, BTC, SPX, Silver (1M/1W), ESG, Horizon, Special. Includes Index Funds section.
Run from technical_analysis/: python scripts/build_trending_industries.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from visualization_common import SHARED_CSS_FILENAME, write_shared_css, score_cell_html, score_legend_html

RESULT_DIR = ROOT / "result_scores"
OUTPUT_DIR = ROOT / "visualizations_output"
PAGE = "trending_industries.html"
MAX_TICKERS_PER_INDUSTRY = 10

# Category key -> display name for "industry" heading (Clean Energy, Web3, Index Funds, etc.)
INDUSTRY_DISPLAY_NAMES = {
    "clean_energy_materials": "Clean Energy Materials",
    "renewable_energy": "Renewable Energy",
    "battery_storage": "Battery Storage",
    "next_gen_automotive": "EV & Next-Gen Automotive",
    "miner_hpc": "Web3 / Mining & HPC",
    "quantum": "Quantum Computing",
    "cryptocurrencies": "Cryptocurrencies",
    "tech_stocks": "Tech Stocks",
    "faang_hot_stocks": "FAANG & Hot Tech",
    "ai_semiconductors": "AI & Semiconductors",
    "index_etfs": "Index Funds",
    "macro_trend": "Macro / Broad Market",
    "precious_metals": "Precious Metals",
    "silver_miners_esg": "Silver Miners (ESG)",
    "energy_commodities": "Energy Commodities",
    "industrial_metals": "Metals (Industrial & Copper)",
    "agricultural_commodities": "Agricultural Commodities",
    "real_estate": "Real Estate",
    "healthcare": "Healthcare",
    "financials": "Financials",
    "consumer_discretionary": "Consumer Discretionary",
    "utilities": "Utilities",
    "space_defense": "Space / Satellites / Defense",
}


def _score(data: dict, symbol: str, tf: str, denom: str) -> float:
    try:
        return data[symbol][tf]["yfinance"][denom]["ta_library"]["score"]
    except (KeyError, TypeError):
        return None


def _pct(data: dict, symbol: str, key: str) -> float:
    try:
        return data.get("data", {}).get(symbol, {}).get(key)
    except (KeyError, TypeError):
        return None


def _why_one_liner(
    sym: str,
    cat: str,
    g1m: float,
    g1w: float,
    s1m: float,
    s1w: float,
    u1m: float,
    u1w: float,
    ticker_notes: dict,
    horizon_special: dict,
) -> str:
    """One-liner why great investment or not: from notes, then special, then auto from scores."""
    # 1) Explicit ticker notes file
    note = ticker_notes.get(sym) if isinstance(ticker_notes, dict) else None
    if note and isinstance(note, str) and note.strip():
        return note.strip()
    # 2) Per-symbol or per-category special/why from horizon_special
    h_s = horizon_special.get(sym) or horizon_special.get(cat) or {}
    for key in ("why", "special"):
        val = h_s.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    # 3) Auto-generate from average score
    scores = [x for x in (g1m, g1w, s1m, s1w, u1m, u1w) if x is not None]
    if not scores:
        return "No score data yet."
    avg = sum(scores) / len(scores)
    if avg >= 2.0:
        return "Strong buy vs commodities; consider accumulation."
    if avg >= 0.5:
        return "Moderate buy; watch for entry."
    if avg >= -0.5:
        return "Neutral; mixed signals."
    if avg >= -1.5:
        return "Weak; reduce or hedge."
    return "Sell signals vs gold/silver/USD; avoid or short."


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_shared_css(OUTPUT_DIR)
    result_files = list(RESULT_DIR.glob("*_results.json"))
    result_files = [f for f in result_files if "esg" not in f.name and "performance" not in f.name]
    if not result_files:
        html = _page("Top Trending Industries", "    <p>No result_scores/*_results.json found. Run technical_analysis.py first.</p>")
        (OUTPUT_DIR / PAGE).write_text(html, encoding="utf-8")
        return 0

    try:
        with open(RESULT_DIR / "performance_vs_spy.json", "r") as f:
            spy_data = json.load(f)
    except Exception:
        spy_data = {}
    try:
        with open(RESULT_DIR / "performance_vs_btc_eth.json", "r") as f:
            btc_data = json.load(f)
    except Exception:
        btc_data = {}
    try:
        with open(RESULT_DIR / "esg_ratings.json", "r") as f:
            esg_data = json.load(f).get("data") or {}
    except Exception:
        esg_data = {}

    # Optional: horizon/special by category or symbol
    horizon_special_path = ROOT / "scripts" / "trending_horizon_special.json"
    horizon_special = {}
    if horizon_special_path.exists():
        try:
            with open(horizon_special_path, "r") as f:
                horizon_special = json.load(f)
        except Exception:
            pass

    # Optional: one-liner "why" per ticker (great investment or not)
    ticker_notes_path = ROOT / "scripts" / "ticker_investment_notes.json"
    ticker_notes = {}
    if ticker_notes_path.exists():
        try:
            with open(ticker_notes_path, "r", encoding="utf-8") as f:
                data_notes = json.load(f)
            ticker_notes = {k: v for k, v in data_notes.items() if not k.startswith("_") and isinstance(v, str)}
        except Exception:
            pass

    # Build Index Funds section first if present, then others; put Index Funds in order
    index_cat = "index_etfs"
    rest = [f for f in sorted(result_files) if f.stem.replace("_results", "") != index_cat]
    index_file = RESULT_DIR / f"{index_cat}_results.json"
    ordered = []
    if index_file.exists():
        ordered.append(index_file)
    ordered.extend(rest)

    sections = []
    for path in ordered:
        cat = path.stem.replace("_results", "")
        name = INDUSTRY_DISPLAY_NAMES.get(cat, cat.replace("_", " ").title())
        with open(path, "r") as f:
            data = json.load(f)
        symbols = [s for s in data.keys() if isinstance(data.get(s), dict)][:MAX_TICKERS_PER_INDUSTRY]
        rows = []
        for sym in symbols:
            g1m = _score(data, sym, "1M", "gold")
            g1w = _score(data, sym, "1W", "gold")
            s1m = _score(data, sym, "1M", "silver")
            s1w = _score(data, sym, "1W", "silver")
            u1m = _score(data, sym, "1M", "usd")
            u1w = _score(data, sym, "1W", "usd")
            spy1m = _pct(spy_data, sym, "1M_vs_spy")
            spy1w = _pct(spy_data, sym, "1W_vs_spy")
            btc1m = _pct(btc_data, sym, "1M_vs_btc")
            btc2w = _pct(btc_data, sym, "2W_vs_btc")
            esg = esg_data.get(sym)
            if esg is None:
                esg = "—"
            h_s = horizon_special.get(sym) or horizon_special.get(cat) or {}
            horizon = h_s.get("horizon") or "—"
            special = h_s.get("special") or "—"
            why = _why_one_liner(sym, cat, g1m, g1w, s1m, s1w, u1m, u1w, ticker_notes, horizon_special)
            cells = [
                f"<td>{sym}</td>",
                score_cell_html(g1m),
                score_cell_html(g1w),
                score_cell_html(s1m),
                score_cell_html(s1w),
                score_cell_html(u1m),
                score_cell_html(u1w),
                f"<td>{_f(spy1m)}</td>",
                f"<td>{_f(spy1w)}</td>",
                f"<td>{_f(btc1m)}</td>",
                f"<td>{_f(btc2w)}</td>",
                f"<td>{esg}</td>",
                f"<td>{horizon}</td>",
                f"<td>{special}</td>",
                f'<td style="max-width:220px;font-size:0.85rem;">{_escape_html(why)}</td>',
            ]
            rows.append("<tr>" + "".join(cells) + "</tr>")
        if not rows:
            continue
        table = (
            '<table class="data-table"><thead><tr><th>Ticker</th><th>Gold 1M</th><th>Gold 1W</th><th>Silver 1M</th><th>Silver 1W</th>'
            '<th>USD 1M</th><th>USD 1W</th><th>SPY 1M%</th><th>SPY 1W%</th><th>BTC 1M%</th><th>BTC 2W%</th>'
            '<th>ESG</th><th>Horizon</th><th>Special</th><th>Why</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>"
        )
        sections.append('<div class="section-block"><h2>{}</h2>\n    {}</div>'.format(name, table))

    body = score_legend_html() + "\n    " + "\n    ".join(sections)
    html = _page("Top Trending Industries", body)
    (OUTPUT_DIR / PAGE).write_text(html, encoding="utf-8")
    print("Wrote", OUTPUT_DIR / PAGE)
    return 0


def _f(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return "{:.1f}".format(v)
    return str(v)


def _escape_html(s: str) -> str:
    if not s:
        return "—"
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _page(title: str, body: str) -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{}</title>
<link href="{css}" rel="stylesheet">
</head>
<body class="page-table">
<a href="index.html" class="back">← Back to Index</a>
<h1>Top Trending Industries</h1>
<p class="subtitle">Per industry: top 5–10 tickers. Scores vs Gold, Silver, USD (1M/1W); SPY and BTC relative performance (1M%/1W% or 2W%); ESG; Horizon (long/mid/short); Special notes. Index Funds section lists SPY, Russell, international, etc.</p>
{}
</body>
</html>""".format(title, body, css=SHARED_CSS_FILENAME)


if __name__ == "__main__":
    sys.exit(main())
