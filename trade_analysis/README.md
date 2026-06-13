# Trade Analysis

Unified trading research workspace: **technical** indicators/scores and **fundamentals** research context.

## Layout

```
trade_analysis/
  index.html              ← main dashboard (top ~150 tickers, scrollable table)
  index.css
  build_trade_index.py    ← generates index.html
  fundamentals/           ← halal screen, research sources, ticker notes
  technical/              ← indicators, scoring, result_scores, visualizations
```

## Quick start

```bash
cd trade_analysis
source .venv/bin/activate   # or repo-root venv
pip install -r technical/requirements.txt

./run_full_analysis.sh
```

## Index table columns

| Column | Source |
|--------|--------|
| Fundamentals | `fundamentals/ticker_investment_notes.json` + optional yfinance (`--live-fundamentals`) |
| W / 2W / M / 2M RSI | `technical/result_scores/*_results.json` |
| Stoch RSI | Cached OHLCV via `--stoch-rsi` (slow) |
| Tech / Fund / Final | 55% technical avg score + 45% fundamental score |

Halal exclusions: defense, alcohol, gambling, adult, banks (see `fundamentals/fundamental_halal_screen.py`).

## Fundamentals research

See `fundamentals/RESEARCH_CONTEXT.md` and `fundamentals/research_sources.json`.
