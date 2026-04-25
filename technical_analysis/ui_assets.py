"""
Modular static assets (CSS/JS strings) and Hot pick plan HTML builder.
Generated pages write these to visualizations_output/*.css and *.js
"""

from __future__ import annotations

import html
from typing import List, Tuple

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


# 8 horizons × ~15 rows: three picks each for four equity niches + three crypto; niches rotate across horizons to cover the universe
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
                ("TTMI", "38", "Industrial IoT", "Aerospace/Auto mix; book-to-bill up.", "Bullish weekly engulf off 200W support."),
                ("CGNX", "32", "Industrial IoT", "Logistics machine vision; design-win pipeline.", "Coil break up; ATR expansion."),
                ("PYPL", "65", "Fintech", "Braintree and checkout; cost takeout.", "Down-channel failure; first higher weekly low."),
                ("FOUR", "42", "Fintech", "In-person and e-com payments; attach rate and vertical software.", "RSI 50 cross from below with volume."),
                ("AFRM", "58", "Fintech", "BNPL path to positive FCF; mix shift.", "Inverse H&S dailies; OBV trend."),
                ("BTC", "67200", "Crypto (L1)", "ETF flows; halving supply; not a savings-yield play.", "Consolidation under ATH; monthly RSI not yet extreme."),
                ("ETH", "3200", "Crypto (L1)", "Staking; rollup roadmap and fee burn theme.", "Weekly close above 200W EMA; ETH/BTC base."),
                ("SOL", "145", "Crypto (L1)", "Consumer apps; throughput leadership narrative.", "Higher cycle lows; weekly resistance test soon."),
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
                ("CASY", "420", "Consumer staples - quality", "Rural c-store; fuel pass-through and unit growth.", "All-time high trend; low beta RS."),
                ("HRL", "32", "Consumer staples - quality", "Margin repair and protein innovation.", "Multi-year base; dividend growth without savings-like yield focus."),
                ("GEV", "160", "Power & grid equipment", "Grid AI load and replacements; spin-off focus.", "Post-spin base; order visibility years."),
                ("PWR", "220", "Power & grid equipment", "Transmission line build-out.", "Accelerating 200D slope; new highs in RS."),
                ("JCI", "72", "Power & grid equipment", "Buildings and controls; retrofit cycle.", "Cup w/ handle vs 2022 highs."),
                ("CVE", "18", "Energy - diversified E&P", "Oilsands and downstream balance sheet; variable returns.", "4-year down channel break on weekly; energy vs SPX turn."),
                ("COP", "100", "Energy - diversified E&P", "Dividend+repurchase, still growth through Permian optionality.", "Bullish weekly structure; 200W as support in uptrend."),
                ("EOG", "120", "Energy - diversified E&P", "Core inventory depth; not a ‘savings’ yield vehicle.", "Compression resolved up; CFTC spec positioning cleaner."),
                ("ETH", "3800", "Crypto (L1)", "Ecosystem and staking depth; ETF parallel narrative.", "Measured leg if prior ATH breaks with breadth."),
                ("SUI", "2.1", "Crypto (L1)", "Move + object model for apps.", "Accumulation on weekly; OI rising."),
                ("TIA", "3.2", "Crypto (modular)", "Data availability sampling growth.", "RS vs majors improving; first major S/R flip."),
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
                ("BAM", "42", "Alts & asset management", "Fee related earnings + deployment cycle.", "RS vs financials; monthly trend intact."),
                ("APO", "110", "Alts & asset management", "PE + insurance; carry optionality in exits.", "Clean bull channel since 2020 reset."),
                ("ARES", "120", "Alts & asset management", "Credit and PE mix; AUM with carry.", "Basing under ATH; OCF trend."),
                ("KKR", "100", "Alts & asset management", "Diversified platforms; balance sheet SOTP.", "Higher lows; 50W = dynamic support."),
                ("BTC", "90e3", "Crypto (L1)", "Four-year stock-to-flow and ETF structural bid.", "Measured move of multi-year range if new highs confirm."),
                ("PENDLE", "3.5", "Crypto (DeFi yield infra)", "Yield trading markets—not bank savings, protocol-native.", "RS vs ETH; weekly trend from higher lows."),
                ("EIGEN", "1.2", "Crypto (restaking)", "Shared security narrative; early ecosystem bet.", "Post-listing base; OI and funding stabilizing."),
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
                ("DRE", "52", "REIT - industrial", "Coastal logistics supply.", "Tight coiling; RS vs IYR."),
                ("CUBE", "42", "REIT - self storage", "Pricing power; urban infill", "3-year H&S; monthly confirm."),
                ("FRT", "102", "REIT - retail (quality)", "Open-air centers; omni-tenant re-leasing.", "Bullish weekly vs sector."),
                ("ETH", "4200", "Crypto (L1)", "Rollup-centric roadmap; not rate-product yield.", "Quadrennial rhythm + RS vs defi beta."),
                ("S", "0.2", "Crypto (modular L1/L2)", "Parallel EVM; gaming adoption.", "Deep base; turnover expansion."),
                ("HYPE", "28", "Crypto (perps DEX L1)", "On-chain perps; fee share", "Bullish structure vs prior cycle."),
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
                ("CME", "220", "Futures exchange", "Hike cycle → vol + rate product usage; not ‘savings’ NIM in the retail sense.", "Bullish monthly; shallow pullbacks in uptrend."),
                ("BTC", "1.0e5", "Crypto (L1)", "Maturing 4Y cycles; institutional and sovereign narrative.", "If monthly ATH confirms, 21M+ holders trend intact."),
                ("LINK", "18", "Crypto (oracle)", "RWA and CCIP; middleware bet.", "Bullish weekly vs 2021-22 downtrend; OI and depth."),
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
                ("HWM", "88", "Aerospace structures", "A320/B737 and civil aero backlogs; supplier to OEM platforms.", "Bullish weekly; supply chain catch-up for narrowbody ramps."),
                ("RACE", "380", "Automotive (luxury)", "Halo models; pricing power, not mass finance yield.", "Clean bull channel; Italian luxury multiple."),
                ("CMI", "280", "Diesel & power systems", "Data center backup power; emissions regs.", "Long-term uptrend; shallow PB."),
                ("CARR", "62", "Climate (repeat 24M)", "Multi-year retrofit super-cycle thesis.", "Measured extension if 21M support holds 24M."),
                ("ETH", "5000", "Crypto (L1) (long-horizon)", "Scaling roadmap and restaking; fee and burn if activity compounds.", "Log 10Y trend; cycle peak timing vs halving and flows."),
                ("XRP", "0.5", "Crypto (payments) (speculative)", "Regulatory overhang resolution narrative; not yield farming.", "Massive 7Y base; resolution candle risk."),
            ],
        ),
    ]


