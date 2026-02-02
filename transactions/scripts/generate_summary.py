#!/usr/bin/env python3
"""Generate summary.json (PnL and tax per year) for the static UI."""
import json
import sys
from pathlib import Path

# Add parent so we can import from transactions/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transaction_analysis import run_analysis as pnl_analysis, load_ticker_to_category
from tax_calculation import run_tax_calculation as tax_run

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSACTIONS_DIR = Path(__file__).resolve().parent.parent
UI_DATA = TRANSACTIONS_DIR / "ui" / "data"
SUMMARY_PATH = UI_DATA / "summary.json"
CATEGORIES_PATH = UI_DATA / "ticker_categories.json"
YEARS = (2026, 2027, 2028, 2029, 2030)


def main():
    UI_DATA.mkdir(parents=True, exist_ok=True)
    summary = {}
    for year in YEARS:
        pnl = pnl_analysis(year)
        summary[str(year)] = {
            "pnl_by_category": pnl.get("by_category", {}),
            "overall_pnl": pnl.get("overall_pnl", 0),
            "transaction_count": pnl.get("transaction_count", 0),
            "tax_fifo": tax_run(year, "fifo")["taxable_gain_or_loss"],
            "tax_lifo": tax_run(year, "lifo")["taxable_gain_or_loss"],
            "tax_average_cost": tax_run(year, "average_cost")["taxable_gain_or_loss"],
        }
        # Copy year transactions into ui/data for static UI to load
        src = TRANSACTIONS_DIR / str(year) / "transactions.json"
        if src.exists():
            dst = UI_DATA / f"{year}.json"
            with open(src) as f:
                data = json.load(f)
            with open(dst, "w") as f:
                json.dump(data, f, indent=2)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    with open(CATEGORIES_PATH, "w") as f:
        json.dump(load_ticker_to_category(), f, indent=2)
    print(f"Wrote {SUMMARY_PATH} and {CATEGORIES_PATH}")


if __name__ == "__main__":
    main()
