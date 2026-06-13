"""
Modular static assets (CSS/JS strings) and Hot pick plan HTML builder.
Generated pages write these to visualizations_output/*.css and *.js
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import List, Optional, Tuple

# --- index landing (linked from index.html only) ---

INDEX_LANDING_CSS = """
.index-toc {
  display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: center;
  margin: 8px 0 28px; padding: 14px 16px; background: #fff; border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; max-width: 920px; margin-left: auto; margin-right: auto;
}
.index-toc__label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-right: 8px; }
.index-toc a { color: #0369a1; font-weight: 600; text-decoration: none; padding: 6px 12px; border-radius: 999px; background: #e0f2fe; }
.index-toc a:hover { background: #bae6fd; text-decoration: none; }
.index-landing { max-width: 1000px; margin: 0 auto; }
.index-fold { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.index-fold > summary {
  list-style: none; cursor: pointer; padding: 16px 20px; font-size: 1.2rem; font-weight: 700; color: #1e293b;
  display: flex; align-items: center; justify-content: space-between; user-select: none;
}
.index-fold > summary::-webkit-details-marker { display: none; }
.index-fold > summary::after { content: "▼"; font-size: 0.65em; color: #64748b; transition: transform 0.2s; }
.index-fold:not([open]) > summary::after { transform: rotate(-90deg); }
.index-fold__body { padding: 0 20px 20px; }
.index-fold__body h2, .index-fold__body .main-cards-grid { margin-top: 0; }
.index-fold__toolbar { text-align: right; margin: 0 0 8px; font-size: 0.85rem; }
.index-fold__toolbar button { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; margin-left: 6px; cursor: pointer; font: inherit; color: #334155; }
.index-fold__toolbar button:hover { background: #e2e8f0; }
.main-cards-grid--three { max-width: 1100px; }
.index-hero { max-width: 1100px; margin: 0 auto 28px; padding: 18px 20px; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.index-hero h2 { margin: 0 0 8px; color: #1e293b; font-size: 1.35rem; }
.index-hero__note { margin: 0 0 14px; max-width: 900px; }
.index-sector-tops { max-width: 1100px; margin: 0 auto 24px; }
.index-sector-tops > h2 { text-align: center; color: #1e293b; margin-bottom: 8px; }
.index-sector-fold { margin-bottom: 10px; }
.index-table-scroll { overflow-x: auto; }
.index-sector-table td, .index-sector-table th, .index-unicorn-table td, .index-unicorn-table th { font-size: 0.88rem; padding: 8px 10px; }
.index-legacy { margin-top: 32px; border-top: 1px solid #e2e8f0; padding-top: 8px; }
.index-legacy > summary { color: #64748b; font-size: 0.95rem; }
"""

INDEX_LANDING_JS = """
(function () {
  function allDetails() {
    return document.querySelectorAll(".index-landing details.index-fold");
  }
  var ex = document.getElementById("index-fold-expand");
  var cl = document.getElementById("index-fold-collapse");
  if (ex) ex.addEventListener("click", function () { allDetails().forEach(function (d) { d.open = true; }); });
  if (cl) cl.addEventListener("click", function () { allDetails().forEach(function (d) { d.open = false; }); });
})();
"""

# --- hot pick plan page (linked from index + its own files) ---

HOT_PICK_PLAN_CSS = """
.hot-pick-page .subtitle { max-width: 800px; margin-left: auto; margin-right: auto; }
.hot-pick-criteria {
  max-width: 900px; margin: 0 auto 20px; padding: 14px 18px; background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px;
  color: #713f12; font-size: 0.9rem; line-height: 1.5;
}
.hot-pick-toc {
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 0 0 24px; padding: 12px; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0;
}
.hot-pick-toc a { font-size: 0.85rem; color: #c2410c; font-weight: 600; text-decoration: none; padding: 4px 10px; border-radius: 6px; background: #ffedd5; }
.hot-pick-toc a:hover { background: #fed7aa; }
.hot-horizon-section { margin-bottom: 12px; }
.hot-horizon-section .index-fold > summary { font-size: 1.05rem; }
.hot-horizon-section .data-table td:nth-child(4), .hot-horizon-section .data-table td:nth-child(5) { font-size: 0.88rem; line-height: 1.4; }
"""

HOT_PICK_PLAN_JS = """
(function () {
  if (window.location.hash) {
    var el = document.getElementById(window.location.hash.slice(1));
    if (el && el.classList && el.classList.contains("index-fold") && el.open === false) el.open = true;
  }
})();
"""

HOT_PICK_TABLE_HEADERS: Tuple[str, ...] = (
    "Ticker",
    "USD Price",
    "Industry / niche",
    "Fundamental reasons",
    "Technical reasons",
)

Row = Tuple[str, str, str, str, str]


def load_fundamental_rows_for_hot_pick(output_dir) -> List[Row]:
    """Load rows from visualizations_output/fundamental_hot_picks.json if valid; else fallback."""
    p = Path(output_dir) / "fundamental_hot_picks.json"
    if not p.is_file():
        return list(FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        out: List[Row] = []
        for r in data.get("rows", []):
            if isinstance(r, (list, tuple)) and len(r) >= 5:
                out.append((str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4])))
        if out:
            return out
    except (json.JSONDecodeError, OSError, TypeError):
        pass
    return list(FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS)


# Illustrative 1–6M fundamental leaders when JSON has not been generated (offline / CI).
# Run scripts/generate_fundamental_hot_picks.py to refresh from yfinance.
FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS: Tuple[Row, ...] = (
    (
        "NVDA",
        "—",
        "Semiconductors (AI compute)",
        "Illustrative: historically high EBITDA margin vs semis; datacenter growth narrative—refresh JSON for live yfinance fields.",
        "Align with ai_semiconductors_scores.html; 50/200D trend risk management.",
    ),
    (
        "MSFT",
        "—",
        "Software / cloud",
        "Illustrative: durable EBITDA + Azure/AI growth—verify revenue mix; halal screen excludes riba-heavy banking segments.",
        "Megacap tape + weekly structure; follow category HTML for timing.",
    ),
    (
        "CRWD",
        "—",
        "Cybersecurity SaaS",
        "Strong subscription gross retention narrative; check rev growth vs rule-of-40 in filings.",
        "Stage-2 resets common; confirm vs sector RS.",
    ),
    (
        "PANW",
        "—",
        "Cybersecurity platform",
        "Platform attach + margin expansion story; verify billings growth.",
        "Weekly base typical; pair with security sector scores page.",
    ),
    (
        "NET",
        "—",
        "Edge / CDN SaaS",
        "Edge TAM + developer adoption; EBITDA path vs hypergrowth years.",
        "Multi-month bases frequent; volume on breakouts.",
    ),
    (
        "DDOG",
        "—",
        "Observability SaaS",
        "Land-and-expand; enterprise traction—refresh script for YoY growth fields.",
        "Horizontal support zones common; vs IGV RS.",
    ),
    (
        "SNPS",
        "—",
        "EDA software",
        "High-margin software model; semiconductor design cycle leverage.",
        "Quality compounder tape; shallow pullbacks in uptrends.",
    ),
    (
        "CDNS",
        "—",
        "EDA software",
        "Similar EDA tailwinds; acquisition integration risk—check filings.",
        "Often correlates with SNPS; use timeframe tables for entries.",
    ),
    (
        "ANET",
        "—",
        "Datacenter switching",
        "Hyperscale networking; gross margin profile vs commodity hardware.",
        "Trend following vs semis index.",
    ),
    (
        "ZS",
        "—",
        "Zero-trust security",
        "SASE TAM; Rule of 40 trajectory—verify in ER.",
        "Volatility elevated vs megacaps; position size accordingly.",
    ),
    (
        "V",
        "—",
        "Payment network (fee-based)",
        "Transaction fee model; not NIM-based bank—cross-check Sharia policy on residual yield.",
        "Long-cycle uptrend common; use weekly risk levels.",
    ),
    (
        "MA",
        "—",
        "Payment network (fee-based)",
        "Similar to V; services attach growth.",
        "Pair with payment peers for RS.",
    ),
    (
        "MDB",
        "—",
        "Database SaaS",
        "Atlas growth + attach; path to leverage—monitor SBC.",
        "High beta software; use staged entries.",
    ),
    (
        "NOW",
        "—",
        "Enterprise workflow SaaS",
        "Large-deal enterprise motion; stable EBITDA progression at scale.",
        "Wide-range consolidations; monthly levels matter.",
    ),
    (
        "FTNT",
        "—",
        "Security / networking",
        "Product-led security + networking bundle; margin vs pure SaaS peers.",
        "RS vs cybersecurity ETF for context.",
    ),
    (
        "VEEV",
        "—",
        "Life-sciences cloud",
        "Vertical SaaS; high retention—growth estimates in consensus feeds.",
        "Lower vol growth; 200D often defines trend.",
    ),
    (
        "ENPH",
        "—",
        "Solar / storage",
        "IRA tailwind + storage attach; cyclical margin—verify inventory channel.",
        "High beta clean energy; see renewable_energy scores.",
    ),
    (
        "FSLR",
        "—",
        "Solar modules",
        "Domestic module narrative; project timing risk.",
        "Policy-sensitive; use risk/reward zones.",
    ),
    (
        "SHOP",
        "—",
        "Digital commerce",
        "Payments take rate; GMV mix—growth vs profitability tradeoffs.",
        "Liquid name; pattern traders’ weekly charts.",
    ),
    (
        "MELI",
        "—",
        "LatAm e-com + fintech",
        "Regional scale; fintech fee revenue—confirm non-interest mix for your policy.",
        "ADR liquidity; EM macro sensitivity.",
    ),
    (
        "ISRG",
        "—",
        "Medical devices",
        "Installed-base recurring; procedure growth estimates from consensus.",
        "Defensive growth tape; slower but steadier trends.",
    ),
    (
        "IDXX",
        "—",
        "Animal diagnostics",
        "Recurring consumables model; pricing power narrative.",
        "Quality healthcare tape; pair with sector charts.",
    ),
)


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _rows_table(rows: List[Row]) -> str:
    th = "".join(f"            <th>{_esc(h)}</th>\n" for h in HOT_PICK_TABLE_HEADERS)
    trs = []
    for t, p, n, f, r in rows:
        trs.append(
            "        <tr>\n"
            f"            <td><strong>{_esc(t)}</strong></td>\n"
            f"            <td>{_esc(p)}</td>\n"
            f"            <td>{_esc(n)}</td>\n"
            f"            <td>{_esc(f)}</td>\n"
            f"            <td>{_esc(r)}</td>\n"
            "        </tr>\n"
        )
    return (
        f'    <table class="data-table" aria-label="Hot picks for this horizon">\n'
        f"        <thead><tr>\n{th}        </tr></thead>\n"
        f"        <tbody>\n{''.join(trs)}        </tbody>\n"
        f"    </table>\n"
    )


def _fundamental_section_html(rows: List[Row]) -> str:
    """Top-of-page block: 1–6M fundamental + halal screen (table uses same columns as horizons)."""
    return f"""
    <section class="hot-horizon-section" id="fundamental-1-6" aria-labelledby="fundamental-1-6-h">
    <details class="index-fold" open>
        <summary id="fundamental-1-6-h">1–6 month fundamental leaders (halal screen + growth/EBITDA)</summary>
        <div class="index-fold__body">
            <p class="subtitle" style="margin-top:0; max-width: 900px">
            Primary watchlist for near-term (1–6M) deploy: prioritizes
            <strong>EBITDA quality</strong> and <strong>revenue/earnings growth</strong> fields (yfinance when you run the generator),
            and excludes <strong>defense/military</strong>, alcohol, tobacco, gambling, adult, and typical interest-based banks/insurers
            (heuristic—<em>not</em> a fatwa or certification). Refresh with
            <code>python trade_analysis/fundamentals/generate_fundamental_hot_picks.py</code> from the repo root.
            </p>
{_rows_table(rows)}
        </div>
    </details>
    </section>"""


# 8 horizons × ~18-21 rows. Each horizon adds halal-aware industry coverage so the union of all horizons spans every category in index.html
# (except Space Defense, excluded by policy). Niches rotate across horizons to keep individual tables varied.
def hot_pick_horizon_blocks() -> List[Tuple[int, str, str, List[Row]]]:
    return [
        (
            3,
            "3-month",
            "horizon-3",
            [
                ("MNDY", "235", "Cloud & SaaS", "Strong top-line growth and expanding NRR; efficient subscription model.", "Weekly RSI breaking out; 50-DMA reclamation on volume."),
                ("NET", "98", "Cloud & SaaS", "Edge TAM; operating leverage vs software peers improving.", "Multi-month base; MACD histogram inflects weekly."),
                ("DDOG", "138", "Cloud & SaaS", "Observability share; enterprise expansion pattern.", "Major horizontal support; RS vs IGV turning up."),
                ("SHOP", "75", "Digital commerce", "Payments attach; GMV mix to higher margin.", "Cup-and-handle weekly; 200-DMA as dynamic support."),
                ("MELI", "2100", "Digital commerce", "LatAm e-com + fintech flywheel.", "Long support band; PPO up from OS."),
                ("ETSY", "52", "Digital commerce", "Take rate and ads tier; disciplined costs.", "RSI double bottom dailies; 12M trendline test."),
                ("IOT", "32", "Industrial IoT", "Fleet data moat; higher ARR per device.", "Ascending triangle; volume confirms accumulation."),
                ("ZBRA", "320", "Industrial IoT", "Retail/logistics barcode + RFID; civil enterprise mix; no defense lines.", "Bullish weekly engulf off 200W support; OBV reclaim."),
                ("CGNX", "32", "Industrial IoT", "Logistics machine vision; design-win pipeline.", "Coil break up; ATR expansion."),
                ("PYPL", "65", "Fintech (fee-based)", "Braintree and checkout volumes; transaction-fee revenue dominant; cost takeout.", "Down-channel failure; first higher weekly low."),
                ("FOUR", "42", "Fintech (fee-based)", "In-person and e-com payments; vertical software attach; non-interest revenue.", "RSI 50 cross from below with volume."),
                ("ADYEY", "13", "Fintech (fee-based)", "Single-platform global payments processor; pure fee-take, no consumer credit/BNPL/NIM.", "Long base after 2023 reset; weekly higher lows; OBV reversal."),
                ("BTC", "67200", "Crypto (L1)", "ETF flows; halving supply; not a savings-yield play.", "Consolidation under ATH; monthly RSI not yet extreme."),
                ("ETH", "3200", "Crypto (L1)", "Staking; rollup roadmap and fee burn theme.", "Weekly close above 200W EMA; ETH/BTC base."),
                ("SOL", "145", "Crypto (L1)", "Consumer apps; throughput leadership narrative.", "Higher cycle lows; weekly resistance test soon."),
                ("NVDA", "115", "Tech megacap (AI compute)", "Datacenter GPU dominance; Blackwell ramp and sovereign-AI deals; non-haram revenue mix.", "Bullish flag under ATH; OBV at highs; 50-DMA reclaim on volume."),
                ("MSFT", "420", "Tech megacap (cloud/AI)", "Azure AI growth; Copilot attach to E5; productivity moat with no riba/defense exposure.", "Multi-month base; weekly RSI mid-range with room; 50W support."),
                ("AAPL", "200", "Tech megacap (devices/services)", "Services margin expansion; iPhone AI cycle; mainstream Sharia indexes include despite Apple Card line.", "Tight range under ATH; weekly MACD positive cross; volume contraction."),
                ("CRM", "260", "Enterprise SaaS", "Agentic layer + margin from scale; double-digit growth est. (verify); non-bank model.", "Long base vs 2021 highs; weekly trend repair on strong ER weeks."),
                ("NOW", "800", "Enterprise workflow SaaS", "Large G2K deals; operating leverage; Rule of 40 path—check SBC in filings.", "2Y range; monthly close through midline = structural improve."),
                ("PANW", "180", "Cybersecurity platform", "Next-gen + cloud ARR; margin mix vs hardware—verify billings.", "Cup vs drawdown; sector RS in leaders when risk-on."),
                ("SNPS", "480", "EDA software", "Oligopoly EDA; very high gross margin; chip design spend tailwind.", "Quality trend; pair trade vs CDNS for beta."),
                ("CDNS", "280", "EDA software", "Similar to SNPS; AI/verification attach; M&A integration watch.", "Tight vs SNPS; use 200D as major risk."),
                ("ANET", "120", "Datacenter networking", "Hyperscale 400G+; margin vs merchant silicon competition.", "Trend vs NDR; watch for range breaks on guidance."),
                ("ZS", "210", "Zero-trust / SASE", "Replace VPN narrative; NRR and margin expansion over years.", "Higher beta; use staged entries off weekly support."),
                ("CRWD", "380", "Endpoint / cloud security", "Platform consolidation story; FCF inflection narrative—verify churn.", "Volatile leader; RS vs HACK-style peers."),
            ],
        ),
        (
            6,
            "6-month",
            "horizon-6",
            [
                ("LRCX", "72", "AI & semiconductors", "HBM/etch stack; AI capex cycle share.", "Weekly RSI through multi-year line; SOX leadership."),
                ("ASML", "880", "AI & semiconductors", "EUV backlog through decade.", "Decade box retest; weekly MACD long."),
                ("ON", "64", "AI & semiconductors", "SiC + power in EV; auto recovery tailwind.", "Bullish flag above pre-COVID highs."),
                ("UBER", "64", "Mobility & platforms", "Mobility + delivery profit; ad layer scale.", "2Y inverse H&S; OBV highs."),
                ("DASH", "120", "Mobility & platforms", "Take rate and U.S. efficiency; EBITDA up.", "Base break; gap as support."),
                ("ABNB", "120", "Mobility & platforms", "Nights and experiences; buybacks, growth not yield-reit style.", "Rounded base vs XLY; golden cross on weeklies near."),
                ("HIMS", "22", "Digital health", "DTC + access; platform optionality beyond single drug.", "Stage-2 base; vol contraction break."),
                ("VEEV", "210", "Digital health", "Life-sciences cloud; durable NRR model.", "Cup and handle to prior ATH area."),
                ("ISRG", "500", "Digital health", "Robotic surgery install base; high switching.", "Downtrend from peak resolving; 40W MAs flatten."),
                ("FSLR", "150", "Clean energy (solar)", "IRA and domestic module capacity.", "Horizontal break; 200W trend as tailwind."),
                ("NXT", "52", "Clean energy (solar)", "Racking/tracker per GW content.", "IPO base; RS vs utilities index."),
                ("ENPH", "86", "Clean energy (solar)", "Storage attach; NA residential.", "Bullish divergence weeklies; key AVWAP backtest."),
                ("BTC", "72000", "Crypto (L1)", "Institution pipes improving; options depth.", "Multiyear rectangle measure if new ATH on monthly close."),
                ("AVAX", "32", "Crypto (L1)", "Subnet growth; on-chain app share.", "Basing on BTC pair; local trend up."),
                ("NEAR", "4.8", "Crypto (L1)", "Sharding; wallet UX.", "Squeeze; weekly range break."),
                ("NEE", "70", "Renewable utility (non-solar mix)", "Largest US renewables developer; rate-base growth from grid + wind + storage.", "Multi-year base resolved; 200W support stack; weekly MACD positive."),
                ("BEP", "30", "Renewable infrastructure (hydro/wind)", "Hydro + wind + solar global IPP; long-dated PPAs; not a pure NIM yield play.", "Trend reversal off 2023 lows; OBV trend up; 50W reclaim."),
                ("AY", "22", "Renewable infrastructure (diversified)", "Operating wind/solar/transmission concessions; regulated cash flows.", "Stage-1 base; weekly compression; RS vs IFRA improving."),
                ("IREN", "11", "Crypto miner / HPC pivot", "Renewable-powered hashing transitioning to AI HPC hosting; low-cost hydro power.", "Weekly higher highs; relative strength to BTC miners; OBV at highs."),
                ("CIFR", "5", "Crypto miner / HPC pivot", "Texas hash + AI compute optionality; site portfolio for HPC conversion.", "Cup base; OBV trend confirming accumulation; volume on up days."),
                ("CORZ", "12", "HPC infrastructure (post-restructure)", "AI compute hosting contracts (e.g. CoreWeave); balance sheet reset post-Ch.11.", "Post-bankruptcy base; stage-1 weekly trend; gap as support."),
                ("FTNT", "80", "Security + networking", "Product bundling; margin vs pure SaaS; services attach.", "RS vs software; 50W risk in uptrend."),
                ("GTLB", "45", "DevSecOps platform", "AI in SDLC; land with devs—growth vs burn tradeoff in ER.", "IPO-era base; revenue beat cycles move it fast."),
                ("MDB", "200", "Database SaaS", "Atlas + vector; enterprise wins—SBC dilution watch.", "Software beta; 200D = major trend filter."),
                ("TEAM", "180", "Collaboration software", "ITSM + dev tools; margin path at scale.", "Range-bound years; break needs durable ARR guide."),
                ("HUBS", "450", "CRM / marketing SaaS", "B2B growth; acquisition efficiency—check payback metrics.", "High multiple; gap risk on guide."),
            ],
        ),
        (
            9,
            "9-month",
            "horizon-9",
            [
                ("NOW", "820", "Enterprise software", "Workflow and AI add-ons; G2K land.", "2Y range absorption; monthly close through midpoint."),
                ("CRM", "300", "Enterprise software", "Agentic copilots; margin from integration.", "Inverse H&S vs 2018-2020 analog."),
                ("MDB", "200", "Enterprise software", "Atlas + vector search; attach on apps.", "Clean higher lows since reset; 50W cross."),
                ("COST", "820", "Consumer staples - quality", "Membership + own-brand mix; not a high-yield cash story.", "Trend channel since 2019; disciplined pullbacks only."),
                ("MKC", "78", "Consumer staples - quality", "Spices and flavor compounding; emerging-market growth; non-haram product mix.", "Multi-year base; 200W flattens; weekly RSI from oversold."),
                ("MNST", "55", "Consumer staples - quality", "Energy drinks (no alcohol); brand pricing; FCF compounding.", "Stage-2 vs 2022; OBV trend; weekly MACD positive."),
                ("GEV", "160", "Power & grid equipment", "Grid AI load and replacements; spin-off focus.", "Post-spin base; order visibility years."),
                ("PWR", "220", "Power & grid equipment", "Transmission line build-out.", "Accelerating 200D slope; new highs in RS."),
                ("JCI", "72", "Power & grid equipment", "Buildings and controls; retrofit cycle.", "Cup w/ handle vs 2022 highs."),
                ("CVE", "18", "Energy - diversified E&P", "Oilsands and downstream balance sheet; variable returns.", "4-year down channel break on weekly; energy vs SPX turn."),
                ("COP", "100", "Energy - diversified E&P", "Dividend+repurchase, still growth through Permian optionality.", "Bullish weekly structure; 200W as support in uptrend."),
                ("EOG", "120", "Energy - diversified E&P", "Core inventory depth; not a ‘savings’ yield vehicle.", "Compression resolved up; CFTC spec positioning cleaner."),
                ("ETH", "3800", "Crypto (L1)", "Ecosystem and staking depth; ETF parallel narrative.", "Measured leg if prior ATH breaks with breadth."),
                ("SUI", "2.1", "Crypto (L1)", "Move + object model for apps.", "Accumulation on weekly; OI rising."),
                ("TIA", "3.2", "Crypto (modular)", "Data availability sampling growth.", "RS vs majors improving; first major S/R flip."),
                ("FCX", "48", "Industrial metals (copper)", "Copper supply deficit narrative; long-cycle electrification + grid demand; no haram exposure.", "Multi-year base; copper/SPX RS turning up; 50W reclaim."),
                ("BHP", "55", "Diversified miner (Cu/Fe/K)", "Copper + iron + potash exposure; FCF discipline; no defense lines.", "Higher lows since 2023; 200D curl; volume on up days."),
                ("RIO", "70", "Diversified miner (Cu/Fe/Li)", "Iron ore cash flow + copper growth pipeline + lithium optionality.", "Coiling under multi-year resistance; volume drying; ATR contraction."),
                ("V", "280", "Payment network (fee-based)", "Global payments volume growth; cross-border revenue mix; non-interest fees, no riba.", "Bullish channel since 2023 low; 50W support; OBV at highs."),
                ("MA", "470", "Payment network (fee-based)", "Value-added services scaling; B2B opportunity; fee-based not NIM-based.", "Stage-2 vs SPX; ATH retest; weekly RSI in healthy range."),
                ("NDAQ", "70", "Exchange operator (fees + market services)", "Market-tech and anti-financial-crime SaaS; non-interest revenue dominant.", "Multi-year ascending channel; relative strength to financials excluding banks."),
            ],
        ),
        (
            12,
            "12-month",
            "horizon-12",
            [
                ("MRNA", "38", "mRNA & biotech platform", "Pipeline beyond COVID; cancer vaccine programs.", "Multi-year H&S; sector RS improving."),
                ("BNTX", "98", "mRNA & biotech platform", "Partner economics + AI discovery.", "Basing after drawdown; weekly MACD positive."),
                ("RPRX", "32", "mRNA & biotech platform", "Royalty aggregator on approved drugs.", "Yield not ‘bank pass-through’—perpetual license model; downtrend over."),
                ("DELL", "110", "Hardware & systems", "AI server backlog; on-prem and cloud mix.", "Megaphone break; AVWAP from 2020 anchor."),
                ("HPE", "20", "Hardware & systems", "As-a-service transition; margin lift.", "Long base vs peers; 200D curl."),
                ("SMCI", "42", "Hardware & systems", "Rack density for AI; correction digesting prior run.", "Vol compression under weekly MA bundle."),
                ("PAVE", "42", "Infrastructure (ETF proxy)", "Civil and transport spend; diversified exposure.", "8-year base breakout retest; RS vs SPX."),
                ("EIFF.PA", "88", "Infrastructure (EU)", "Civil and nuclear-adjacent French engineering.", "Long rounded bottom in local currency."),
                ("AEM", "80", "Precious metals - miners", "Jurisdictions + FCF; growth via expansion.", "Bullish weekly vs gold—operating leverage."),
                ("WPM", "60", "Precious metals - miners", "Streaming; optionality in copper by-product.", "Uptrend vs PM index; 200D stack."),
                ("FNV", "150", "Precious metals - miners", "Royalty model; exploration upside.", "Monthly RS vs bullion; shallow pullback."),
                ("GDXJ", "42", "Precious metals (junior mix)", "Exploration torque if metal cycle extends.", "Stage-1 base; beta to move."),
                ("BTC", "80e3", "Crypto (L1)", "Mature ETF rails; 4Y cycle rhythm.", "Multi-month flag toward prior measured extension zone."),
                ("LTC", "90", "Crypto (payments L1)", "Diversified payments narrative; not yield farming.", "Long-term down log trend break attempt."),
                ("MNT", "0.6", "Crypto (L2 / modular)", "Restaking and rollup roadmap.", "Listings and turnover expansion."),
                ("ALB", "100", "Clean energy materials (lithium)", "Lowest-cost brine + Mt. Holland; long-cycle EV/storage demand; cycle bottom narrative.", "Multi-year H&S; first higher weekly low; 50W flatten."),
                ("MP", "18", "Clean energy materials (rare earths NA)", "Mountain Pass + downstream magnet build; reshoring policy tailwind.", "Long base; volume accumulation; 200D curl."),
                ("LAC", "5", "Clean energy materials (lithium developer)", "Strategic NA lithium asset (Thacker Pass); GM partnership; not a yield product.", "Stage-1 base; first major S/R flip; OBV reversal."),
                ("PAAS", "20", "Silver miner ESG (mid-tier)", "Diversified jurisdictions; cost discipline; metals leverage to monetary policy turn.", "Bullish weekly vs silver futures; RS to gold miners improving."),
                ("FSM", "5", "Silver miner ESG (small-cap)", "Operational turnaround; lower AISC trajectory; no defense exposure.", "Long base resolution; OBV trend; ATR expansion off lows."),
                ("MAG", "12", "Silver miner ESG (high-grade JV)", "Juanicipio JV with Fresnillo; high-grade Mexican silver; clean balance sheet.", "Trend channel; pulls to 200D shallow; weekly higher lows."),
            ],
        ),
        (
            15,
            "15-month",
            "horizon-15",
            [
                ("CAT", "380", "Heavy industry & machines", "Cycle services + autonomous mine; electrification and autonomy.", "Decade uptrend; shallow 2022-23 base digest."),
                ("DE", "400", "Heavy industry & machines", "Precision ag; autonomy and fleet optimization.", "Cup and handle; emerging markets cycle resolve."),
                ("PCAR", "98", "Heavy industry & machines", "Class 8 up-cycle; margin from mix.", "Bullish weekly compression break."),
                ("URI", "620", "Equipment rental", "PPI pass-through; utilization highs.", "Multi-year range break; buybacks, not a savings play."),
                ("GEV", "165", "Power & grid", "Order book for large transformers/rotating kit.", "Post-demerger; RS vs XLU."),
                ("EPD", "32", "Energy infrastructure (MLP)", "Fee-based take-or-pay cash flow; not a short-term ‘savings’ substitute.", "Channel on weekly; dist yield from ops not idle cash TD."),
                ("KMI", "20", "Energy infrastructure (MLP)", "Gas takeaway capacity from basins to coast.", "Higher lows since rate peak; 200D turn."),
                ("LNG", "3", "LNG & gas macro", "Contracted tolling and shipping optionality to EU/Asia demand.", "Multi-year base vs gas macro."),
                ("MTZ", "140", "Engineering & construction services", "Power transmission, telecom and clean-energy infra build; fee-for-service revenue.", "Stage-2 trend; 200D curl; weekly RS vs XLI."),
                ("EME", "440", "Engineering & construction services", "Mechanical/electrical contractor; data center + reshoring; civil-only book.", "Multi-year breakout retest; OCF compounding; shallow pullbacks only."),
                ("DY", "200", "Engineering & construction services", "Telecom infrastructure (fiber + wireless) contractor; civil-only customer base.", "Bullish weekly base; OBV at highs; 50W support."),
                ("BTC", "90e3", "Crypto (L1)", "Four-year stock-to-flow and ETF structural bid.", "Measured move of multi-year range if new highs confirm."),
                ("PENDLE", "3.5", "Crypto (DeFi yield infra)", "Yield trading markets—not bank savings, protocol-native.", "RS vs ETH; weekly trend from higher lows."),
                ("EIGEN", "1.2", "Crypto (restaking)", "Shared security narrative; early ecosystem bet.", "Post-listing base; OI and funding stabilizing."),
                ("IONQ", "12", "Quantum (trapped ion)", "Networked quantum architecture; AWS Braket presence; long-horizon speculative TAM.", "Stage-1 vs 2023 trend; weekly compression coiling; volume on up days."),
                ("RGTI", "3", "Quantum (superconducting)", "Modular chip roadmap; DOE / national-lab grants (non-defense civil research).", "Post-spec base; turnover expansion; OBV reversal off lows."),
                ("QBTS", "2.5", "Quantum (annealer)", "Optimization use cases monetized; cloud quantum service revenue.", "Volatile but deep base; first higher weekly low if quantum narrative reignites."),
                ("LULU", "260", "Consumer discretionary (athleisure)", "International growth; men's category re-acceleration; brand pricing power.", "Bullish base after 2024 reset; OBV recovery; weekly RSI from oversold."),
                ("NKE", "85", "Consumer discretionary (footwear/apparel)", "Innovation pipeline reset; wholesale rebuild; structural global brand.", "Multi-year base; 200W mean-revert setup; volume contraction signaling capitulation."),
                ("ULTA", "400", "Consumer discretionary (beauty retail)", "Premium prestige + mass mix; loyalty program depth; non-haram product mix.", "Long base; weekly MACD positive cross; first higher weekly close."),
            ],
        ),
        (
            18,
            "18-month",
            "horizon-18",
            [
                ("GOOGL", "165", "Internet & search / AI", "Ad resilience + TPU/cloud AI attach; SOTP sum-of-parts.", "Megacap with multi-year line break possible on weekly."),
                ("META", "500", "Internet & social", "Reels and AI capex; expense discipline.", "3-year range resolve; 200W stack support."),
                ("NFLX", "850", "Internet & media", "Ads and paid sharing; content ROI.", "Stage-2 vs 2022 lows; PPO through zero."),
                ("INTU", "600", "FinTech / SMB software", "QuickBooks + Credit Karma flywheel; not a bank savings substitute.", "Stage-2 base; weekly RS vs XLF and software."),
                ("ADSK", "240", "Engineering & design software", "Subscription and AI copilots; industrial digitization tailwind.", "Bullish monthly coil; OCF and margin compounding."),
                ("PANW", "180", "Cybersecurity (platform)", "SASE and AI SOC attach; best-in-breed margin profile.", "Cup-and-handle vs 2021; sector RS in leaders."),
                ("EQIX", "820", "REIT - data center", "AI power + interconnection; supply constrained.", "Long uptrend; shallow consolidations only."),
                ("AMT", "200", "REIT - cell towers", "5G and amendment revenue.", "Bullish trend since 2015; 40W = risk."),
                ("STAG", "38", "REIT - industrial", "Single-tenant; spread vs bonds through rent growth.", "Basing after rate shock; 200D curl."),
                ("PLD", "120", "REIT - industrial", "Largest global logistics REIT; coastal infill supply; data-center conversion optionality.", "Tight coiling; RS vs IYR; 200D curl."),
                ("CUBE", "42", "REIT - self storage", "Pricing power; urban infill", "3-year H&S; monthly confirm."),
                ("FRT", "102", "REIT - retail (quality)", "Open-air centers; omni-tenant re-leasing.", "Bullish weekly vs sector."),
                ("ETH", "4200", "Crypto (L1)", "Rollup-centric roadmap; not rate-product yield.", "Quadrennial rhythm + RS vs defi beta."),
                ("S", "0.2", "Crypto (modular L1/L2)", "Parallel EVM; gaming adoption.", "Deep base; turnover expansion."),
                ("HYPE", "28", "Crypto (perps DEX L1)", "On-chain perps; fee share", "Bullish structure vs prior cycle."),
                ("LLY", "780", "Healthcare (pharma - GLP-1 leader)", "Mounjaro / Zepbound platform; long-cycle obesity TAM; oncology pipeline depth.", "Long uptrend; shallow corrections only; 50W as risk."),
                ("NVO", "100", "Healthcare (pharma - GLP-1)", "Wegovy / Ozempic franchise + new pipeline (CagriSema); supply ramp visible.", "Stage-2 base after 2024 reset; weekly higher lows; 200D curl."),
                ("JNJ", "165", "Healthcare (diversified pharma + medtech)", "MedTech recovery + pharma franchise; consumer split clean; defensive compounder.", "Quiet uptrend; 50W = only meaningful risk; low-beta RS."),
                ("TSLA", "180", "Next-gen automotive (EV + AV + storage)", "Robotaxi + Optimus optionality; energy storage scaling; included in Sharia indexes.", "Multi-year range resolve attempt; 200W tested as support; OBV trend."),
                ("MBLY", "20", "Next-gen automotive (autonomous vision)", "ADAS + autonomous stack; supply to OEMs across regions; non-defense civil tech.", "Stage-1 base; first major S/R flip; volume on up days."),
                ("AUR", "8", "Next-gen automotive (autonomous trucking)", "Aurora Driver freight pilots; long-cycle structural labor / efficiency thesis.", "Post-IPO accumulation; OBV reversal; weekly higher lows."),
            ],
        ),
        (
            21,
            "21-month",
            "horizon-21",
            [
                ("LIN", "420", "Chemicals & industrial gases", "H2 and specialty merge; OCI integration synergies.", "Bullish decade channel; shallow consolidations in uptrend only."),
                ("APD", "300", "Chemicals & industrial gases", "Air separation + hydrogen; India expansion.", "Cup-and-handle; RS vs XLB."),
                ("ECL", "200", "Chemicals - water", "Nalco recurring revenue; pricing power in treated water.", "Basing since 2022; 200D curl in leaders."),
                ("HOLN.SW", "50", "Building materials (global)", "Cement and aggregates—cycle optionality, not a savings product.", "European leader; 20Y monthly trend."),
                ("VMC", "250", "Building materials (NA)", "Price + volume in aggregates; M&A in regionals.", "Break from 2018-2020 base."),
                ("MLM", "500", "Building materials (NA)", "Pricing leader in Southeast U.S. stone.", "RS to SPX; 50/200D ribbon."),
                ("CARR", "58", "HVAC & building climate", "Data center and heat pump long-cycle.", "Stage-1 vs 2022; weekly MACD cross."),
                ("TT", "320", "Climate - Trane (building)", "Global HVAC; heat pump and services mix.", "Bullish channel; 200D support in re-rated leaders."),
                ("GWW", "920", "Industrial distribution", "MRO and digital pricing; FCF to buybacks.", "Linear trend since GFC; 40W support."),
                ("FAST", "40", "Industrial distribution", "Vending and branch density; gross margin through scale.", "Bullish pole-and-flag; low vol quality."),
                ("LNG", "3.4", "Global gas value chain (repeat)", "Contracted U.S. exports to premium markets.", "Same macro story; longer-dated call on weekly."),
                ("GLNG", "28", "LNG shipping", "Voyage optionality; ton-mile demand.", "Multi-year H&S; RS to tankers/bulk index."),
                ("COIN", "260", "Crypto exchange (fee-based)", "Spot + derivatives + custody fees; institutional pipes; non-NIM revenue mix.", "Bullish base above 2024 lows; weekly RS to BTC; OBV trend."),
                ("BTC", "1.0e5", "Crypto (L1)", "Maturing 4Y cycles; institutional and sovereign narrative.", "If monthly ATH confirms, 21M+ holders trend intact."),
                ("LINK", "18", "Crypto (oracle)", "RWA and CCIP; middleware bet.", "Bullish weekly vs 2021-22 downtrend; OI and depth."),
                ("AEP", "92", "Utilities (regulated + transmission)", "Largest US transmission grid investment plan; data-center load tailwind; rate-base growth, not pure NIM.", "Long base; 200W support; weekly MACD positive."),
                ("VST", "120", "Utilities (merchant + nuclear)", "TX/PJM merchant power + nuclear baseload; data-center contracted PPAs.", "Post-2023 breakout consolidation; shallow pullbacks in uptrend."),
                ("CEG", "230", "Utilities (nuclear baseload)", "US nuclear fleet leverage to AI compute demand; long-dated PPAs with hyperscalers.", "Bullish channel since 2022 spin; weekly RSI in healthy range."),
                ("STEM", "1.5", "Battery storage (software-defined)", "Athena AI for grid + commercial storage optimization; recurring SaaS attach.", "Deep base; first major S/R flip if reached; only for risk tolerance."),
                ("FLNC", "10", "Battery storage (grid-scale BESS)", "Siemens/AES heritage; global BESS systems integrator; growing backlog.", "Stage-1 base; weekly OBV reversal; 200D curl."),
                ("EOSE", "4", "Battery storage (zinc-aqueous)", "Long-duration alternative chemistry; non-lithium safety profile; backlog growing.", "Volatile base; OI and turnover expanding; binary on commercial scale-up."),
            ],
        ),
        (
            24,
            "24-month",
            "horizon-24",
            [
                ("MOS", "32", "Agriculture & inputs", "Potash/fertilizer cycle; acreage and pricing.", "Long bottom vs ag futures; 200D turn."),
                ("NTR", "52", "Agriculture & inputs", "Low-cost N provider; repurchase and integration.", "Monthly RS vs DBA; rounded base."),
                ("CF", "80", "Agriculture & inputs", "Ammonia and N capacity in NA.", "Bullish weekly; energy vs feed spread."),
                ("UAL", "88", "Airlines", "Transatlantic and wide-body mix; repair not a casino pure-play.", "Multi-year H&S; jet fuel and ops leverage."),
                ("DAL", "48", "Airlines", "Hubs and loyalty; credit card co-brand.", "RS to XAL; 200D bull stack."),
                ("AAL", "12", "Airlines", "International recovery and fleet simplification still risk-on.", "Deep value base; only for risk tolerance."),
                ("BKNG", "3800", "Online travel (OTA)", "High take rate; AI trip planning attach.", "Long uptrend; 50W = only meaningful risk."),
                ("ABNB", "150", "Online travel (short-term) (repeat)", "Still growth + buybacks, not a yield reit", "2Y measured move on monthly if prior highs clear."),
                ("EXPE", "180", "Online travel (OTA mix)", "B2B and B2C mix; brand relaunch optionality.", "Basing vs BKNG ratio improving."),
                ("RACE", "380", "Automotive (luxury, civil only)", "Halo models; pricing power, not mass finance yield; no defense/military exposure.", "Clean bull channel; Italian luxury multiple."),
                ("GNRC", "150", "Power systems (residential + commercial)", "Civil-only generators; data-center backup, residential standby; clean tail to grid stress.", "Long base; weekly higher lows; 200D curl."),
                ("CARR", "62", "Climate (repeat 24M)", "Multi-year retrofit super-cycle thesis.", "Measured extension if 21M support holds 24M."),
                ("ETH", "5000", "Crypto (L1) (long-horizon)", "Scaling roadmap and restaking; fee and burn if activity compounds.", "Log 10Y trend; cycle peak timing vs halving and flows."),
                ("XRP", "0.5", "Crypto (payments) (speculative)", "Regulatory overhang resolution narrative; not yield farming.", "Massive 7Y base; resolution candle risk."),
                ("SPUS", "55", "Index ETFs (Sharia-screened US large-cap)", "S&P 500 Shariah Industry Exclusions ETF; pre-screened for halal-aware exposure.", "Tracks SPX-screened universe; structural compounding; no need for per-name screening."),
                ("HLAL", "60", "Index ETFs (Sharia-screened US broad)", "Wahed FTSE USA Shariah ETF; broader US screened universe than SPUS.", "Long-term uptrend; matches SPX risk-on regimes with screen overlay."),
                ("SPRE", "30", "Index ETFs (Sharia-screened real estate)", "S&P Global REIT Shariah ETF; equity REITs only (excludes mortgage REITs and high-leverage names).", "Defensive yield-from-rents profile; long-dated structural housing/logistics demand."),
                ("IAU", "60", "Macro trend (gold real-asset hedge)", "Physically-backed spot gold; monetary debasement and CB demand structural bid.", "Decade uptrend; 200W as dynamic support; new ATHs intact."),
                ("SLV", "30", "Macro trend (silver real-asset hedge)", "Physically-backed silver; industrial + monetary dual demand; lagged catch-up to gold.", "Long base; first attempt at 2011 highs in cycle; volume confirms."),
                ("IBIT", "55", "Macro trend (BTC spot ETF)", "Largest US BTC spot ETF (BlackRock); institutional pipes maturing; 4Y cycle structure.", "Tracks BTC; multi-month flag if consolidating under cycle ATH."),
            ],
        ),
    ]


def build_hot_pick_plan_content(fundamental_rows: Optional[List[Row]] = None) -> str:
    """Return inner HTML: intro + TOC + fundamental section + <details> sections with tables."""
    fr = fundamental_rows if fundamental_rows is not None else list(FUNDAMENTAL_HOT_PICK_FALLBACK_ROWS)
    blocks: List[Tuple[int, str, str, List[Row]]] = hot_pick_horizon_blocks()
    toc = ['    <nav class="hot-pick-toc" aria-label="Time horizons">']
    toc.append('        <a href="#fundamental-1-6">1–6M fund.</a>')
    for m, _label, sid, _ in blocks:
        toc.append(f'        <a href="#{sid}">{m} mo</a>')
    toc.append("    </nav>")
    intro = f"""    <p class="hot-pick-criteria" role="note">
    <strong>Scope:</strong> Illustrative “top pick” style rows plus a <a href="#fundamental-1-6">1–6 month fundamental block</a> (growth/EBITDA focus)—replace or regenerate with your pipeline.
    <strong>Halal-aware filter:</strong> excludes defense/military, alcohol, tobacco, gambling/casinos, adult content, pork-related products,
    conventional banks and insurers (interest-based revenue / NIM), and savings-like cash-yield substitutes (pure pass-through yield plays, mortgage REITs, bond funds).
    Favors growth and real-asset compounders, payment networks, fee-based exchange operators, equity REITs, infrastructure cash flows, and crypto where technicals align.
    The Index ETF row uses Sharia-screened equivalents (SPUS / HLAL / SPRE) rather than broad mainstream funds, since mainstream index funds hold excluded constituents by construction.
    Tables are ordered by <em>intended</em> technical quality over 3, 6, 9, 12, 15, 18, 21, and 24 months (shorter = nearer-term pattern edge; longer = structure and multi-year S/R).
    Niches and crypto are rotated across horizons so the full set explores every category in <a href="index.html">the index</a> (Space Defense is excluded by policy).
    </p>
{chr(10).join(toc)}
    <div class="hot-horizon-sections">
{_fundamental_section_html(fr)}
"""
    parts: List[str] = [intro]
    for m, _slug, sid, rows in blocks:
        title = f"{m}-Month hot picks"
        part = f"""
    <section class="hot-horizon-section" id="{sid}" aria-labelledby="{sid}-h">
    <details class="index-fold" open>
        <summary id="{sid}-h">{_esc(title)}</summary>
        <div class="index-fold__body">
{_rows_table(rows)}
        </div>
    </details>
    </section>"""
        parts.append(part)
    parts.append("    </div>")
    return "\n".join(parts)


def write_landing_artifacts(
    output_dir, shared_css: str = "shared.css", hot_page: str = "hot_pick_plan.html"
) -> None:
    """Write modular CSS/JS and hot_pick_plan.html into output_dir (no pandas / visualize dependency)."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    fund_rows = load_fundamental_rows_for_hot_pick(p)
    (p / "index_landing.css").write_text(INDEX_LANDING_CSS, encoding="utf-8")
    (p / "index_landing.js").write_text(INDEX_LANDING_JS, encoding="utf-8")
    (p / "hot_pick_plan.css").write_text(HOT_PICK_PLAN_CSS, encoding="utf-8")
    (p / "hot_pick_plan.js").write_text(HOT_PICK_PLAN_JS, encoding="utf-8")
    (p / hot_page).write_text(render_hot_pick_plan_page(shared_css, fund_rows), encoding="utf-8")


def render_hot_pick_plan_page(
    shared_css_link: str = "shared.css",
    fundamental_rows: Optional[List[Row]] = None,
) -> str:
    inner = build_hot_pick_plan_content(fundamental_rows)
    body = f"""<body class="page-table hot-pick-page">
{html_back_link()}
    <h1>🔥 Hot pick plan (by time horizon)</h1>
    <p class="subtitle">Ticker, USD price, industry/niche, fundamental thesis, and technical reason—per horizon, strongest technical edge first within each view. Start with <a href="#fundamental-1-6">1–6M fundamentals</a> for EBITDA/growth-filtered names.</p>
{inner}
    <script src="hot_pick_plan.js" defer></script>
</body>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hot pick plan - Technical analysis</title>
    <link href="{shared_css_link}" rel="stylesheet">
    <link href="hot_pick_plan.css" rel="stylesheet">
</head>
{body}
</html>"""


def html_back_link() -> str:
    return '    <a href="index.html" class="back">← Back to index</a>'
