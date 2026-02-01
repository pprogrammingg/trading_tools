"""
Shared constants and helpers for visualization and UI tests.
Single source of truth for section IDs, column names, and page filenames.
"""

from typing import List

# Top scorers: column order by denomination (Gold, Silver, USD), then 1M/2W/1W; then scores vs BTC/ETH (same framework)
TOP_SCORER_TFS = ["1M", "2W", "1W"]
TOP_SCORER_DENOMS = ["gold", "silver", "usd"]
TOP_SCORER_BTC_ETH_COLUMNS = ["1M BTC", "2W BTC", "1M ETH", "2W ETH"]
TOP_SCORER_BTC_ETH_KEYS = ["1M_btc", "2W_btc", "1M_eth", "2W_eth"]
# Legacy names for Elliott table (same column labels)
ELLIOTT_BTC_ETH_COLUMNS = ["1M BTC", "2W BTC", "1M ETH", "2W ETH"]
PERF_VS_KEYS = ["1M_vs_btc", "2W_vs_btc", "1M_vs_eth", "2W_vs_eth"]

# Section IDs and headers (index and standalone pages)
INDEX_SECTION_TOP_SCORERS_ID = "top-scores-by-category"
INDEX_SECTION_TOP_SCORERS_HEADER = "Top scores grouped by industry/category of investment, sorted in each group by market cap"
INDEX_SECTION_ELLIOTT_ID = "elliott-wave-count"
INDEX_SECTION_ELLIOTT_HEADER = "Elliott Wave Count"
INDEX_SECTION_CATEGORY_HEADER = "Industry / Category"

# Standalone page filenames (linked from index)
PAGE_TOP_SCORES_BY_CATEGORY = "top_scores_by_category.html"
PAGE_ELLIOTT_WAVE_COUNT = "elliott_wave_count.html"
PAGE_WEALTH_PHASE = "wealth_phase.html"
PAGE_GOLD_PRESENTATION = "gold_high_scores_presentation.html"
PAGE_CME_SUNDAY_OPEN = "cme_sunday_open.html"

# Table column headers (for generation and tests)
INDEX_TOP_SCORER_COLUMNS = (
    ["Category", "Symbol", "MktCap"]
    + [f"{tf} {('USD' if d == 'usd' else 'Gold' if d == 'gold' else 'Silver')}" for tf in TOP_SCORER_TFS for d in TOP_SCORER_DENOMS]
    + TOP_SCORER_BTC_ETH_COLUMNS
    + ["ESG"]
)
INDEX_ELLIOTT_COLUMNS = (
    ["Industry", "Symbol", "MktCap", "1M Gold", "2W Gold", "1W Gold"]
    + ELLIOTT_BTC_ETH_COLUMNS
    + ["Monthly Wave Count", "Weekly Wave Count", "2D Wave Count", "Alternative", "ESG"]
)


def table_header_cells(headers: List[str]) -> str:
    """Build <th>...</th> cells for table header row (caller wraps in <tr>)."""
    return "\n            ".join(f"<th>{h}</th>" for h in headers)