def build_hot_pick_plan_content() -> str:
    """Return inner HTML: intro + TOC + <details> sections with tables (no outer page wrapper)."""
    blocks: List[Tuple[int, str, str, List[Row]]] = hot_pick_horizon_blocks()
    toc = ['    <nav class="hot-pick-toc" aria-label="Time horizons">']
    for m, _label, sid, _ in blocks:
        toc.append(f'        <a href="#{sid}">{m} mo</a>')
    toc.append("    </nav>")
    intro = f"""    <p class="hot-pick-criteria" role="note">
    <strong>Scope:</strong> Illustrative “top pick” style rows only—replace with your research pipeline. Excludes defense/military, alcohol, gambling, and
    business models that mainly resemble large interest-bearing cash savings (e.g. pure pass-through bank yield plays). Favors growth, compounding, structural winners,
    and crypto where technicals align. Tables are ordered by <em>intended</em> technical quality over 3, 6, 9, 12, 15, 18, 21, and 24 months (shorter = nearer-term
    pattern edge; longer = structure and multi-year S/R). Niches and crypto are rotated across horizons so the full set explores many industries.
    </p>
{chr(10).join(toc)}
    <div class="hot-horizon-sections">"""
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
    from pathlib import Path

    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "index_landing.css").write_text(INDEX_LANDING_CSS, encoding="utf-8")
    (p / "index_landing.js").write_text(INDEX_LANDING_JS, encoding="utf-8")
    (p / "hot_pick_plan.css").write_text(HOT_PICK_PLAN_CSS, encoding="utf-8")
    (p / "hot_pick_plan.js").write_text(HOT_PICK_PLAN_JS, encoding="utf-8")
    (p / hot_page).write_text(render_hot_pick_plan_page(shared_css), encoding="utf-8")


def render_hot_pick_plan_page(shared_css_link: str = "shared.css") -> str:
    body = f"""<body class="page-table hot-pick-page">
{html_back_link()}
    <h1>🔥 Hot pick plan (by time horizon)</h1>
    <p class="subtitle">Ticker, USD price, industry/niche, fundamental thesis, and technical reason—per horizon, strongest technical edge first within each view.</p>
{build_hot_pick_plan_content()}
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
