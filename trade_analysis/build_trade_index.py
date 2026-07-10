#!/usr/bin/env python3
"""
Build trade_analysis/index.html — single scrollable table of top N tickers.

Columns: Ticker, Description, Fundamentals, 1W/2W/1M/2M RSI & Stoch, Technical reasons (verdict + RSI/Stoch notes), Tech/Fund/Final scores.

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

from html_utils import esc_html, fmt_num  # noqa: E402
from sector_sections import INDEX_SECTOR_SECTIONS  # noqa: E402
from result_score_access import avg_and_metrics, index_tech_score  # noqa: E402
from scripts.rsi_stochrsi_common import fetch_stoch_rsi_for_symbol  # noqa: E402
from score_fundamentals import build_fundamentals_column, load_ticker_notes  # noqa: E402
from symbol_description import (  # noqa: E402
    build_symbol_description,
    load_profiles_cache,
    profile_from_metrics,
    save_profiles_cache,
)
from technical_reasons import build_technical_reasons, verdict_color, verdict_display_label  # noqa: E402
from sector_signal import (  # noqa: E402
    MAX_ETFS_PER_SECTOR,
    MAX_PICKS_PER_SECTOR,
    compute_sector_signal,
    pick_sector_index_rows,
    sector_verdict_sort_rank,
)
from universe_collectors import collect_index_rows_from_results  # noqa: E402

RANK_TFS: Tuple[str, ...] = ("1W", "2W", "1M", "2M")
TF_SHORT = {"1W": "W", "2W": "2W", "1M": "M", "2M": "2M"}
DEFAULT_LIMIT = 250
MAX_PICKS_PER_INDUSTRY = MAX_PICKS_PER_SECTOR
TOP_ETFS_PER_INDUSTRY = MAX_ETFS_PER_SECTOR
TECH_WEIGHT = 0.55
FUND_WEIGHT = 0.45

INDUSTRY_LABELS: Dict[str, str] = {k: v for k, v in INDEX_SECTOR_SECTIONS}
INDUSTRY_ORDER: Tuple[str, ...] = tuple(k for k, _ in INDEX_SECTOR_SECTIONS)

INDEX_CSS_TEXT = """
body.trade-index { max-width: 100%; margin: 0 auto; padding: 20px 12px 48px; font-family: system-ui, sans-serif; background: #f1f5f9; color: #1e293b; }
.trade-index h1 { text-align: center; margin-bottom: 6px; }
.trade-index .subtitle { text-align: center; color: #64748b; max-width: 900px; margin: 0 auto 20px; line-height: 1.5; }
.trade-index .meta { text-align: center; font-size: 0.85rem; color: #94a3b8; margin-bottom: 16px; }
.trade-index-table-wrap { overflow-x: hidden; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; max-height: 85vh; overflow-y: auto; }
.trade-index-table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.78rem; }
.trade-index-table th { position: sticky; top: 0; background: #0f766e; color: #fff; padding: 6px 3px; text-align: left; z-index: 2; font-size: 0.72rem; line-height: 1.2; }
.trade-index-table th.num { text-align: center; white-space: nowrap; }
.trade-index-table th.col-ind-sub { font-weight: 500; font-size: 0.62rem; opacity: 0.92; }
.trade-index-table td { padding: 6px 4px; border-bottom: 1px solid #e2e8f0; vertical-align: top; overflow-wrap: anywhere; }
.trade-index-table tr:hover td { background: #f8fafc; }
.trade-index-table tr.industry-header td { background: #e0f2fe; color: #0c4a6e; font-weight: 700; font-size: 0.9rem; padding: 10px 8px; border-bottom: 2px solid #7dd3fc; position: sticky; top: 36px; z-index: 1; }
.trade-index-table tr.industry-header.sector-strong-accumulation td { background: #bbf7d0; color: #14532d; border-bottom-color: #4ade80; }
.trade-index-table tr.industry-header.sector-accumulation td { background: #d1fae5; color: #14532d; border-bottom-color: #86efac; }
.trade-index-table tr.industry-header.sector-sell td { background: #ffedd5; color: #9a3412; border-bottom-color: #fdba74; }
.trade-index-table tr.industry-header.sector-strong-sell td { background: #fee2e2; color: #7f1d1d; border-bottom-color: #fca5a5; }
.trade-index-table tr.industry-header.sector-neutral td { background: #fef9c3; color: #713f12; border-bottom-color: #fde047; }
.trade-index-table tr.industry-header:hover td { background: #e0f2fe; }
.trade-index-table tr.industry-header.sector-strong-accumulation:hover td { background: #86efac; }
.trade-index-table tr.industry-header.sector-accumulation:hover td { background: #bbf7d0; }
.trade-index-table tr.industry-header.sector-sell:hover td { background: #fed7aa; }
.trade-index-table tr.industry-header.sector-strong-sell:hover td { background: #fecaca; }
.trade-index-table tr.industry-header.sector-neutral:hover td { background: #fef08a; }
.trade-index-table tr.sector-signal-row.sector-strong-accumulation td { background: #dcfce7; border-bottom: 2px solid #86efac; }
.trade-index-table tr.sector-signal-row.sector-strong-accumulation:hover td { background: #bbf7d0; }
.trade-index-table tr.sector-signal-row.sector-accumulation td { background: #ecfdf5; border-bottom: 2px solid #bbf7d0; }
.trade-index-table tr.sector-signal-row.sector-accumulation:hover td { background: #d1fae5; }
.trade-index-table tr.sector-signal-row.sector-sell td { background: #fff7ed; border-bottom: 2px solid #fed7aa; }
.trade-index-table tr.sector-signal-row.sector-sell:hover td { background: #ffedd5; }
.trade-index-table tr.sector-signal-row.sector-strong-sell td { background: #fef2f2; border-bottom: 2px solid #fecaca; }
.trade-index-table tr.sector-signal-row.sector-strong-sell:hover td { background: #fee2e2; }
.trade-index-table tr.sector-signal-row.sector-neutral td { background: #fefce8; border-bottom: 2px solid #fde68a; }
.trade-index-table tr.sector-signal-row.sector-neutral:hover td { background: #fef9c3; }
.trade-index-table .sector-signal-label { color: #0d9488; font-size: 0.72rem; }
.trade-index-table .sector-signal-call { font-weight: 700; }
.trade-index-table .sector-signal-etfs { font-size: 0.72rem; }
.trade-index-table .sector-verdict-strong-accum { color: #14532d; font-weight: 700; }
.trade-index-table .sector-verdict-accum { color: #15803d; font-weight: 700; }
.trade-index-table .sector-verdict-sell { color: #b45309; font-weight: 700; }
.trade-index-table .sector-verdict-strong-sell { color: #b91c1c; font-weight: 700; }
.trade-index-table .sector-verdict-neutral { color: #a16207; font-weight: 700; }
.trade-index-table .col-rank { width: 2.2%; }
.trade-index-table .col-ticker { width: 5.5%; }
.trade-index-table .col-desc { width: 14%; }
.trade-index-table .col-fund { width: 14%; }
.trade-index-table .col-ind { width: 2.8%; }
.trade-index-table .col-ta { width: 16%; }
.trade-index-table .col-score { width: 3.2%; }
.trade-index-table .fund-col { line-height: 1.3; font-size: 0.74rem; color: #334155; }
.trade-index-table .desc-col { line-height: 1.3; font-size: 0.74rem; color: #334155; }
.trade-index-table .desc-name { font-weight: 700; color: #0f172a; display: block; margin-bottom: 2px; }
.trade-index-table .desc-meta { display: block; font-size: 0.68rem; color: #64748b; margin-bottom: 3px; }
.trade-index-table .desc-about { display: block; color: #475569; font-size: 0.72rem; }
.trade-index-table .tech-reason-col { line-height: 1.35; font-size: 0.68rem; color: #334155; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.trade-index-table .tech-summary { font-family: system-ui, sans-serif; font-size: 0.72rem; color: #475569; display: block; margin-bottom: 4px; }
.trade-index-table .tech-verdict { font-weight: 700; font-size: 0.78rem; display: inline-block; margin-bottom: 2px; }
.trade-index-table .num { text-align: center; white-space: nowrap; font-size: 0.74rem; }
.trade-index-table .score-final { font-weight: 700; background: #ecfdf5; }
.trade-index-table .ticker { font-weight: 700; font-size: 0.76rem; overflow-wrap: normal; word-break: keep-all; }
.trade-index-links { text-align: center; margin: 16px 0; font-size: 0.9rem; }
.trade-index-links a { margin: 0 10px; color: #0d9488; font-weight: 600; }
"""


def _fetch_fundamentals(ticker: str, live: bool) -> Optional[Dict[str, Any]]:
    if not live:
        return None
    try:
        from fundamental_halal_screen import fetch_screen_info, normalize_equity_symbol

        sym = ticker.split("-")[0] if "-USD" not in ticker.upper() else ticker
        if normalize_equity_symbol(sym) is None and "-USD" not in ticker.upper():
            return None
        m = fetch_screen_info(sym)
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
    max_picks_per_industry: int,
    etfs_per_industry: int,
    result_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Top picks per niche (max 10); sections sorted by sector ETF signal."""
    from collections import defaultdict

    by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in scored:
        by_cat[r["category"]].append(r)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: (-x["final_score"], -x["tech_score"], x["symbol"]))

    industry_index = {cat: i for i, cat in enumerate(INDUSTRY_ORDER)}
    cat_plan: List[Tuple[int, int, str, List[Dict[str, Any]], Dict[str, Any]]] = []
    seen: Set[str] = set()

    def _plan_cat(cat: str) -> None:
        if cat in seen:
            return
        picks = pick_sector_index_rows(
            cat,
            by_cat.get(cat, []),
            max_picks=max_picks_per_industry,
            etfs_per_industry=etfs_per_industry,
        )
        if not picks:
            return
        seen.add(cat)
        sig = compute_sector_signal(cat, result_dir) if result_dir is not None else {"sector_verdict": "Neutral"}
        cat_plan.append(
            (
                sector_verdict_sort_rank(sig.get("sector_verdict", "Neutral")),
                industry_index.get(cat, 10_000),
                cat,
                picks,
                sig,
            )
        )

    for cat in INDUSTRY_ORDER:
        if cat in by_cat:
            _plan_cat(cat)
    for cat in sorted(by_cat.keys()):
        _plan_cat(cat)

    cat_plan.sort(key=lambda x: (x[0], x[1]))

    out: List[Dict[str, Any]] = []
    row_num = 0
    for _sort_rank, _ord_idx, cat, picks, sig in cat_plan:
        row_class = sig.get("sector_row_class", "sector-neutral")
        out.append(
            {
                "_kind": "header",
                "category": cat,
                "label": _industry_label(cat),
                "count": len(picks),
                "sector_row_class": row_class,
            }
        )
        if result_dir is not None:
            out.append({"_kind": "sector_signal", **sig})
        for r in picks:
            row_num += 1
            out.append({"_kind": "row", "_rank": row_num, **r})

    return out


def build_rows(
    limit: int,
    live_fundamentals: bool,
    stoch_rsi: bool,
    max_picks_per_industry: int = MAX_PICKS_PER_INDUSTRY,
    etfs_per_industry: int = TOP_ETFS_PER_INDUSTRY,
) -> List[Dict[str, Any]]:
    notes = load_ticker_notes()
    profiles_cache = load_profiles_cache()
    cache_updates: Dict[str, Dict[str, str]] = {}
    universe = collect_index_rows_from_results(RESULT_SCORES_DIR)
    scored: List[Dict[str, Any]] = []
    fund_as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if live_fundamentals:
        print(f"  Live fundamentals: screening {len(universe)} symbols…", flush=True)

    for sym, cat, sym_data, display, denom in universe:
        tech_avg, metrics = avg_and_metrics(sym_data, RANK_TFS, denom=denom, missing_sentinel=-999.0, stoch_key="stoch")
        if tech_avg <= -900:
            if denom == "btc_denominated" and cat == "cryptocurrencies":
                tech_score = 0.0
            else:
                continue
        else:
            tech_score = index_tech_score(tech_avg, metrics, RANK_TFS)
        fund_m = _fetch_fundamentals(sym, live_fundamentals)
        if fund_m:
            prof = profile_from_metrics(fund_m)
            if prof:
                cache_updates[sym.upper()] = prof
        fund_text, fund_score = build_fundamentals_column(
            sym, cat, fund_m, notes, as_of_date=fund_as_of
        )
        desc_name, desc_meta, desc_about = build_symbol_description(
            sym,
            display,
            cat,
            fund_metrics=fund_m,
            notes=notes,
            profiles_cache=profiles_cache,
            category_label=_industry_label(cat),
        )
        try:
            from config_loader import get_index_ticker_label

            index_symbol = get_index_ticker_label(sym)
        except Exception:
            index_symbol = display
        if denom == "btc_denominated":
            fund_text = f"{fund_text} (BTC pair technicals)."
        final = round(FUND_WEIGHT * fund_score + TECH_WEIGHT * tech_score, 1)
        verdict, tech_reasons = build_technical_reasons(metrics, RANK_TFS, TF_SHORT)
        scored.append(
            {
                "symbol": index_symbol,
                "yahoo_symbol": sym,
                "category": cat,
                "desc_name": desc_name,
                "desc_meta": desc_meta,
                "desc_about": desc_about,
                "fundamentals": fund_text,
                "fund_score": fund_score,
                "tech_score": tech_score,
                "final_score": final,
                "metrics": metrics,
                "tech_verdict": verdict,
                "tech_reasons": tech_reasons,
                "_cat": cat,
                "_denom": denom,
            }
        )

    grouped = _group_rows_by_industry(
        scored,
        limit=limit,
        max_picks_per_industry=max_picks_per_industry,
        etfs_per_industry=etfs_per_industry,
        result_dir=RESULT_SCORES_DIR,
    )
    data_rows = [x for x in grouped if x.get("_kind") == "row"]

    if stoch_rsi:
        total = len(data_rows) * len(RANK_TFS)
        print(f"  Stoch RSI: up to {total} fetches ({len(data_rows)} tickers × {len(RANK_TFS)} TFs)…", flush=True)
        done = 0
        for item in data_rows:
            sym, cat, denom = item["yahoo_symbol"], item["_cat"], item["_denom"]
            if denom != "usd":
                continue
            for tf in RANK_TFS:
                sk, sd = fetch_stoch_rsi_for_symbol(sym, tf, cat)
                item["metrics"][f"{tf}_stoch"] = sk
                item["metrics"][f"{tf}_stoch_d"] = sd
                done += 1
                if done == 1 or done % 20 == 0 or done == total:
                    print(f"  Stoch RSI progress: {done}/{total}", flush=True)
        for item in data_rows:
            v, txt = build_technical_reasons(item["metrics"], RANK_TFS, TF_SHORT)
            item["tech_verdict"] = v
            item["tech_reasons"] = txt
    if cache_updates:
        save_profiles_cache(cache_updates)
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
    n_cols = 5 + len(RANK_TFS) * 2 + 3
    header = [
        '<th class="num col-rank">#</th>',
        '<th class="col-ticker">Ticker</th>',
        '<th class="col-desc" title="Name · industry · what they do">DESC</th>',
        '<th class="col-fund" title="Why strong / why now">Fundamentals</th>',
    ]
    _tf_titles = {"1W": "1 week", "2W": "2 weeks", "1M": "1 month", "2M": "2 months"}
    for tf in RANK_TFS:
        sh = TF_SHORT[tf]
        tt = _tf_titles[tf]
        header.extend(
            [
                f'<th class="num col-ind" title="{tt} RSI, 0–100 (30 oversold · 70 overbought)">{sh}<br><span class="col-ind-sub">RSI</span></th>',
                f'<th class="num col-ind" title="{tt} Stoch RSI %K, 0–100 (20 oversold · 80 overbought)">{sh}<br><span class="col-ind-sub">Stoch</span></th>',
            ]
        )
    header.extend(
        [
            '<th class="col-ta" title="Five-tier call from RSI/Stoch (Strong Accumulation → Strong Sell)">TA</th>',
            '<th class="num col-score" title="Technical score, 0–10 (higher = stronger setup)">Tech<br><span class="col-ind-sub">/10</span></th>',
            '<th class="num col-score" title="Fundamental score, 0–10 (margins, growth, valuation)">Fund<br><span class="col-ind-sub">/10</span></th>',
            '<th class="num col-score" title="Final score, 0–10 (55% Tech + 45% Fund)">Final<br><span class="col-ind-sub">/10</span></th>',
        ]
    )
    th_row = "\n            ".join(header)

    body_rows: List[str] = []
    for item in items:
        if item.get("_kind") == "header":
            label = esc_html(item["label"])
            cnt = item.get("count", 0)
            hdr_class = esc_html(item.get("sector_row_class", ""))
            hdr_cls = f"industry-header {hdr_class}" if hdr_class else "industry-header"
            body_rows.append(
                f'        <tr class="{hdr_cls}"><td colspan="{n_cols}">{label} '
                f'<span style="font-weight:500;font-size:0.85em">({cnt} picks)</span></td></tr>'
            )
            continue
        if item.get("_kind") == "sector_signal":
            row_class = esc_html(item.get("sector_row_class", "sector-neutral"))
            text_class = esc_html(item.get("sector_verdict_text_class", "sector-verdict-neutral"))
            vlabel = esc_html(item.get("sector_verdict_display", "Neutral"))
            etf_sum = esc_html(item.get("etf_summary", ""))
            etf_labels = esc_html(item.get("etf_labels", "—"))
            cells = [
                '<td class="num">—</td>',
                '<td class="ticker sector-signal-label">Sector</td>',
                f'<td class="desc-col sector-signal-call">'
                f'<span class="tech-verdict {text_class}">{vlabel}</span></td>',
                f'<td class="fund-col sector-signal-etfs" title="{etf_sum}">'
                f"<strong>ETFs:</strong> {etf_labels}"
                f'<br><span style="font-size:0.68rem;color:#64748b">{etf_sum}</span></td>',
            ]
            for _tf in RANK_TFS:
                cells.extend(['<td class="num">—</td>', '<td class="num">—</td>'])
            cells.append(
                '<td class="tech-reason-col">'
                '<span style="font-size:0.72rem;color:#64748b">Sector call from benchmark ETFs</span>'
                "</td>"
            )
            cells.extend(['<td class="num">—</td>', '<td class="num">—</td>', '<td class="num">—</td>'])
            body_rows.append(
                f'        <tr class="sector-signal-row {row_class}">\n            '
                + "\n            ".join(cells)
                + "\n        </tr>"
            )
            continue
        r = item
        m = r["metrics"]
        cells = [
            f'<td class="num">{r["_rank"]}</td>',
            f'<td class="ticker">{esc_html(r["symbol"])}</td>',
            f'<td class="desc-col">'
            f'<span class="desc-name">{esc_html(r.get("desc_name", r["symbol"]))}</span>'
            f'<span class="desc-meta">{esc_html(r.get("desc_meta", ""))}</span>'
            f'<span class="desc-about">{esc_html(r.get("desc_about", ""))}</span>'
            f"</td>",
            f'<td class="fund-col">{esc_html(r["fundamentals"])}</td>',
        ]
        for tf in RANK_TFS:
            cells.append(f'<td class="num">{fmt_num(m.get(f"{tf}_rsi"))}</td>')
            cells.append(f'<td class="num">{fmt_num(m.get(f"{tf}_stoch"))}</td>')
        vc = verdict_color(r.get("tech_verdict", "Neutral"))
        vlabel = verdict_display_label(r.get("tech_verdict", "Neutral"))
        ta_body = esc_html(r.get("tech_reasons", "")).replace("\n", "<br>")
        cells.append(
            f'<td class="tech-reason-col">'
            f'<span class="tech-verdict" style="color:{vc}">{esc_html(vlabel)}</span><br>'
            f'<span class="tech-summary">{ta_body}</span>'
            f"</td>"
        )
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
    <p class="subtitle"><strong>{data_count}</strong> picks grouped by <strong>{group_count}</strong> market niches (up to <strong>{MAX_PICKS_PER_INDUSTRY}</strong> per sector: sector ETFs + top stocks by final score). Sections sorted <strong>Strong Accumulation → Accumulation → Neutral → Sell → Strong Sell (Get Out)</strong> by sector ETF signal. TA column uses RSI/Stoch across W · 2W · M · 2M.</p>
    <p class="meta">Generated {generated_at} UTC · Technical data: <code>technical/result_scores/</code></p>
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
    import time

    if str(_TRADE_ROOT) not in sys.path:
        sys.path.insert(0, str(_TRADE_ROOT))
    from pipeline_log import step_banner, step_done  # noqa: E402

    parser = argparse.ArgumentParser(description="Build trade_analysis/index.html")
    parser.add_argument("-n", "--limit", type=int, default=DEFAULT_LIMIT, help=f"Max rows (default {DEFAULT_LIMIT})")
    parser.add_argument("--live-fundamentals", action="store_true", help="Fetch yfinance for fundamental scores (slow)")
    parser.add_argument("--stoch-rsi", action="store_true", help="Compute Stoch RSI from cached OHLCV (slow)")
    parser.add_argument(
        "--max-picks-per-sector",
        type=int,
        default=MAX_PICKS_PER_INDUSTRY,
        help=f"Max rows per sector including ETFs (default {MAX_PICKS_PER_INDUSTRY})",
    )
    parser.add_argument(
        "--etfs-per-industry",
        type=int,
        default=TOP_ETFS_PER_INDUSTRY,
        help=f"Max sector benchmark ETFs per industry (default {TOP_ETFS_PER_INDUSTRY}; from sector_etfs.json)",
    )
    args = parser.parse_args()
    t0 = time.time()
    step_banner(
        "Unified trade index",
        limit=args.limit,
        max_picks_per_industry=args.max_picks_per_sector,
        etfs_per_industry=args.etfs_per_industry,
        live_fundamentals="yes" if args.live_fundamentals else "no",
        stoch_rsi="yes" if args.stoch_rsi else "no",
        output=str(INDEX_HTML),
    )

    items = build_rows(
        args.limit,
        args.live_fundamentals,
        args.stoch_rsi,
        max_picks_per_industry=args.max_picks_per_sector,
        etfs_per_industry=args.etfs_per_industry,
    )
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    INDEX_CSS.write_text(INDEX_CSS_TEXT.strip() + "\n", encoding="utf-8")
    INDEX_HTML.write_text(render_html(items, ts), encoding="utf-8")
    n = sum(1 for x in items if x.get("_kind") == "row")
    g = sum(1 for x in items if x.get("_kind") == "header")
    step_done(
        "Unified trade index",
        t0,
        rows=n,
        industry_sections=g,
        path=str(INDEX_HTML),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
