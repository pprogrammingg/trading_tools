#!/usr/bin/env python3
"""
Produce performance (PnL) by category across years.
Outputs JSON for the performance dashboard. Run from repo root.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transaction_analysis import run_analysis

TRANSACTIONS_DIR = Path(__file__).resolve().parent.parent
UI_DATA = TRANSACTIONS_DIR / "ui" / "data"
PERF_PATH = UI_DATA / "performance.json"
YEARS = (2026, 2027, 2028, 2029, 2030)


def main():
    by_year = {}
    by_category = {}
    for year in YEARS:
        result = run_analysis(year)
        by_year[str(year)] = result.get("by_category", {})
        for cat, pnl in (result.get("by_category") or {}).items():
            by_category.setdefault(cat, []).append(pnl)
    # Pad by_category so each list has len(YEARS)
    for cat in by_category:
        while len(by_category[cat]) < len(YEARS):
            by_category[cat].append(0)
    out = {
        "by_year": by_year,
        "by_category": by_category,
        "years": [str(y) for y in YEARS],
    }
    PERF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PERF_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {PERF_PATH}")


if __name__ == "__main__":
    main()
