# Transactions

Parallel to `technical_analysis/`. Holds transaction data, PnL and tax scripts, and a static UI.

## Layout

- **transaction_schema.json** — JSON schema for a single transaction (includes `account_name`, `date`, `ticker`, `action`, `quantity`, `price`, etc.).
- **2026/ … 2030/** — One folder per year; put `transactions.json` in each (you can fill manually).
- **transaction_analysis.py** — PnL by category and overall for a year. Category comes from `technical_analysis/symbols_config.json`.
- **tax_calculation.py** — Taxable gain/loss for a year; excludes accounts whose name contains `TFSA`. Methods: `Average Cost Basis`, `FIFO`, `LIFO`.
- **ui/** — Static HTML/CSS/JS: year tabs, transactions by category, yearly PnL and taxes; plus a Performance dashboard.

## Commands (from repo root)

```bash
# PnL for a year
python3 transactions/transaction_analysis.py 2026
python3 transactions/transaction_analysis.py 2026 --json

# Tax for a year (excludes TFSA)
python3 transactions/tax_calculation.py 2026 fifo
python3 transactions/tax_calculation.py 2026 "Average Cost Basis"
python3 transactions/tax_calculation.py 2026 lifo

# Regenerate UI data (summary + ticker categories + copy of year JSONs)
python3 transactions/scripts/generate_summary.py

# Optional: write performance.json for the performance dashboard
python3 transactions/scripts/performance_by_category.py
```

## UI

1. Run `python3 transactions/scripts/generate_summary.py` from the repo root.
2. Open `transactions/ui/index.html` in a browser, or serve the folder (e.g. `python3 -m http.server 8000` from `transactions/ui/` and go to `http://localhost:8000`).

- **Transactions** — Tabs = years; each tab shows PnL, tax (FIFO/LIFO/Avg Cost), and transactions grouped by category.
- **Performance** — PnL by category and year (table).
