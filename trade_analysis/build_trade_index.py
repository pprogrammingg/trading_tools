#!/usr/bin/env python3
"""
Build trade_analysis/index.html — single scrollable table of top N tickers.

Columns: Ticker, Category, Fundamentals (why strong / why now), 1W/2W/1M/2M RSI & Stoch %K,
Technical score, Fundamental score, Final score.

Usage (from repo root or trade_analysis/):
  python trade_analysis/build_trade_index.py
  python trade_analysis/build_trade_index.py --limit 200 --stoch-rsi --live-fundamentals
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Bootstrap paths before cross-package imports.
_TRADE_ROOT = Path(__file__).resolve().parent
if str(_TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRADE_ROOT))
from trade_paths import (  # noqa: E402
    INDEX_CSS,
    INDEX_HTML,
    RESULT_SCORES_DIR,
    setup_import_paths,
)

setup_import_paths()

from exclusion_policy import EXCLUDED_CATEGORIES  # noqa: E402
from html_utils import esc_html, fmt_num  # noqa: E402
from index_landing_builder import INDEX_SECTOR_SECTIONS  # noqa: E402
from result_score_access import avg_and_metrics, tech_score_to_display  # noqa: E402
from scripts.rsi_stochrsi_common import fetch_stoch_rsi_for_symbol  # noqa: E402
from score_fundamentals import build_fundamentals_column, load_ticker_notes  # noqa: E402
from universe_collectors import collect_index_rows_from_results  # noqa: E402

RANK_TFS: Tuple[str, ...] = ("1W", "2W", "1M", "2M")
TF_SHORT = {"1W": "W", "2W": "2W", "1M": "M", "2M": "2M"}
DEFAULT_LIMIT = 150
TOP_PER_INDUSTRY = 8
TECH_WEIGHT = 0.55
FUND_WEIGHT = 0.45

INDUSTRY_LABELS: Dict[str, str] = {k: v for k, v in INDEX_SECTOR_SECTIONS}
INDUSTRY_ORDER: Tuple[str, ...] = tuple(k for k, _ in INDEX_SECTOR_SECTIONS)

INDEX_CSS_TEXT = """
body.trade-index { max-width: 1600px; margin: 0 auto; padding: 20px 16px 48px; font-family: system-ui, sans-serif; background: #f1f5f9; color: #1e293b; }
.trade-index h1 { text-align: center; margin-bottom: 6px; }
.trade-index .subtitle { text-align: center; color: #64748b; max-width: 900px; margin: 0 auto 20px; line-height: 1.5; }
.trade-index .meta { text-align: center; font-size: 0.85rem; color: #94a3b8; margin-bottom: 16px; }
.trade-index-table-wrap { overflow-x: auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; max-height: 85vh; overflow-y: auto; }
.trade-index-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.trade-index-table th { position: sticky; top: 0; background: #0f766e; color: #fff; padding: 10px 8px; text-align: left; z-index: 2; white-space: nowrap; }
.trade-index-table td { padding: 8px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
.trade-index-table tr:hover td { background: #f8fafc; }
.trade-index-table tr.industry-header td { background: #e0f2fe; color: #0c4a6e; font-weight: 700; font-size: 0.95rem; padding: 12px 10px; border-bottom: 2px solid #7dd3fc; position: sticky; top: 42px; z-index: 1; }
.trade-index-table tr.industry-header:hover td { background: #e0f2fe; }
.trade-index-table .fund-col { min-width: 220px; max-width: 320px; line-height: 1.35; font-size: 0.8rem; color: #334155; }
.trade-index-table .num { text-align: center; white-space: nowrap; }
.trade-index-table .score-final { font-weight: 700; background: #ecfdf5; }
.trade-index-table .ticker { font-weight: 700; white-space: nowrap; }
.trade-index-links { text-align: center; margin: 16px 0; font-size: 0.9rem; }
.trade-index-links a { margin: 0 10px; color: #0d9488; font-weight: 600; }
"""


def _fetch_fundamentals(ticker: str, live: bool) -> Optional[Dict[str, Any]]:
    if not live:
        return None
    try:
        from fundamental_halal_screen import fetch_screen_info, normalize_equity_symbol

        if normalize_equity_symbol(ticker.split("-")[0]) is None and "-USD" not in ticker.upper():
            return None
        m = fetch_screen_info(ticker.split("-")[0] if "-USD" not in ticker.upper() else ticker)
        if m.get("excluded"):
            return None
        return m
    except Exception:
        return None


def _industry_label(category: str) -> str:
    if category in INDUSTRY_LABELS:
        return INDUSTRY_LABELS[category]
    try:
        from config_loader import get_display_name_category

        return get_display_name_category(category)
    except Exception:
        return category.replace("_", " ").title()


def _group_rows_by_industry(
    scored: List[Dict[str, Any]],
    limit: int,
    per_industry: int,
) -> List[Dict[str, Any]]:
    """Top picks per niche/industry, ordered by INDUSTRY_ORDER with section headers."""
    from collections import defaultdict

    by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in scored:
        by_cat[r["category"]].append(r)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: (-x["final_score"], -x["tech_score"], x["symbol"]))

    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    row_num = 0

    def _append_group(cat: str) -> None:
        nonlocal row_num
        picks = by_cat.get(cat, [])[:per_industry]
        if not picks:
            return
        out.append({"_kind": "header", "category": cat, "label": _industry_label(cat), "count": len(picks)})
        for r in picks:
            row_num += 1
            out.append({"_kind": "row", "_rank": row_num, **r})

    for cat in INDUSTRY_ORDER:
        if cat in by_cat:
            _append_group(cat)
            seen.add(cat)
    for cat in sorted(by_cat.keys()):
        if cat not in seen:
            _append_group(cat)

    return out


def build_rows(
    limit: int,
    live_fundamentals: bool,
    stoch_rsi: bool,
    per_industry: int = TOP_PER_INDUSTRY,
) -> List[Dict[str, Any]]:
    notes = load_ticker_notes()
    universe = collect_index_rows_from_results(RESULT_SCORES_DIR)
    scored: List[Dict[str, Any]] = []

    for sym, cat, sym_data, display, denom in universe:
        tech_avg, metrics = avg_and_metrics(sym_data, RANK_TFS, denom=denom, missing_sentinel=-999.0, stoch_key="stoch")
        if tech_avg <= -900:
            if denom == "btc_denominated" and cat == "cryptocurrencies":
                tech_score = 0.0
            else:
                continue
        else:
            tech_score = round(tech_score_to_display(tech_avg), 1)
        fund_m = _fetch_fundamentals(sym, live_fundamentals)
        fund_text, fund_score = build_fundamentals_column(sym, cat, fund_m, notes)
        if denom == "btc_denominated":
            fund_text = f"{fund_text} (BTC pair technicals)."
        final = round(FUND_WEIGHT * fund_score + TECH_WEIGHT * tech_score, 1)
        scored.append(
            {
                "symbol": display,
                "yahoo_symbol": sym,
                "category": cat,
                "fundamentals": fund_text,
                "fund_score": fund_score,
                "tech_score": tech_score,
                "final_score": final,
                "metrics": metrics,
                "_cat": cat,
                "_denom": denom,
            }
        )

    grouped = _group_rows_by_industry(scored, limit=limit, per_industry=per_industry)
    data_rows = [x for x in grouped if x.get("_kind") == "row"]

    if stoch_rsi:
        for item in data_rows:
            sym, cat, denom = item["yahoo_symbol"], item["_cat"], item["_denom"]
            if denom != "usd":
                continue
            for tf in RANK_TFS:
                sk, _sd = fetch_stoch_rsi_for_symbol(sym, tf, cat)
                item["metrics"][f"{tf}_stoch"] = sk
    return grouped


def _score_color(v: float) -> str:
    if v >= 7.5:
        return "#166534"
    if v >= 6:
        return "#15803d"
    if v >= 4.5:
        return "#ca8a04"
    return "#b45309"


def render_html(items: List[Dict[str, Any]], generated_at: str) -> str:
    n_cols = 3 + len(RANK_TFS) * 2 + 3
    header = [
        "<th>#</th>",
        "<th>Ticker</th>",
        "<th>Fundamentals (why strong / why now)</th>",
    ]
    for tf in RANK_TFS:
        sh = TF_SHORT[tf]
        header.extend(
            [
                f'<th class="num">{sh} RSI</th>',
                f'<th class="num">{sh} Stoch</th>',
            ]
        )
    header.extend(
        [
            '<th class="num">Tech</th>',
            '<th class="num">Fund</th>',
            '<th class="num">Final</th>',
        ]
    )
    th_row = "\n            ".join(header)

    body_rows: List[str] = []
    for item in items:
        if item.get("_kind") == "header":
            label = esc_html(item["label"])
            cnt = item.get("count", 0)
            body_rows.append(
                f'        <tr class="industry-header"><td colspan="{n_cols}">{label} '
                f'<span style="font-weight:500;font-size:0.85em">({cnt} picks)</span></td></tr>'
            )
            continue
        r = item
        m = r["metrics"]
        cells = [
            f'<td class="num">{r["_rank"]}</td>',
            f'<td class="ticker">{esc_html(r["symbol"])}</td>',
            f'<td class="fund-col">{esc_html(r["fundamentals"])}</td>',
        ]
        for tf in RANK_TFS:
            cells.append(f'<td class="num">{fmt_num(m.get(f"{tf}_rsi"))}</td>')
            cells.append(f'<td class="num">{fmt_num(m.get(f"{tf}_stoch"))}</td>')
        fc = _score_color(r["tech_score"])
        ff = _score_color(r["fund_score"])
        fn = _score_color(r["final_score"])
        cells.extend(
            [
                f'<td class="num" style="color:{fc};font-weight:600">{r["tech_score"]:.1f}</td>',
                f'<td class="num" style="color:{ff};font-weight:600">{r["fund_score"]:.1f}</td>',
                f'<td class="num score-final" style="color:{fn}">{r["final_score"]:.1f}</td>',
            ]
        )
        body_rows.append("        <tr>\n            " + "\n            ".join(cells) + "\n        </tr>")

    data_count = sum(1 for x in items if x.get("_kind") == "row")
    group_count = sum(1 for x in items if x.get("_kind") == "header")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trade Analysis — {data_count} picks · {group_count} industries</title>
    <link href="index.css" rel="stylesheet">
</head>
<body class="trade-index">
    <h1>📊 Trade Analysis Index</h1>
    <p class="subtitle"><strong>{data_count}</strong> picks grouped by <strong>{group_count}</strong> market niches (top {TOP_PER_INDUSTRY} per industry by final score). Excludes military/defense, adult, alcohol, pharma/drugs, banks, gambling. Crypto: top 5 non-stable + TAO + NEAR as BASE/USD and BASE/BTC.</p>
    <p class="meta">Generated {generated_at} UTC · Technical data: <code>technical/result_scores/</code></p>
    <p class="trade-index-links">
        <a href="technical/visualizations_output/hot_pick_plan.html">Hot pick plan</a>
        <a href="technical/visualizations_output/trending_industries.html">Trending industries</a>
        <a href="fundamentals/RESEARCH_CONTEXT.md">Research workflow</a>
    </p>
    <div class="trade-index-table-wrap">
        <table class="trade-index-table" aria-label="Top tickers">
            <thead><tr>
            {th_row}
            </tr></thead>
            <tbody>
{chr(10).join(body_rows)}
            </tbody>
        </table>
    </div>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build trade_analysis/index.html")
    parser.add_argument("-n", "--limit", type=int, default=DEFAULT_LIMIT, help=f"Max rows (default {DEFAULT_LIMIT})")
    parser.add_argument("--live-fundamentals", action="store_true", help="Fetch yfinance for fundamental scores (slow)")
    parser.add_argument("--stoch-rsi", action="store_true", help="Compute Stoch RSI from cached OHLCV (slow)")
    parser.add_argument(
        "--per-industry",
        type=int,
        default=TOP_PER_INDUSTRY,
        help=f"Max rows per industry/niche (default {TOP_PER_INDUSTRY})",
    )
    args = parser.parse_args()

    items = build_rows(args.limit, args.live_fundamentals, args.stoch_rsi, per_industry=args.per_industry)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    INDEX_CSS.write_text(INDEX_CSS_TEXT.strip() + "\n", encoding="utf-8")
    INDEX_HTML.write_text(render_html(items, ts), encoding="utf-8")
    n = sum(1 for x in items if x.get("_kind") == "row")
    print(f"Wrote {n} rows → {INDEX_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
