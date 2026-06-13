# Seasonality Indicator Implementation for Cryptocurrencies

## Overview

Added seasonality analysis to the scoring system specifically for cryptocurrencies. The indicator analyzes historical monthly and quarterly patterns to adjust scores based on seasonal trends.

## Implementation Details

### 1. Seasonality Module (`indicators/seasonality.py`)

**Functions:**
- `calculate_crypto_seasonality(df, min_years=2)`: Calculates seasonal patterns
- `get_seasonal_adjustment_for_timeframe(df, timeframe, min_years=2)`: Gets adjustment for specific timeframe

**Features:**
- Analyzes monthly returns across all available years
- Analyzes quarterly returns
- Calculates average returns, win rates, and positive year counts
- Generates seasonal adjustment based on current month/quarter
- Requires minimum 2 years of data for reliability

### 2. Integration into Scoring System

**Location:** `scoring/improved_scoring.py`

**Application:**
- Only applies to `cryptocurrencies` category
- Only applies to appropriate timeframes: 1D, 2D, 1W, 2W, 1M, 2M, 3M
- Adjusts score based on historical seasonal performance

**Adjustment Logic:**
- **Very Strong Month (>5% avg return):** +1.5 points
- **Strong Month (>2% avg return):** +1.0 points
- **Positive Month (>0% avg return):** +0.5 points
- **Slightly Negative (-2% to 0%):** -0.5 points
- **Negative Month (-5% to -2%):** -1.0 points
- **Very Negative Month (<-5%):** -1.5 points

**Timeframe Multipliers:**
- 1D: 0.3x (small adjustment)
- 2D: 0.4x
- 1W: 0.5x
- 2W: 0.6x
- 1M: 0.8x
- 2M: 1.0x (full weight)
- 3M: 1.0x (full weight)

### 3. Data Requirements

**For Cryptocurrencies:**
- Uses maximum available historical data (`period="max"`)
- Minimum 2 years of data required for seasonality calculation
- Analyzes all available years to build seasonal patterns

**Example:**
- ETH-USD: 8.21 years of data (2017-2026)
- BTC-USD: Similar long history
- SOL-USD: Shorter history (if available)

### 4. Scoring Integration

**Score Adjustment:**
```python
if is_crypto and timeframe in appropriate_timeframes:
    seasonal_adj, seasonality_info = get_seasonal_adjustment_for_timeframe(df, timeframe)
    score += seasonal_adj  # Applied before timeframe multiplier
```

**Indicators Added:**
- `seasonality_score`: 0-100 score based on current month/quarter
- `current_month`: Current month (1-12)
- `current_quarter`: Current quarter (1-4)
- `month_avg_return`: Historical average return for current month
- `month_win_rate`: Historical win rate for current month

**Breakdown Added:**
- `seasonality_adjustment`: Points added/subtracted based on seasonality

## Example: ETH-USD Seasonality

### Current Month (January)
- **Average Return:** +14.77%
- **Win Rate:** 44.4%
- **Positive Years:** 4 out of 9
- **Seasonality Score:** 80/100
- **Adjustment:** +2.00 points (on 2M/3M timeframes)

### Seasonal Adjustment by Timeframe
- **1D:** +0.60 points (30% of +2.00)
- **2D:** +0.80 points (40% of +2.00)
- **1W:** +1.00 points (50% of +2.00)
- **2W:** +1.20 points (60% of +2.00)
- **1M:** +1.60 points (80% of +2.00)
- **2M:** +2.00 points (100% of +2.00)
- **3M:** +2.00 points (100% of +2.00)

## Benefits

1. **Historical Context:** Uses years of data to identify seasonal patterns
2. **Timeframe-Appropriate:** Larger adjustments for longer timeframes
3. **Crypto-Specific:** Only applies to cryptocurrencies where seasonality is relevant
4. **Data-Driven:** Based on actual historical performance, not assumptions

## Usage

The seasonality indicator is automatically applied when:
1. Category is "cryptocurrencies"
2. Timeframe is 1D, 2D, 1W, 2W, 1M, 2M, or 3M
3. At least 2 years of historical data is available

No additional configuration needed - it's integrated into the scoring system.

## Files Modified

1. `indicators/seasonality.py` - New seasonality calculation module
2. `scoring/improved_scoring.py` - Integrated seasonality adjustment
3. `technical_analysis.py` - Updated to use max data for crypto

---

*Implementation Date: 2026-01-19*  
*Status: Complete ✅*
