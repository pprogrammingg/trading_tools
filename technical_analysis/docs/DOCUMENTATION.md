# Technical Analysis System Documentation

## Overview

Automated technical analysis system that calculates buy/sell scores for financial instruments using multiple technical indicators. Based on research into why RSI failed to predict gold's 1970s 600% move, this system incorporates **trend-following indicators (ADX, CCI, OBV)** alongside mean-reverting ones (RSI) to catch major moves that RSI misses.

**Key Innovation**: Context-aware RSI that reduces weight when strong trends are detected (ADX > 25), preventing false signals during major bull runs.

Analyzes symbols in both USD and Gold denominations across multiple timeframes.

## Quick Start

```bash
# Run full analysis (all categories)
./run_full_analysis.sh

# Run specific category
python technical_analysis.py --category faang_hot_stocks

# Force refresh all data
python technical_analysis.py --refresh

# Generate visualizations only
python visualize_scores.py
```

## Architecture

### Data Flow

1. **Download/Fetch** → Both terms refer to the same operation: retrieving data from yFinance
   - "Downloading" = message for gold prices (GC=F)
   - "Fetching data" = message for regular symbols
   - Both use `download_data()` function with caching

2. **Cache Check** → Checks if data exists and is fresh
   - Fresh if newer than last Sunday 4 PM UTC
   - Otherwise downloads fresh data

3. **Resample** → Converts daily data to timeframes (1W, 2W, 1M, 2M, 6M)

4. **Calculate Indicators** → Two methods:
   - `ta_library`: Standard technical analysis library
   - `tradingview_library`: TradingView-style calculations

5. **Score Calculation** → Combines indicator signals into buy/sell score

6. **Visualization** → Generates HTML tables per category

## Configuration

### Symbols Configuration (`symbols_config.json`)

```json
{
  "category_name": ["SYMBOL1", "SYMBOL2", ...]
}
```

**Categories:**
- `quantum`: Quantum computing stocks
- `miner_hpc`: Mining/HPC companies
- `faang_hot_stocks`: FAANG + hot tech stocks
- `tech_stocks`: Other tech stocks
- `cryptocurrencies`: Crypto pairs (BTC-USD, ETH-USD, etc.)
- `precious_metals`: Futures (GC=F, SI=F, etc.)
- `index_etfs`: ETFs (SPY, IWM, VTWO)

## Technical Indicators

### Core Indicators (Simplified)

