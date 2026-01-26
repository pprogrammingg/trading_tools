# Intraday Timeframes Implementation (1D and 4H)

## Overview

Added daily (1D) and 4-hour (4H) timeframes to the technical analysis system with comprehensive backtesting to validate explosive move and trend continuation detection.

## Implementation Details

### 1. Timeframe Configuration

**Added to `TIMEFRAMES` dictionary:**
- `"4H": "4H"` - 4-hour intraday timeframe
- `"1D": "1D"` - Daily timeframe

**Timeframe Order:** 4H → 1D → 2D → 1W → 2W → 1M → 2M → 6M

### 2. Data Download and Resampling

**4H Timeframe:**
- Downloads 60 days of 1-hour intraday data
- Resamples to 4-hour bars using pandas `resample('4h')`
- Falls back to daily data if intraday data unavailable

**1D Timeframe:**
- Uses daily data directly
- If intraday data is provided, resamples to daily bars

**Updated Functions:**
- `download_data()` - Now supports `interval="1h"` for intraday data
- `resample_ohlcv()` - Handles 4H and 1D timeframes with appropriate logic

### 3. Scoring Adjustments

**Timeframe Multipliers (in `improved_scoring.py`):**
```python
timeframe_multipliers = {
    "4H": 0.6,   # Very strict (reduce scores by 40%) - intraday noise
    "1D": 0.65,  # Strict (reduce scores by 35%) - daily volatility
    "2D": 0.7,   # Stricter (reduce scores by 30%)
    "1W": 0.85,  # Slightly stricter (reduce by 15%)
    "2W": 1.0,   # Standard
    "1M": 1.1,   # Slightly more lenient (increase by 10%)
}
```

**Rationale:**
- **4H:** Most strict due to intraday noise and false signals
- **1D:** Strict due to daily volatility and shorter-term signals
- Longer timeframes get progressively more lenient

### 4. Visualization Updates

**Updated `visualize_scores.py`:**
- `sort_timeframes()` function now handles 4H and 1D
- 4H appears first (shortest timeframe)
- 1D appears before 2D
- All timeframes properly sorted in visualization tables

### 5. Comprehensive Backtesting

**Created `intraday_timeframe_backtest.py`:**
- Tests both 4H and 1D timeframes
- Detects explosive moves (30%+ within lookback period)
- Detects trend continuations (price above EMAs)
- Analyzes catch rates with and without VIX adjustments
- Categorizes by:
  - Timeframe (4H vs 1D)
  - Move type (explosive_bottom vs continuation)
  - VIX level (low, moderate, high)

**Backtest Features:**
- Historical VIX context for each entry point
- Market context (SPX/Gold ratio) integration
- Score comparison (with vs without VIX)
- Detailed breakdown of indicators and patterns

## Backtest Results Summary

### Initial Findings

**4H Timeframe:**
- Limited data availability (requires intraday data)
- Fewer explosive moves detected (due to shorter lookback)
- More sensitive to intraday noise

**1D Timeframe:**
- Good data availability
- High number of explosive moves detected
- Better signal quality than 4H

### Performance Metrics

**By Timeframe:**
- **4H:** Lower catch rate due to strict multipliers and noise
- **1D:** Higher catch rate, good balance of sensitivity and reliability

**By Move Type:**
- **Explosive Bottom:** Better detection on 1D timeframe
- **Trend Continuation:** Good detection on both timeframes

**By VIX Level:**
- **Low VIX:** Best performance (no adjustments)
- **Moderate VIX:** Slight reduction in catch rate
- **High VIX:** Significant reduction (risk management working)

## Usage

### Running Analysis

The new timeframes are automatically included when running:
```bash
python technical_analysis.py
```

### Running Backtest

```bash
python backtesting/intraday_timeframe_backtest.py
```

### Viewing Results

Results are saved to:
- `backtesting/intraday_timeframe_backtest_results.json`

Visualizations automatically include 4H and 1D timeframes in the HTML output.

## Technical Notes

### Data Limitations

**4H Timeframe:**
- Requires intraday data (1h interval)
- Limited to 60 days of history (yfinance limitation)
- May have gaps during non-trading hours
- Not all symbols have reliable intraday data

**1D Timeframe:**
- Uses standard daily data
- Full historical data available
- More reliable for most symbols

### Scoring Considerations

**4H Scoring:**
- Very strict multipliers (0.6) to reduce false signals
- Intraday noise can create false patterns
- Best for active traders with tight risk management

**1D Scoring:**
- Strict multipliers (0.65) for daily volatility
- Good balance for swing traders
- More reliable than 4H for most use cases

## Recommendations

1. **4H Timeframe:**
   - Use primarily for active trading
   - Requires careful risk management
   - Best for liquid, high-volume symbols
   - Consider combining with longer timeframes for confirmation

2. **1D Timeframe:**
   - Recommended for most traders
   - Good balance of sensitivity and reliability
   - Works well with existing 2D, 1W timeframes
   - Suitable for swing trading strategies

3. **Combined Analysis:**
   - Use multiple timeframes for confirmation
   - 4H for entry timing
   - 1D for trend confirmation
   - 1W+ for overall direction

## Files Modified

1. `technical_analysis.py`
   - Added 4H and 1D to TIMEFRAMES
   - Updated `resample_ohlcv()` function
   - Updated `process_category()` for 4H data download

2. `scoring/improved_scoring.py`
   - Added 4H and 1D multipliers

3. `visualize_scores.py`
   - Updated `sort_timeframes()` function

4. `backtesting/intraday_timeframe_backtest.py`
   - New comprehensive backtest script

## Future Enhancements

1. **Intraday Pattern Detection:**
   - Add intraday-specific patterns
   - Volume profile analysis
   - Time-of-day effects

2. **Optimization:**
   - Fine-tune multipliers based on backtest results
   - Category-specific adjustments for 4H/1D
   - VIX sensitivity calibration

3. **Additional Timeframes:**
   - 1H timeframe for very active traders
   - 30M for scalping strategies

---

*Implementation Date: 2026-01-19*  
*Status: Complete and Tested ✅*
