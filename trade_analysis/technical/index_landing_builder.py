#!/usr/bin/env python3
"""
Build index.html primary content: unicorn growth (pre-IPO) table + top tickers per sector
ranked on 7D (1W), 1M, 2M composite scores and RSI / Stoch RSI when available.

Halal-aware: skips defense/military categories and blocklisted symbols (banks, alcohol, etc.).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_TRADE_ROOT = Path(__file__).resolve().parents[1]
if str(_TRADE_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRADE_ROOT))
for _sub in ("technical", "fundamentals"):
    _p = str(_TRADE_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from exclusion_policy import EXCLUDED_CATEGORIES, is_blocklisted, load_ticker_blocklist
from html_utils import esc_html, fmt_num
from result_score_access import avg_ta_score, get_ta_block, ta_float
from scripts.rsi_stochrsi_common import fetch_stoch_rsi_for_symbol
from visualization_common import score_cell_html

# Pre-IPO / private “unicorn” watchlist (name, region, description). Not scored—research list only.
UNICORN_GROWTH_COMPANIES: Tuple[Tuple[str, str, str], ...] = (
    (
        "SpaceX",
        "US",
        "Reusable launch + Starlink; largest private space company by valuation; civil launch focus.",
    ),
    (
        "OpenAI",
        "US",
        "Foundation models (GPT); enterprise API + ChatGPT; AI infra demand driver.",
    ),
    (
        "Stripe",
        "US / IE",
        "Payments infrastructure API; fee-based model; global internet commerce rails.",
    ),
    (
        "Databricks",
        "US",
        "Data lakehouse + ML platform; enterprise AI workflow and lakehouse TAM.",
    ),
    (
        "ByteDance",
        "China",
        "TikTok / Douyin short-video; ad platform at global scale (private holding).",
    ),
    (
        "Shein",
        "China / SG",
        "Ultra-fast-fashion e-commerce; cross-border supply chain at scale.",
    ),
    (
        "Canva",
        "Australia",
        "Design SaaS for prosumer + teams; freemium with enterprise upsell.",
    ),
    (
        "Revolut",
        "UK / EU",
        "Neobank + payments app; verify non-interest revenue mix for Sharia policy.",
    ),
    (
        "Fanatics",
        "US",
        "Sports commerce + collectibles; licensing-heavy retail platform.",
    ),
    (
        "Anthropic",
        "US",
        "Claude LLM stack; enterprise safety-focused AI; Amazon/Google backing.",
    ),
    (
        "xAI",
        "US",
        "Grok models + X integration; AI lab with consumer distribution optionality.",
    ),
    (
        "Figure AI",
        "US",
        "Humanoid robotics for logistics / warehouse; early commercial pilots.",
    ),
    (
        "Horizon Robotics",
        "China",
        "ADAS + edge AI chips for autos; China EV supply chain exposure.",
    ),
    (
        "DJI",
        "China",
        "Consumer / industrial drones; global hardware scale (private).",
    ),
    (
        "Kraken",
        "US",
        "Crypto exchange (private); fee-based trading—high regulatory sensitivity.",
    ),
)

INDEX_SECTOR_SECTIONS: Tuple[Tuple[str, str], ...] = (
    ("ai_semiconductors", "AI & Semiconductors"),
    ("faang_hot_stocks", "AI Platforms & Megacap Tech"),
    ("tech_stocks", "SaaS & Enterprise Software"),
    ("miner_hpc", "AI Infra / Datacenter & HPC"),
    ("quantum", "Quantum & Next-Gen Compute"),
    ("renewable_energy", "Renewable Energy & Solar"),
    ("clean_energy_materials", "Clean Energy Materials (Li, Cu, REE)"),
    ("battery_storage", "Battery & Grid Storage"),
    ("next_gen_automotive", "EV & Next-Gen Automotive"),
    ("industrial_metals", "Industrial Metals & Copper"),
    ("precious_metals", "Precious Metals"),
    ("silver_miners_esg", "Silver Miners (ESG)"),
    ("consumer_discretionary", "Consumer Discretionary"),
    ("healthcare", "Health Tech, MedTech & Services"),
    ("real_estate", "Real Estate & REITs"),
    ("utilities", "Utilities & Grid"),
    ("cryptocurrencies", "Crypto & Digital Assets"),
    ("index_etfs", "Index & Sharia ETFs"),
    ("energy_commodities", "Energy Commodities"),
    ("agricultural_commodities", "Agricultural Commodities"),
)

RANK_TIMEFRAMES: Tuple[str, ...] = ("1W", "1M", "2M")  # 1W ≈ 7D in config tf_rules
TF_LABEL = {"1W": "7D (1W)", "1M": "1M", "2M": "2M"}
TOP_N_PER_SECTOR = 8


def _rank_sector_symbols(
    data: dict,
    blocklist: frozenset[str],
    allow_network: bool,
    category: str,
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """Return [(symbol, avg_score, metrics_dict), ...] sorted best first."""
    ranked: List[Tuple[str, float, Dict[str, Any]]] = []
    for sym, sym_data in data.items():
        if not isinstance(sym_data, dict):
            continue
        if is_blocklisted(sym, blocklist):
            continue
        avg = avg_ta_score(sym_data, RANK_TIMEFRAMES)
        if avg <= -9000:
            continue
        metrics: Dict[str, Any] = {"avg_score": avg}
        for tf in RANK_TIMEFRAMES:
            ta = get_ta_block(sym_data, tf)
            metrics[f"{tf}_score"] = ta_float(ta, "score")
            metrics[f"{tf}_rsi"] = ta_float(ta, "rsi")
            metrics[f"{tf}_stoch_k"] = None
            metrics[f"{tf}_stoch_d"] = None
        ranked.append((sym, avg, metrics))
    ranked.sort(key=lambda x: (-x[1], x[0]))
    top = ranked[:TOP_N_PER_SECTOR]
    if allow_network:
        n_stoch = len(top) * len(RANK_TIMEFRAMES)
        print(f"  Stoch RSI: fetching {n_stoch} series for {category}…", flush=True)
        for sym, _avg, metrics in top:
            for tf in RANK_TIMEFRAMES:
                sk, sd = fetch_stoch_rsi_for_symbol(sym, tf, category)
                metrics[f"{tf}_stoch_k"] = sk
                metrics[f"{tf}_stoch_d"] = sd
    return top


def _unicorn_table_html() -> str:
    rows = []
    for name, region, desc in UNICORN_GROWTH_COMPANIES:
        rows.append(
            f"        <tr>\n"
            f"            <td><strong>{esc_html(name)}</strong></td>\n"
            f"            <td>{esc_html(region)}</td>\n"
            f"            <td>{esc_html(desc)}</td>\n"
            "        </tr>\n"
        )
    return f"""    <section class="index-hero" id="unicorn-growth">
    <h2>🦄 Unicorn growth companies (pre-IPO)</h2>
    <p class="subtitle index-hero__note">Private companies not yet public—US, China, EU, and elsewhere. Research list only (no scores).</p>
    <table class="data-table index-unicorn-table" aria-label="Unicorn growth companies">
        <thead><tr>
            <th>Company</th>
            <th>Region</th>
            <th>Description</th>
        </tr></thead>
        <tbody>
{''.join(rows)}        </tbody>
    </table>
    </section>"""


def _sector_table_html(
    category: str,
    title: str,
    result_path: Path,
    blocklist: frozenset[str],
    allow_network: bool,
) -> str:
    if not result_path.is_file():
        return ""
    try:
        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""

    top = _rank_sector_symbols(data, blocklist, allow_network, category)
    if not top:
        return ""

    sid = f"sector-{category.replace('_', '-')}"
    header_cells = ["<th>Symbol</th>", "<th>Avg score</th>"]
    for tf in RANK_TIMEFRAMES:
        label = TF_LABEL[tf]
        header_cells.extend(
            [
                f"<th>{label}<br><small>Score</small></th>",
                f"<th>{label}<br><small>RSI</small></th>",
                f"<th>{label}<br><small>Stoch %K</small></th>",
            ]
        )
    header_row = "\n            ".join(header_cells)

    body_rows: List[str] = []
    for sym, avg, m in top:
        cells = [f"<td><strong>{esc_html(sym)}</strong></td>"]
        cells.append(score_cell_html(round(avg, 1)))
        for tf in RANK_TIMEFRAMES:
            sc = m.get(f"{tf}_score")
            cells.append(score_cell_html(round(sc, 1) if sc is not None else None))
            cells.append(f"<td>{fmt_num(m.get(f'{tf}_rsi'))}</td>")
            sk = m.get(f"{tf}_stoch_k")
            cells.append(f"<td>{fmt_num(sk)}</td>")
        body_rows.append("        <tr>\n            " + "\n            ".join(cells) + "\n        </tr>")

    scores_link = f"{category}_scores.html"
    return f"""
    <details class="index-fold index-sector-fold" id="{sid}">
        <summary>{esc_html(title)} — top {TOP_N_PER_SECTOR} by avg 7D/1M/2M score (halal screen)</summary>
        <div class="index-fold__body">
            <p class="subtitle">Ranked by average composite score (includes RSI, MACD, volume, etc.) on <strong>7D (1W)</strong>, <strong>1M</strong>, and <strong>2M</strong> vs USD. RSI from result JSON; Stoch RSI refreshed on index rebuild when network is enabled. Excludes military/defense, adult, alcohol, pharma/drugs, banks, gambling. <a href="{scores_link}" target="_blank">Full { esc_html(title) } page →</a></p>
            <div class="index-table-scroll">
            <table class="data-table index-sector-table">
                <thead><tr>
            {header_row}
                </tr></thead>
                <tbody>
{chr(10).join(body_rows)}
                </tbody>
            </table>
            </div>
        </div>
    </details>"""


def build_sector_tops_html(
    result_dir: Path,
    allow_network: bool = True,
) -> str:
    blocklist = load_ticker_blocklist()
    parts: List[str] = [
        '    <section class="index-sector-tops" id="sector-tops">',
        "    <h2>📈 Top companies by sector</h2>",
        '    <p class="subtitle">Expand a sector for leaders on <strong>7D, 1M, and 2M</strong> RSI / Stoch RSI and composite scores. Sectors collapsed by default—use Expand all below.</p>',
    ]
    for cat, title in INDEX_SECTOR_SECTIONS:
        if cat in EXCLUDED_CATEGORIES:
            continue
        path = result_dir / f"{cat}_results.json"
        block = _sector_table_html(cat, title, path, blocklist, allow_network)
        if block.strip():
            parts.append(block)
    parts.append("    </section>")
    return "\n".join(parts)


def build_index_primary_html(
    result_dir: Path,
    allow_network: bool = True,
) -> str:
    """Unicorn block + sector tops (always visible hero + collapsible sector tables)."""
    return _unicorn_table_html() + "\n" + build_sector_tops_html(result_dir, allow_network=allow_network)
