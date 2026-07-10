# Trade Analysis

Main output: **`index.html`** — scrollable table of top picks with fundamentals, per-timeframe RSI/Stoch, TA verdicts, and Tech / Fund / Final scores.

**Five-tier calls** (sector ETFs and individual picks): **Strong Accumulation** · **Accumulation** · **Neutral** · **Sell** · **Strong Sell (Get Out)**

Up to **10 picks per sector** (sector benchmark ETFs + top stocks by final score).

## One-time setup

```bash
cd trade_analysis
python3 -m venv .venv
./.venv/bin/pip install -r technical/requirements.txt
```

## Build `index.html`

| When | Command | Time |
|------|---------|------|
| **Index only** — reuse cached scores | `./.venv/bin/python build_trade_index.py` | ~seconds |
| **Normal update** — recompute technical scores + index | `./run_full_analysis.sh` | minutes |
| **Full refresh** — new OHLCV, live fundamentals, Stoch RSI | `./run_full_analysis.sh --full` | slow |

```bash
open index.html
```

## Pipeline flags

```bash
./run_full_analysis.sh                              # cached OHLCV; 10 picks/sector
./run_full_analysis.sh --refresh                    # re-download OHLCV
./run_full_analysis.sh --live-fundamentals --stoch-rsi
./run_full_analysis.sh --max-picks-per-sector 10
./run_full_analysis.sh --index-limit 250
```

Pass extra args through to `technical_analysis.py` (e.g. `./run_full_analysis.sh --category ai_semiconductors`).

## What runs

1. **Technical scores** — `technical/technical_analysis.py` → `technical/result_scores/*_results.json`
2. **Unified index** — `build_trade_index.py` → **`index.html`** + `index.css`

## Layout

```
trade_analysis/
  index.html, index.css       ← open this
  build_trade_index.py
  run_full_analysis.sh
  fundamentals/               notes, halal screen, symbol profiles cache
  technical/
    result_scores/            input JSON for the index
    sector_etfs.json          benchmark ETFs per sector
```

## Tests

```bash
./.venv/bin/python -m pytest technical/tests/test_technical_reasons.py technical/tests/test_sector_signal.py technical/tests/test_trade_index.py technical/tests/test_result_score_access.py
```

Rebuild `index.html` before `test_trade_index.py` if scores changed.