1. **RSI (14 period)** - Context-aware based on trend strength
   - Oversold (<30): +2 points (reduced to +1 if ADX > 25, strong trend)
   - Slightly oversold (30-40): +1 point (reduced to +0.5 if ADX > 25)
   - Overbought (>70): -2 points (reduced to -1 if ADX > 25)
   - Approaching overbought (>65): -1 point (reduced to -0.5 if ADX > 25)
   - **Why context-aware?** RSI is mean-reverting and fails in strong trends (like gold's 1970s move). When ADX shows strong trend, RSI signals are less reliable.

2. **Moving Averages**
   - EMA50, EMA200: Trend following
   - SMA50, SMA200: Golden/Death Cross detection
   - Price above EMA50: +0.5
   - Price above EMA200: +1
   - Golden Cross (SMA50 > SMA200): +1.5
   - Death Cross: -1.5

3. **GMMA (Guppy Multiple Moving Average)**
   - Bullish (all short EMAs above long EMAs): +2
   - Early expansion: +1

4. **MACD**
   - Bullish + positive histogram: +1

5. **ATR (Average True Range)**
   - *Not used for scoring* - ATR is displayed as data only
   - Volatility is a risk metric, not a buy/sell signal
   - High volatility can indicate opportunity (crypto, growth stocks)
   - Volatility is already reflected in momentum and price action

6. **ADX (Average Directional Index)** - Trend strength indicator
   - Very strong trend (ADX > 30): +2 points
   - Strong trend (ADX > 25): +1.5 points
   - **Key insight:** ADX measures trend strength, not direction. High ADX = strong trend (up OR down). This would have caught gold's 1970s move that RSI missed.

7. **CCI (Commodity Channel Index)** - Better for commodities than RSI
   - Oversold recovery (CCI < -100): +1.5 points
   - Overbought (CCI > 100): -1.5 points
   - Bullish momentum (CCI > 0): +0.5 points
   - **Why better?** CCI was designed for commodities and is less prone to false signals in trending markets.

8. **Volume Analysis**
   - Above 120% of 20-day average: +1
   - **OBV (On-Balance Volume) trending up:** +1 (shows accumulation)
   - **Accumulation/Distribution Line trending up:** +1 (institutional buying)

9. **Momentum (Rate of Change)**
   - Very strong (>15%): +1
   - Strong (8-15%): +0.5
   - Moderate (3-8%): +0.5
   - Very negative (<-15%): -1.5
   - Negative (<-8%): -1

10. **4-Week Low**
   - At or near 4-week low: +1

### Removed Indicators

- StochRSI (redundant with RSI)
- EMA20, SMA20 (kept only 50 and 200)
- GMMA compressed (less reliable)

## Scoring System

**Starting Score:** 0

**Score Interpretation:**
- **≥6**: Great Buy (Dark Green) - Very strong bullish signals
- **4-5**: Strong Buy (Medium Green) - Strong bullish signals
- **2-3**: OK Buy (Light Green) - Moderate bullish signals
- **0-1**: Neutral (Yellow) - Weak/neutral signals
- **<0**: Bearish (Red) - Bearish signals

**Maximum Possible Score:** ~10-12 points (increased with ADX, CCI, OBV, A/D indicators)

**Key Improvements Based on Gold RSI Research:**
- **ADX** detects strong trends that RSI misses (would have caught gold's 1970s 600% move)
- **CCI** better for commodities than RSI (less false signals)
- **OBV/A/D** show accumulation before price moves
- **RSI is context-aware** - reduced weight when strong trend detected (ADX > 25)

## Data Caching

### Cache Location
`data_cache/{category}/{symbol}.pkl`

### Refresh Logic

Data is refreshed if:
1. `--refresh` flag is passed explicitly
2. Cache doesn't exist
3. Cache is older than last Sunday 4 PM UTC

**Weekly Refresh:**
- Ensures weekly closes (Sunday 4 PM UTC) are always captured
- No unnecessary downloads during the week
- Automatic refresh after Sunday 4 PM UTC

### Cache Status

Output shows `(cached)` label when using cached data:
```
Fetching data... ✓ (1256 rows) (cached) [0.20s]
```

## Timeframes

Analysis performed on calendar-day resampled periods:
- **1W**: 7 calendar days
- **2W**: 14 calendar days
- **1M**: 30 calendar days
- **2M**: 60 calendar days
- **6M**: 180 calendar days

## Denominations

Each symbol is analyzed in:
1. **USD**: Standard USD-denominated prices
2. **Gold**: Price converted to gold terms (price / gold_price)

Gold conversion allows comparison of asset performance relative to gold.

## Output Files

### Result Files
`result_scores/{category}_results.json`

Contains:
- All timeframes (1W, 2W, 1M, 2M, 6M)
- Both calculation methods (ta_library, tradingview_library)
- Both denominations (usd, gold)
- Score breakdowns

### Visualization Files
`visualizations_output/{category}_scores.html`

HTML tables showing:
- Scores by timeframe
- Color-coded by score range
- All indicators and values

## Command Line Options

```bash
python technical_analysis.py [OPTIONS]

Options:
  --category CATEGORY     Process only this category
  --config PATH           Path to symbols config (default: symbols_config.json)
  --calculate-potential   Calculate relative potential (slower)
  --refresh               Force refresh all data (ignore cache)
```

## Scripts

### `run_full_analysis.sh`
Runs complete pipeline:
1. Data generation for all categories
2. Visualization generation
3. Opens HTML files in browser

### `run_visualization.sh`
Generates visualizations from existing data and opens them.

### `open_visualizations.sh`
Opens all HTML visualization files in browser.

## Performance

**Typical Execution Times:**
- With cache: ~3-4 seconds (all categories)
- Without cache: ~7-10 seconds (all categories)
- Data downloads: ~60-70% of total time
- Indicator calculations: ~15-20% of total time

**Cache Efficiency:**
- 100% cache hit rate when data is fresh
- Automatic weekly refresh after Sunday 4 PM UTC

## Troubleshooting

### Symbol Not Found
If a symbol fails to download:
- Check symbol format (e.g., BTC-USD, GC=F)
- Verify symbol exists on Yahoo Finance
- Some symbols may not be available on yFinance

### Cache Issues
To force refresh:
```bash
python technical_analysis.py --refresh
```

To clear cache manually:
```bash
rm -rf data_cache/*
```

### Missing Dependencies
Install requirements:
```bash
pip install -r requirements.txt
```

## Technical Details

### Calculation Methods

**ta_library:**
- Uses `ta` Python library
- Standard technical analysis formulas
- More widely used

**tradingview_library:**
- Uses `tradingview-indicators` library
- Matches TradingView platform calculations
- More consistent with TradingView charts

Both methods use the same yFinance data source, only calculation libraries differ.

### Data Source

- **Primary**: yFinance (Yahoo Finance)
- **Period**: 5 years of historical data
- **Interval**: Daily (1d)
- **Auto-adjust**: Disabled (raw prices)

## License & Credits

Technical analysis system for investment research.
Uses yFinance for market data.
