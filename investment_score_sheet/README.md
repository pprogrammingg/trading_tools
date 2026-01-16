# Technical Analysis Scoring System

This tool calculates technical indicators and generates buy/sell scores for financial instruments using data from Yahoo Finance (yFinance). Each symbol is analyzed in both USD and Gold denominations across multiple timeframes.

## Data Source

- **yFinance**: Historical price data (OHLCV) for all symbols
- **Gold Prices**: GC=F futures prices used for gold-denominated analysis

## Timeframes

Analysis is performed on calendar-day resampled periods:
- **1W**: 7 calendar days
- **2W**: 14 calendar days
- **1M**: 30 calendar days
- **2M**: 60 calendar days
- **6M**: 180 calendar days

## Technical Indicators

### 1. **RSI (Relative Strength Index)**
- **Period**: 14
- **Purpose**: Measures momentum and identifies overbought/oversold conditions
- **Range**: 0-100
- **Scoring**: 
  - +2 points if RSI < 30 (oversold - strong buy signal)
  - +1 point if RSI 30-40 (slightly oversold - mild bullish signal)
  - -1 point if RSI > 70 (overbought - sell signal)

### 2. **StochRSI (Stochastic RSI)**
- **Period**: 14, with K=3 and D=3 smoothing
- **Purpose**: More sensitive momentum indicator than RSI
- **Components**: 
  - Fast (%K): StochRSI smoothed by 3 periods
  - Slow (%D): %K smoothed by 3 periods
- **Scoring**:
  - +1 point if Fast < 20 (oversold)
  - -1 point if Fast > 80 (overbought)

### 3. **ATR (Average True Range)**
- **Period**: 14
- **Purpose**: Measures volatility/risk
- **Calculation**: Average of True Range (max of: High-Low, |High-PrevClose|, |Low-PrevClose|)
- **Scoring** (based on ATR as % of price):
  - -2 points if ATR > 40% (extremely high volatility - significant risk)
  - -1 point if ATR > 30% (very high volatility - moderate risk)
  - **Note**: Thresholds adjusted to account for crypto's naturally higher volatility (15-30% is normal for crypto)

### 4. **EMA50 (50-Period Exponential Moving Average)**
- **Purpose**: Trend-following indicator
- **Scoring**:
  - +1 point if current price > EMA50 (uptrend)

### 5. **GMMA (Guppy Multiple Moving Average)**
- **Purpose**: Identifies trend strength and compression/expansion phases
- **Short EMAs**: 3, 5, 8, 10, 12, 15 periods
- **Long EMAs**: 30, 35, 40, 45, 50, 60 periods
- **Scoring**:
  - +2 points if GMMA bullish (all short EMAs above all long EMAs)
  - +1 point if early expansion (short EMAs > long EMAs with low spread)
  - +1 point if compressed (short EMA spread < 1.5% of price)

### 6. **MACD (Moving Average Convergence Divergence)**
- **Purpose**: Identifies trend changes and momentum
- **Components**: 
  - MACD Line: EMA(12) - EMA(26)
  - Signal Line: EMA(9) of MACD Line
  - Histogram: MACD Line - Signal Line
- **Scoring**:
  - +1 point if MACD bullish AND histogram positive (both conditions)

### 7. **Volume Analysis**
- **Purpose**: Confirms price movements with volume
- **Calculation**: Current volume vs 20-period average
- **Scoring**:
  - +1 point if volume > 120% of 20-period average (volume confirmation)

### 8. **Momentum (Rate of Change)**
- **Period**: 10 periods
- **Purpose**: Measures price change velocity
- **Calculation**: ((Current Price / Price 10 periods ago) - 1) × 100
- **Scoring**:
  - +1 point if momentum > 5% (strong positive momentum)
  - +1 point if momentum 2-5% (moderate positive momentum)
  - -1 point if momentum < -5% (strong negative momentum)

### 9. **4-Week Low**
- **Purpose**: Identifies if price is near recent lows (potential support)
- **Scoring**:
  - +1 point if current price ≤ 4-week low (at support level)

## Scoring System

**Starting Score**: 0

**Maximum Possible Score**: ~8-10 points (depending on indicator combinations)

### Score Interpretation

- **≥ 6**: Great Buy (Dark Green) - Very strong bullish signals
- **4-5**: Strong Buy (Medium Green) - Strong bullish signals
- **2-3**: OK Buy (Light Green) - Moderate bullish signals
- **0-1**: Neutral (Yellow) - Weak/neutral signals
- **< 0**: Filtered (not shown) - Bearish signals

### Calculation Method

Each symbol is analyzed using **two calculation libraries**:
1. **ta_library**: Standard technical analysis library
2. **tradingview_library**: TradingView-style calculations (matches TradingView formulas)

The **maximum score** from both methods is displayed (ensures best signal is shown if methods disagree).

## Denomination Analysis

Each symbol is analyzed in two ways:
- **USD**: Standard price analysis in US dollars
- **Gold**: Price denominated in gold ounces (price / gold_price)

This allows comparison of asset performance relative to both fiat currency and gold, providing insight into real purchasing power preservation.

## Relative Upside/Downside Potential

For each symbol, the system calculates relative potential metrics:

### 1. **Upside Potential (%)**
- Distance from current price to 52-week high
- Indicates maximum potential gain if price returns to recent high
- Example: 32.4% means price could rise 32.4% to reach 52-week high

### 2. **Downside Potential (%)**
- Distance from current price to 52-week low
- Indicates maximum potential loss if price falls to recent low
- Example: 25.16% means price could fall 25.16% to reach 52-week low

### 3. **Price Position in 52-Week Range**
- Percentage position: 0% = at 52-week low, 100% = at 52-week high
- Helps identify if asset is near support (low) or resistance (high)
- Example: 38.3% means price is in lower third of 52-week range

### 4. **Market Cap Comparison (Stocks Only)**
- Compares market cap to category peers (Tech, Crypto, Metals)
- Ratio: 1.0 = average, >1 = larger than peers, <1 = smaller than peers
- Helps identify relative valuation within niche
- Example: 0.33x means 33% of average peer market cap (smaller, potential for growth)

These metrics are displayed in the visualization for each timeframe, showing upside (↑) and downside (↓) percentages alongside the technical score.

## Output

Results are saved to `all_results.json` with the following structure:
```
{
  "SYMBOL": {
    "TIMEFRAME": {
      "yfinance": {
        "usd": {
          "ta_library": { ... indicators and score ... },
          "tradingview_library": { ... indicators and score ... }
        },
        "gold": {
          "ta_library": { ... indicators and score ... },
          "tradingview_library": { ... indicators and score ... }
        }
      }
    }
  }
}
```

## Visualization

Run `./run_visualization.sh` to generate an HTML table showing scores for all symbols, timeframes, and denominations. The visualization uses color coding to quickly identify buy/sell opportunities.
