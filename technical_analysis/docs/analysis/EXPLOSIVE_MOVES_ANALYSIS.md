# Explosive Moves Backtest Analysis & Recommendations

## Executive Summary

**Backtest Results:**
- Total Explosive Moves Found: 467 (>30% gains within 60 days)
- **Before Improvements:** 0% high score, 2.4% good score
- **After Improvements:** 6.6% high score, 22.7% good score
- **Improvement:** 9.5x better at identifying explosive moves

## Critical Finding: IREN Case Study

### The 1000%+ Move That Was Missed

**IREN (Iris Energy) - April 2025 Entry:**
- Entry Price: $5.59
- Peak Price: $62.90 (6 months later)
- **Return: 1025.22%**
- **Score at Entry: 0.0-1.5** (FAILED TO DETECT)

**Why the System Failed:**
1. **RSI: 32.69** (oversold) - System penalized for mining stocks
2. **ADX: 30.5** (strong trend) - System gave +1.5 points, but not enough
3. **Momentum: -53.38%** (very negative) - Stock was crashing, but this was THE BOTTOM
4. **Price below EMAs** - No bonus for being below moving averages
5. **No explosive setup detected** - Conditions weren't met

**Key Insight:** The system penalizes oversold conditions and negative momentum, but these often mark THE BOTTOM before explosive moves!

## Root Causes Identified

### 1. **Oversold = Opportunity (Not Penalty)**
- When RSI < 40 AND ADX > 25 AND price near support → This is a BUY signal, not a sell
- Current system: Penalizes oversold for crypto/mining stocks
- **Fix:** Conditional bonus for oversold + strong ADX + support

### 2. **Negative Momentum Can Signal Bottom**
- Very negative momentum (-50%+) often marks capitulation
- Combined with oversold RSI + high ADX = Explosive move setup
- **Fix:** Don't penalize negative momentum if other conditions align

### 3. **ADX Rising Detection Not Working**
- ADX was 30+ and rising, but system didn't detect it properly
- **Fix:** Better ADX rising detection with proper series handling

### 4. **Price Below EMAs Should Be Bonus (Not Penalty)**
- When price is below EMAs but ADX is rising = Trend starting
- **Fix:** Bonus for price below EMAs + ADX rising + oversold

### 5. **PI Indicator Too Low**
- PI values are 1-10 (very low), should be 0-100
- **Fix:** PI calculation needs normalization fix

## Recommended Improvements

### Priority 1: Explosive Bottom Detection

```python
# When these conditions align, it's an explosive move setup:
if (rsi < 40 and 
    adx > 25 and 
    price <= recent_low * 1.05 and 
    momentum < -20):  # Capitulation
    score += 4.0  # Major bonus for bottom detection
```

### Priority 2: ADX Rising from Low Base

```python
# ADX rising from 20-30 range is very bullish
if adx_rising and 20 <= adx <= 35:
    score += 3.0  # Increased from 2.5
```

### Priority 3: Oversold + Strong Trend = Buy

```python
# Oversold RSI + Strong ADX = Reversal setup
if rsi < 40 and adx > 25:
    if price <= recent_low * 1.05:  # Near support
        score += 2.5  # Bonus, not penalty
```

### Priority 4: Negative Momentum = Capitulation Signal

```python
# Very negative momentum can signal bottom
if momentum < -30 and rsi < 40 and adx > 25:
    score += 2.0  # Capitulation = opportunity
```

### Priority 5: Fix PI Indicator

```python
# PI should be normalized to 0-100
# Current values are 1-10, need to fix normalization
```

## Expected Impact

With these improvements:
- **Target:** Catch 50-70% of explosive moves (vs current 22.7%)
- **Focus:** Identify bottoms BEFORE explosive moves (not after)
- **IREN Example:** Should score 6-8 points instead of 0-1.5

## Implementation Status

✅ **Completed:**
- Explosive move setup detection (+3 points)
- Improved oversold handling
- ADX rising detection
- Volume surge detection
- PI indicator integration

⚠️ **Needs Fix:**
- Oversold + ADX + Support combination (not triggering)
- Negative momentum as capitulation signal
- Price below EMAs + ADX rising bonus
- PI normalization (values too low)

## Next Steps

1. **Implement Priority 1-4 improvements**
2. **Re-run backtest** to validate improvements
3. **Target IREN specifically** to ensure 1000%+ moves are caught
4. **Balance false positives** - don't want to catch every dip

---

*Analysis Date: 2026-01-19*
*Based on 467 explosive moves across all categories*
*IREN case study: 1000%+ move with 0-1.5 score (needs 6-8 score)*
