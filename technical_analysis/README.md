# Technical Analysis System

Automated technical analysis system that calculates buy/sell scores for financial instruments using multiple technical indicators. Based on research into why RSI failed to predict gold's 1970s 600% move, this system incorporates trend-following indicators (ADX, CCI, OBV) alongside mean-reverting ones (RSI).

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full analysis (all categories)
./run_full_analysis.sh

# Run specific category
python technical_analysis.py --category faang_hot_stocks

# Force refresh all data
python technical_analysis.py --refresh

# Generate visualizations only
python visualize_scores.py

# Open all visualizations
bash open_visualizations.sh
```

## 📊 Features

### Advanced Technical Indicators

**Trend-Following Indicators** (catch major moves RSI misses):
- **ADX (Average Directional Index)**: Measures trend strength
  - ADX > 30: +2 points (very strong trend)
  - ADX > 25: +1.5 points (strong trend)
  - Would have caught gold's 1970s move that RSI missed

- **CCI (Commodity Channel Index)**: Better for commodities than RSI
  - CCI < -100: +1.5 points (oversold recovery)
  - CCI > 100: -1.5 points (overbought)
  - Designed for commodities, less false signals

- **OBV & Accumulation/Distribution**: Volume-based indicators
  - OBV trending up: +1 point (accumulation)
  - A/D trending up: +1 point (institutional buying)

**Context-Aware RSI**:
- RSI weight reduced by 50% when ADX > 25 (strong trend)
- Addresses RSI failure in strong trending markets
- Prevents false oversold signals during major bull runs

**Traditional Indicators**:
- Moving Averages (EMA50/200, SMA50/200) - Golden Cross detection
- MACD - Momentum confirmation
- GMMA - Guppy Multiple Moving Average
- Volume analysis
- Momentum (Rate of Change)
- 4-week low detection

### Multi-Timeframe Analysis

Analyzes across 5 timeframes:
- **1W**: 7 calendar days
- **2W**: 14 calendar days
- **1M**: 30 calendar days
- **2M**: 60 calendar days
- **6M**: 180 calendar days

### Dual Denomination Analysis

Each symbol analyzed in:
1. **USD**: Standard USD-denominated prices
2. **Gold**: Price converted to gold terms (price / gold_price)

Allows comparison of asset performance relative to gold.

### Category-Based Organization

Symbols organized into categories:
- `quantum`: Quantum computing stocks (IONQ, QTUM, QBTS, RGTI)
- `miner_hpc`: Mining/HPC companies (MNRS, IREN, BMNR, HUT, etc.)
- `faang_hot_stocks`: FAANG + hot tech (META, AAPL, AMZN, NFLX, GOOGL, MSFT, NVDA, TSLA, etc.)
- `tech_stocks`: Other tech stocks
- `cryptocurrencies`: Crypto pairs (BTC-USD, ETH-USD, SOL-USD)
- `precious_metals`: Futures (GC=F, SI=F, PA=F, PL=F)
- `index_etfs`: ETFs (SPY, IWM, VTWO)

## 📈 Scoring System

**Starting Score:** 0

**Score Interpretation:**
- **≥6**: Great Buy (Dark Green) - Very strong bullish signals
- **4-5**: Strong Buy (Medium Green) - Strong bullish signals
- **2-3**: OK Buy (Light Green) - Moderate bullish signals
- **0-1**: Neutral (Yellow) - Weak/neutral signals
- **<0**: Bearish (Red) - Bearish signals

**Maximum Possible Score:** ~10-12 points (increased with ADX, CCI, OBV, A/D indicators)

### Key Improvements Based on Gold RSI Research

This system addresses the historical failure of RSI to predict major moves (like gold's 1970s 600% move) by:

1. **ADX Trend Detection**: Catches strong trends that RSI misses
2. **CCI for Commodities**: Better signal quality for gold/commodities
3. **Volume Confirmation**: OBV/A/D show accumulation before price moves
4. **Context-Aware RSI**: Reduced weight in strong trends prevents false signals

See `GOLD_RSI_RESEARCH.md` for detailed research.

## 📁 Project Structure

```
technical_analysis/
├── technical_analysis.py      # Main analysis script
├── visualize_scores.py         # HTML visualization generator
├── symbols_config.json         # Symbol categories configuration
├── run_full_analysis.sh        # Full pipeline script
├── run_visualization.sh        # Visualization-only script
├── open_visualizations.sh      # Open HTML files
├── data_cache/                 # Cached market data
├── result_scores/              # JSON result files
└── visualizations_output/      # HTML visualization files
```

## 🔧 Configuration

### Symbols Configuration (`symbols_config.json`)

```json
{
  "category_name": ["SYMBOL1", "SYMBOL2", ...]
}
```

Edit this file to add/remove symbols or categories.

### Data Caching

Data is automatically cached in `data_cache/{category}/{symbol}.pkl`

**Cache Refresh Logic:**
- Data refreshed if older than last Sunday 4 PM UTC
- Use `--refresh` flag to force refresh
- Weekly refresh ensures weekly closes are captured

## 📊 Output Files

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

## 🛠️ Command Line Options

```bash
python technical_analysis.py [OPTIONS]

Options:
  --category CATEGORY     Process only this category
  --config PATH           Path to symbols config (default: symbols_config.json)
  --calculate-potential   Calculate relative potential (slower)
  --refresh               Force refresh all data (ignore cache)
```

## 📚 Documentation

All documentation is in the `docs/` folder:

- **docs/DOCUMENTATION.md**: Complete system documentation
- **docs/GOLD_RSI_RESEARCH.md**: Research on why RSI failed for gold's 1970s move
- **docs/IMPLEMENTATION_SUMMARY.md**: Implementation details of new indicators
- **docs/SCRIPTS_README.md**: Shell scripts documentation
- **docs/SENTIMENT_ANALYSIS_GUIDE.md**: Reddit sentiment analysis setup
- **docs/EMAIL_NOTIFICATION_GUIDE.md**: Email report setup
- **docs/GITHUB_SETUP.md**: GitHub Actions email setup
- **docs/HOT_STOCKS_SETUP.md**: Hot stock discovery setup
- **docs/REDDIT_APP_SETUP.md**: Reddit app creation guide

## 🔬 Technical Details

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

## ⚡ Performance

**Typical Execution Times:**
- With cache: ~3-4 seconds (all categories)
- Without cache: ~7-10 seconds (all categories)
- Data downloads: ~60-70% of total time
- Indicator calculations: ~15-20% of total time

**Cache Efficiency:**
- 100% cache hit rate when data is fresh
- Automatic weekly refresh after Sunday 4 PM UTC

## 🐛 Troubleshooting

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

## 📦 Dependencies

See `requirements.txt` for full list:
- `yfinance` - Market data
- `pandas` - Data manipulation
- `ta` - Technical analysis indicators
- `tradingview-indicators` - TradingView-style calculations
- `sendgrid` - Email notifications (optional)
- `praw` - Reddit API (optional)
- `textblob` - Sentiment analysis (optional)

## 🎯 Use Cases

1. **Stock Screening**: Identify buy/sell opportunities across categories
2. **Trend Detection**: Catch major moves that RSI misses (like gold 1970s)
3. **Commodity Analysis**: Better signals for gold/commodities with CCI
4. **Volume Analysis**: Detect accumulation before price moves
5. **Multi-Timeframe**: Analyze short-term vs long-term trends

## 📝 License & Credits

Technical analysis system for investment research.
Uses yFinance for market data.

Based on research into historical indicator performance, particularly the failure of RSI to predict gold's 1970s 600% move.
