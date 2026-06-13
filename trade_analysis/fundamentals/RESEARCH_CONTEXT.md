# Fundamentals research context

Use this folder when answering **“why strong?”** and **“why now?”** for a ticker row in `../index.html`.

## Workflow

1. **Halal screen** — run `fundamental_halal_screen.py` logic (sector/industry keywords). Skip defense, alcohol, tobacco, gambling, adult, pork-heavy, conventional banks/insurers.
2. **Pull metrics** — yfinance `info` for EBITDA margin, revenue/earnings growth, PEG (verify in filings).
3. **Cross-check sources** — see `research_sources.json` for preferred sites (SEC EDGAR, Macrotrends, Koyfin, CoinGecko, etc.).
4. **One-line thesis** — combine:
   - **Why strong:** durable margin, TAM, moat, balance sheet (from filings/notes).
   - **Why now:** growth inflection, score turn on 1W/1M, RS vs SPY, cycle tailwind.
5. **Optional manual notes** — add/edit `ticker_investment_notes.json` for tickers you follow closely.

## Scoring (used by `../build_trade_index.py`)

| Component | Weight | Source |
|-----------|--------|--------|
| Fundamental | 45% | `composite_score()` in `fundamental_halal_screen.py` (yfinance) or note-based fallback |
| Technical | 55% | Average USD composite score on **1W, 2W, 1M, 2M** from `technical/result_scores/*_results.json` |

**Final score** = weighted blend, scaled 0–10 for display.

## Regenerate data

```bash
cd trade_analysis/technical
../.venv/bin/python ../build_trade_index.py --limit 150
```

With live yfinance fundamentals (slower):

```bash
../.venv/bin/python ../build_trade_index.py --limit 150 --live-fundamentals
```

With Stoch RSI from cached OHLCV (slower):

```bash
../.venv/bin/python ../build_trade_index.py --limit 150 --stoch-rsi
```
