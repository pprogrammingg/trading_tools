#!/usr/bin/env python3
"""
Tax calculation for a given year using specified cost basis method.
Excludes transactions where account_name contains 'TFSA'.
Methods: average_cost, fifo, lifo.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict

TRANSACTIONS_DIR = Path(__file__).resolve().parent


def load_transactions(year: int) -> list[dict]:
    """Load transactions for year from transactions/{year}/transactions.json."""
    path = TRANSACTIONS_DIR / str(year) / "transactions.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def exclude_tfsa(transactions: list[dict]) -> list[dict]:
    """Exclude transactions whose account_name contains 'TFSA' (case-insensitive)."""
    return [t for t in transactions if "TFSA" not in (t.get("account_name") or "").upper()]


def fifo_realized(positions: dict[str, list], ticker: str, qty: float, price: float, fees: float) -> float:
    """Match sell to earliest buys (FIFO), return taxable gain (proceeds - cost)."""
    remaining = qty
    cost_used = 0.0
    while remaining > 0 and positions[ticker]:
        lot_qty, lot_price = positions[ticker][0]
        take = min(remaining, lot_qty)
        cost_used += take * lot_price
        remaining -= take
        if take >= lot_qty:
            positions[ticker].pop(0)
        else:
            positions[ticker][0] = (lot_qty - take, lot_price)
    sold_qty = qty - remaining
    proceeds = sold_qty * price - fees
    return proceeds - cost_used


def lifo_realized(positions: dict[str, list], ticker: str, qty: float, price: float, fees: float) -> float:
    """Match sell to latest buys (LIFO), return taxable gain."""
    remaining = qty
    cost_used = 0.0
    while remaining > 0 and positions[ticker]:
        lot_qty, lot_price = positions[ticker][-1]
        take = min(remaining, lot_qty)
        cost_used += take * lot_price
        remaining -= take
        if take >= lot_qty:
            positions[ticker].pop()
        else:
            positions[ticker][-1] = (lot_qty - take, lot_price)
    sold_qty = qty - remaining
    proceeds = sold_qty * price - fees
    return proceeds - cost_used


def average_cost_realized(
    positions: dict[str, list[tuple[float, float]]],
    ticker: str,
    qty: float,
    price: float,
    fees: float,
) -> float:
    """Use average cost of all lots for this ticker; return taxable gain."""
    if not positions[ticker]:
        return 0.0
    total_qty = sum(lot[0] for lot in positions[ticker])
    total_cost = sum(lot[0] * lot[1] for lot in positions[ticker])
    avg_cost = total_cost / total_qty if total_qty else 0
    cost_used = min(qty, total_qty) * avg_cost
    # Consume from positions (FIFO for lot reduction)
    remaining = qty
    while remaining > 0 and positions[ticker]:
        lot_qty, _ = positions[ticker][0]
        take = min(remaining, lot_qty)
        remaining -= take
        if take >= lot_qty:
            positions[ticker].pop(0)
        else:
            positions[ticker][0] = (lot_qty - take, positions[ticker][0][1])
    sold_qty = qty - remaining
    proceeds = sold_qty * price - fees
    return proceeds - cost_used


def compute_taxable_gain(transactions: list[dict], method: str) -> float:
    """
    Compute total taxable gain/loss using the given method.
    method: 'average_cost', 'fifo', 'lifo'
    """
    positions: dict[str, list[tuple[float, float]]] = defaultdict(list)
    total_gain = 0.0
    sorted_tx = sorted(transactions, key=lambda t: t["date"])

    for t in sorted_tx:
        ticker = t["ticker"]
        action = t["action"].lower()
        qty = float(t["quantity"])
        price = float(t["price"])
        fees = float(t.get("fees") or 0)

        if action == "buy":
            positions[ticker].append((qty, price))
            continue

        if action != "sell":
            continue

        if method == "fifo":
            gain = fifo_realized(positions, ticker, qty, price, fees)
        elif method == "lifo":
            gain = lifo_realized(positions, ticker, qty, price, fees)
        elif method in ("average_cost", "average"):
            gain = average_cost_realized(positions, ticker, qty, price, fees)
        else:
            raise ValueError(f"Unknown method: {method}. Use average_cost, fifo, or lifo.")
        total_gain += gain

    return total_gain


def normalize_method(method: str) -> str:
    """Map user-friendly names to internal method."""
    m = method.lower().replace(" ", "_").replace("-", "_")
    if m in ("average_cost_basis", "average_cost", "average"):
        return "average_cost"
    if m == "fifo":
        return "fifo"
    if m == "lifo":
        return "lifo"
    return method


def run_tax_calculation(year: int, method: str) -> dict:
    """Exclude TFSA, then compute taxable gain with given method."""
    tx = load_transactions(year)
    taxable_tx = exclude_tfsa(tx)
    method_key = normalize_method(method)
    gain = compute_taxable_gain(taxable_tx, method_key)
    return {
        "year": year,
        "method": method,
        "included_transactions": len(taxable_tx),
        "excluded_tfsa": len(tx) - len(taxable_tx),
        "taxable_gain_or_loss": round(gain, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Tax calculation (excludes TFSA)")
    parser.add_argument("year", type=int, help="Year (e.g. 2026)")
    parser.add_argument(
        "method",
        type=str,
        nargs="?",
        default="fifo",
        help="Cost basis: Average Cost Basis, FIFO, LIFO (default: fifo)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    result = run_tax_calculation(args.year, args.method)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Year: {result['year']}  Method: {result['method']}")
    print(f"Included transactions: {result['included_transactions']}  Excluded (TFSA): {result['excluded_tfsa']}")
    print(f"Taxable gain/loss: {result['taxable_gain_or_loss']:,.2f}")


if __name__ == "__main__":
    main()
