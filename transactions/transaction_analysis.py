#!/usr/bin/env python3
"""
Transaction PnL analysis by category and overall for a given year.
Uses technical_analysis/symbols_config.json for ticker -> category lookup.
FIFO matching for realized PnL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
SYMBOLS_CONFIG = REPO_ROOT / "technical_analysis" / "symbols_config.json"
TRANSACTIONS_DIR = Path(__file__).resolve().parent


def load_ticker_to_category() -> dict[str, str]:
    """Build ticker -> category from symbols_config.json (first match wins)."""
    with open(SYMBOLS_CONFIG) as f:
        categories = json.load(f)
    ticker_to_cat = {}
    for cat, tickers in categories.items():
        for t in tickers:
            ticker_to_cat.setdefault(t, cat)
    return ticker_to_cat


def load_transactions(year: int) -> list[dict]:
    """Load transactions for year from transactions/{year}/transactions.json."""
    path = TRANSACTIONS_DIR / str(year) / "transactions.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def fifo_realized_pnl(transactions: list[dict]) -> list[tuple[str, str, float]]:
    """
    Match sells to buys (FIFO) and return list of (ticker, category, realized_pnl).
    Each element is one lot's realized PnL.
    """
    ticker_to_cat = load_ticker_to_category()
    # positions[ticker] = list of (quantity, price, date) for buys
    positions: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    realized: list[tuple[str, str, float]] = []

    sorted_tx = sorted(transactions, key=lambda t: (t["date"], t.get("notes", "")))

    for t in sorted_tx:
        ticker = t["ticker"]
        action = t["action"].lower()
        qty = float(t["quantity"])
        price = float(t["price"])
        fees = float(t.get("fees") or 0)
        date = t["date"]
        cat = ticker_to_cat.get(ticker, "other")

        if action == "buy":
            positions[ticker].append((qty, price, date))
            continue

        if action != "sell":
            continue

        remaining = qty
        cost_used = 0.0
        while remaining > 0 and positions[ticker]:
            lot_qty, lot_price, _ = positions[ticker][0]
            take = min(remaining, lot_qty)
            cost_used += take * lot_price
            remaining -= take
            if take >= lot_qty:
                positions[ticker].pop(0)
            else:
                positions[ticker][0] = (lot_qty - take, lot_price, positions[ticker][0][2])

        sold_qty = qty - remaining
        proceeds = sold_qty * price - fees
        pnl = proceeds - cost_used
        realized.append((ticker, cat, pnl))

    return realized


def run_analysis(year: int) -> dict:
    """Compute PnL by category and overall for the year."""
    tx = load_transactions(year)
    if not tx:
        return {"year": year, "by_category": {}, "overall_pnl": 0.0, "transaction_count": 0}

    realized = fifo_realized_pnl(tx)
    by_category: dict[str, float] = defaultdict(float)
    for _ticker, cat, pnl in realized:
        by_category[cat] += pnl
    overall = sum(p for _t, _c, p in realized)

    return {
        "year": year,
        "by_category": dict(by_category),
        "overall_pnl": round(overall, 2),
        "transaction_count": len(tx),
    }


def main():
    parser = argparse.ArgumentParser(description="Transaction PnL analysis by year")
    parser.add_argument("year", type=int, help="Year (e.g. 2026)")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    result = run_analysis(args.year)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Year: {result['year']}  Transactions: {result['transaction_count']}")
    print("PnL by category:")
    for cat, pnl in sorted(result["by_category"].items(), key=lambda x: -abs(x[1])):
        print(f"  {cat}: {pnl:,.2f}")
    print(f"Overall PnL: {result['overall_pnl']:,.2f}")


if __name__ == "__main__":
    main()
