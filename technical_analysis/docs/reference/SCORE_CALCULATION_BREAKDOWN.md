# Score Calculation Breakdown by Timeframe

## Overview

This document provides a comprehensive breakdown of how scores are calculated for each timeframe, including all indicators, their meanings, weights, and category-specific adjustments for **all asset classes**.

## Score Calculation Flow

1. **Base Indicators** → Calculate raw indicator values
2. **Category-Specific Adjustments** → Apply category-specific parameters
3. **Explosive Bottom Detection** → Identify potential explosive moves
4. **Trend Continuation** → Detect continuation opportunities
5. **Pattern Recognition** → Bottoming structures and Elliott Wave
6. **Seasonality (Crypto Only)** → Monthly/quarterly adjustments
7. **Market Context** → SPX/Gold, VIX, ISM adjustments
8. **Timeframe Multiplier** → Apply timeframe-specific strictness
9. **Final Cap** → Maximum score of 20

---

## Asset Class Categories

### Mining Stocks (Two Types)
- **Crypto Mining (miner_hpc):** Bitcoin/crypto mining companies (IREN, HUT, BITF, etc.)
- **Metal Mining (silver_miners_esg):** Precious metal mining companies (AG, PAAS, HL, etc.)
- **Note:** Both types share similar volatility characteristics and are grouped together in this documentation

### Other Categories
- **Cryptocurrencies:** BTC-USD, ETH-USD, SOL-USD
- **Tech Stocks:** General technology companies
- **FAANG/Hot Stocks:** Large-cap tech and high-growth stocks
- **Precious Metals:** Gold, Silver, Platinum, Palladium futures
- **Index ETFs:** SPY, IWM, VTWO
- **Quantum:** Quantum computing companies
- **Battery Storage:** Battery technology companies
- **Clean Energy Materials:** Materials for clean energy
- **Renewable Energy:** Solar, wind, renewable energy companies
- **Next Gen Automotive:** Electric vehicle and automotive innovation companies

---

## Indicators Used

### 1. RSI (Relative Strength Index)
**Meaning:** Measures momentum, identifies overbought (>70) and oversold (<30) conditions. Values above 70 suggest overbought conditions (potential sell), values below 30 suggest oversold conditions (potential buy).

**Weight by Category:**

#### Cryptocurrencies
- **Oversold threshold:** 35 (more sensitive)
- **Overbought threshold:** 70
- **Oversold bonus:** +2.0 points
- **Overbought penalty:** -1.5 points
- **Why:** Cryptocurrencies are highly volatile and can stay oversold longer, requiring a lower threshold to catch buying opportunities. The 35 threshold accounts for crypto's tendency to overshoot.

#### Tech Stocks
- **Oversold threshold:** 35
- **Overbought threshold:** 70
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Tech stocks can experience extended oversold periods during corrections, but recover strongly. The 35 threshold helps catch these opportunities.

#### FAANG/Hot Stocks
- **Oversold threshold:** 35
- **Overbought threshold:** 70
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Similar to tech stocks, these high-growth stocks can have volatile corrections followed by strong recoveries.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +2.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Crypto mining stocks are extremely volatile and can experience severe oversold conditions. The 40 threshold with higher bonus (2.5) helps catch explosive reversals.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +2.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Metal mining stocks share similar volatility with crypto mining. They can experience deep oversold conditions during commodity downturns, followed by explosive recoveries.

#### Precious Metals
- **Oversold threshold:** 30 (standard)
- **Overbought threshold:** 70
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Precious metals are less volatile than mining stocks. Standard 30/70 thresholds work well for these assets.

#### Index ETFs
- **Oversold threshold:** 30 (standard)
- **Overbought threshold:** 70
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Index ETFs are diversified and less volatile. Standard thresholds provide good signals.

#### Quantum
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Quantum computing stocks are emerging tech with high volatility, requiring higher thresholds.

#### Battery Storage
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Battery technology stocks are volatile growth stocks, similar to quantum.

#### Clean Energy Materials
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Materials for clean energy are cyclical and volatile, requiring adjusted thresholds.

#### Renewable Energy
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** Renewable energy stocks are policy-sensitive and volatile, requiring higher thresholds.

#### Next Gen Automotive
- **Oversold threshold:** 40
- **Overbought threshold:** 75
- **Oversold bonus:** +1.5 points
- **Overbought penalty:** -1.0 points
- **Why:** EV and automotive innovation stocks are highly volatile growth stocks.

**Timeframe Impact:** None (same across all timeframes)

---

### 2. ADX (Average Directional Index)
**Meaning:** Measures trend strength (0-100), higher values indicate stronger trends. ADX above 25 indicates a strong trend, above 40 indicates a very strong trend. ADX does not indicate direction, only strength.

**Weight by Category:**

#### Cryptocurrencies
- **Thresholds:** 20 (moderate), 30 (strong), 40 (very strong)
- **Moderate trend (20-30):** +1.0 points
- **Strong trend (30-40):** +2.0 points
- **Very strong trend (>40):** +3.0 points
- **ADX Multiplier:** 0.5x (reduced weight)
- **Why:** Crypto trends are more volatile and can form quickly. Lower thresholds (20/30/40) catch trends earlier. Reduced multiplier (0.5x) prevents over-weighting ADX in mean-reversion scenarios.

#### Tech Stocks
- **Thresholds:** 25 (moderate), 35 (strong), 45 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (35-45):** +2.0 points
- **Very strong trend (>45):** +3.0 points
- **ADX Multiplier:** 0.5x (reduced weight)
- **Why:** Tech stocks can have strong trends but also mean-revert. Standard thresholds with reduced multiplier balance trend-following and mean-reversion.

#### FAANG/Hot Stocks
- **Thresholds:** 25 (moderate), 35 (strong), 45 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (35-45):** +2.0 points
- **Very strong trend (>45):** +3.0 points
- **ADX Multiplier:** 0.5x (reduced weight)
- **Why:** Similar to tech stocks, these large-cap growth stocks need balanced approach.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **Thresholds:** 18 (moderate), 28 (strong), 38 (very strong)
- **Moderate trend (18-28):** +1.5 points
- **Strong trend (28-38):** +2.5 points
- **Very strong trend (>38):** +3.5 points
- **ADX Multiplier:** 1.0x (full weight)
- **Why:** Crypto mining stocks are extremely volatile. Lower thresholds (18/28/38) catch explosive moves earlier. Higher bonuses (1.5/2.5/3.5) reward strong trends. Full multiplier (1.0x) because these stocks trend strongly when they move.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **Thresholds:** 18 (moderate), 28 (strong), 38 (very strong)
- **Moderate trend (18-28):** +1.5 points
- **Strong trend (28-38):** +2.5 points
- **Very strong trend (>38):** +3.5 points
- **ADX Multiplier:** 1.0x (full weight)
- **Why:** Metal mining stocks share crypto mining's volatility. They can have explosive moves during commodity cycles. Same thresholds and bonuses as crypto mining.

#### Precious Metals
- **Thresholds:** 25 (moderate), 35 (strong), 40 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (35-40):** +2.0 points
- **Very strong trend (>40):** +3.0 points
- **ADX Multiplier:** 1.0x (full weight)
- **Why:** Precious metals trend strongly during macro cycles. Standard thresholds work well.

#### Index ETFs
- **Thresholds:** 25 (moderate), 35 (strong), 40 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (35-40):** +2.0 points
- **Very strong trend (>40):** +3.0 points
- **ADX Multiplier:** 1.0x (full weight)
- **Why:** Index ETFs trend well during bull/bear markets. Standard thresholds are appropriate.

#### Quantum
- **Thresholds:** 25 (moderate), 35 (strong), 35 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (>35):** +2.0 points
- **ADX Multiplier:** 0.75x (reduced weight)
- **Why:** Quantum stocks are emerging tech with high volatility. Slightly reduced multiplier balances trend and volatility.

#### Battery Storage
- **Thresholds:** 25 (moderate), 35 (strong), 35 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (>35):** +2.0 points
- **ADX Multiplier:** 0.75x (reduced weight)
- **Why:** Battery stocks are volatile growth stocks. Similar approach to quantum.

#### Clean Energy Materials
- **Thresholds:** 25 (moderate), 35 (strong), 35 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (>35):** +2.0 points
- **ADX Multiplier:** 0.75x (reduced weight)
- **Why:** Materials stocks are cyclical and volatile. Reduced multiplier accounts for this.

#### Renewable Energy
- **Thresholds:** 25 (moderate), 35 (strong), 35 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (>35):** +2.0 points
- **ADX Multiplier:** 0.75x (reduced weight)
- **Why:** Renewable energy stocks are policy-sensitive and volatile.

#### Next Gen Automotive
- **Thresholds:** 25 (moderate), 35 (strong), 35 (very strong)
- **Moderate trend (25-35):** +1.0 points
- **Strong trend (>35):** +2.0 points
- **ADX Multiplier:** 0.75x (reduced weight)
- **Why:** EV stocks are highly volatile growth stocks.

**Timeframe Impact:** None (same across all timeframes)

---

### 3. Momentum (Price Change)
**Meaning:** Rate of price change over 14 periods, identifies acceleration/deceleration. Positive momentum indicates upward price acceleration, negative indicates downward acceleration.

**Weight by Category:**
- **All Categories:** 
  - Very negative momentum (<-20%): +2.0 points (capitulation signal)
  - Negative momentum (-10% to -20%): +1.0 points
  - Strong positive momentum (>15%): +1.5 points
  - Moderate positive momentum (8-15%): +0.5 points
  - **Why:** Extreme negative momentum can signal capitulation bottoms. Strong positive momentum indicates trend acceleration. This applies universally across all asset classes.

**Timeframe Impact:** None (same across all timeframes)

---

### 4. Volume Analysis
**Meaning:** Measures buying/selling pressure through volume patterns. High volume confirms price moves, low volume suggests weak moves.

**Weight by Category:**

#### Cryptocurrencies
- **Volume spike (>2x average):** +1.5 points
- **Building volume (increasing trend):** +1.0 points
- **Volume Multiplier:** 2.0x (double weight)
- **Why:** Crypto volume is crucial for confirming moves. Volume spikes often precede major moves. Double multiplier emphasizes volume importance.

#### Tech Stocks
- **Volume spike (>1.5x average):** +1.0 points
- **Building volume:** +0.5 points
- **Volume Multiplier:** 1.5x
- **Why:** Tech stocks need volume confirmation, but less critical than crypto.

#### FAANG/Hot Stocks
- **Volume spike (>1.5x average):** +1.0 points
- **Building volume:** +0.5 points
- **Volume Multiplier:** 1.5x
- **Why:** Similar to tech stocks, volume confirms moves in large-cap growth stocks.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **Volume spike (>2.5x average):** +2.0 points
- **Building volume:** +1.5 points
- **Volume Multiplier:** 1.5x
- **Why:** Crypto mining stocks need very strong volume confirmation due to extreme volatility. Higher threshold (2.5x) ensures genuine interest.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **Volume spike (>2.5x average):** +2.0 points
- **Building volume:** +1.5 points
- **Volume Multiplier:** 1.5x
- **Why:** Metal mining stocks also need strong volume confirmation. Same approach as crypto mining.

#### Precious Metals
- **Volume spike (>1.5x average):** +1.0 points
- **Building volume:** +0.5 points
- **Volume Multiplier:** 1.0x (standard)
- **Why:** Precious metals have standard volume requirements.

#### Index ETFs
- **Volume spike (>1.5x average):** +1.0 points
- **Building volume:** +0.5 points
- **Volume Multiplier:** 1.0x (standard)
- **Why:** Index ETFs have standard volume patterns.

#### Quantum, Battery Storage, Clean Energy Materials, Renewable Energy, Next Gen Automotive
- **Volume spike (>1.5x average):** +1.0 points
- **Building volume:** +0.5 points
- **Volume Multiplier:** 1.5x
- **Why:** These volatile growth sectors need volume confirmation similar to tech stocks.

**Timeframe Impact:** None (same across all timeframes)

---

### 5. Moving Averages (EMA50, EMA200)
**Meaning:** Trend direction indicators, price above/below indicates bullish/bearish trend. EMA50 is short-term trend, EMA200 is long-term trend.

**Weight by Category:**
- **All Categories:**
  - Price > EMA50 and EMA200: +1.0 points (uptrend)
  - Price < EMA50 but > EMA200: +0.5 points (mixed)
  - Price < EMA50 and EMA200: -0.5 points (downtrend)
  - Extreme oversold (<70% of EMA50): +3.0 points
  - Very oversold (<80% of EMA50): +2.0 points
  - **Why:** Extreme oversold conditions often precede reversals. This applies universally. Moving averages provide trend context.

**Timeframe Impact:** None (same across all timeframes)

---

### 6. ATR (Average True Range)
**Meaning:** Measures volatility, high ATR indicates high volatility. Low ATR suggests consolidation, high ATR suggests active trading.

**Weight by Category:**

#### Cryptocurrencies
- **Low volatility (<5% of price):** +1.0 points
- **High volatility (>15% of price):** -0.5 points
- **Why:** Low volatility in crypto can signal compression before explosive moves. High volatility suggests uncertainty.

#### Tech Stocks
- **Low volatility (<3% of price):** +0.5 points
- **High volatility (>10% of price):** -0.5 points
- **Why:** Tech stocks have lower base volatility than crypto. Compression signals are less dramatic.

#### FAANG/Hot Stocks
- **Low volatility (<3% of price):** +0.5 points
- **High volatility (>10% of price):** -0.5 points
- **Why:** Similar to tech stocks, these large-caps have moderate volatility.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **Low volatility (<8% of price):** +1.5 points
- **High volatility (>20% of price):** -1.0 points
- **Why:** Crypto mining stocks are extremely volatile. Low volatility (<8%) is rare and signals potential explosive moves. High volatility (>20%) indicates high risk.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **Low volatility (<8% of price):** +1.5 points
- **High volatility (>20% of price):** -1.0 points
- **Why:** Metal mining stocks share crypto mining's volatility characteristics. Same thresholds apply.

#### Precious Metals
- **Low volatility (<3% of price):** +0.5 points
- **High volatility (>10% of price):** -0.5 points
- **Why:** Precious metals have moderate volatility. Standard thresholds work.

#### Index ETFs
- **Low volatility (<2% of price):** +0.5 points
- **High volatility (>8% of price):** -0.5 points
- **Why:** Index ETFs are less volatile due to diversification. Lower thresholds.

#### Quantum, Battery Storage, Clean Energy Materials, Renewable Energy, Next Gen Automotive
- **Low volatility (<5% of price):** +0.5 points
- **High volatility (>15% of price):** -0.5 points
- **Why:** These growth sectors have higher volatility. Similar to crypto but less extreme.

**Timeframe Impact:** None (same across all timeframes)

---

### 7. Price Intensity (PI Indicator)
**Meaning:** Multi-factor indicator combining momentum, volume strength, volatility compression, and price extension (0-100). Higher values indicate stronger buying pressure.

**Weight by Category:**
- **All Categories:**
  - PI > 70: +2.0 points
  - PI > 60: +1.5 points
  - PI > 50: +1.0 points
  - PI < 30: +0.5 points (oversold)
  - **Why:** High PI indicates strong buying pressure across all asset classes. Universal indicator.

**Timeframe Impact:** None (same across all timeframes)

---

### 8. Explosive Bottom Detection
**Meaning:** Identifies conditions that historically precede explosive moves (>30% in 60 days). Combines multiple signals to catch major reversals.

**Weight by Category:**

#### Cryptocurrencies
- **All conditions met:** +5.0 points (base 4.0 × 1.5 multiplier)
- **Most conditions met:** +3.0 points
- **Explosive Bottom Bonus Multiplier:** 1.5x
- **Why:** Crypto has more explosive moves. Higher bonus (1.5x) rewards catching these opportunities.

#### Tech Stocks
- **All conditions met:** +4.0 points
- **Most conditions met:** +2.5 points
- **Explosive Bottom Bonus Multiplier:** 1.0x
- **Why:** Tech stocks can have explosive moves but less frequent than crypto.

#### FAANG/Hot Stocks
- **All conditions met:** +4.0 points
- **Most conditions met:** +2.5 points
- **Explosive Bottom Bonus Multiplier:** 1.0x
- **Why:** Similar to tech stocks, these large-caps can have strong reversals.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **All conditions met:** +6.0 points (base 4.0 × 2.0 multiplier)
- **Most conditions met:** +4.0 points
- **Explosive Bottom Bonus Multiplier:** 2.0x
- **Why:** Crypto mining stocks have the most explosive moves. Highest bonus (2.0x) rewards catching these rare but highly profitable opportunities.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **All conditions met:** +6.0 points (base 4.0 × 2.0 multiplier)
- **Most conditions met:** +4.0 points
- **Explosive Bottom Bonus Multiplier:** 2.0x
- **Why:** Metal mining stocks can have explosive moves during commodity cycles. Same high bonus as crypto mining.

#### Precious Metals
- **All conditions met:** +4.0 points
- **Most conditions met:** +2.5 points
- **Explosive Bottom Bonus Multiplier:** 1.0x
- **Why:** Precious metals can have strong moves but less explosive than mining stocks.

#### Index ETFs
- **All conditions met:** +4.0 points
- **Most conditions met:** +2.5 points
- **Explosive Bottom Bonus Multiplier:** 1.0x
- **Why:** Index ETFs are diversified and less explosive, but can have strong reversals.

#### Quantum, Battery Storage, Clean Energy Materials, Renewable Energy, Next Gen Automotive
- **All conditions met:** +4.5 points (base 4.0 × 1.5 multiplier)
- **Most conditions met:** +3.0 points
- **Explosive Bottom Bonus Multiplier:** 1.5x
- **Why:** These growth sectors can have explosive moves. Higher bonus (1.5x) similar to crypto.

**Conditions:**
- Oversold RSI (category-specific threshold)
- Strong ADX (trend starting, category-specific threshold)
- Very negative momentum (capitulation, category-specific threshold)
- Near support level (within 5% of 4-week low)
- Volatility compressed (Bollinger Band squeeze)
- Volume building (increasing volume trend)

**Timeframe Impact:** None (same across all timeframes)

---

### 9. Trend Continuation
**Meaning:** Identifies strong trends that are likely to continue. Catches moves in established uptrends.

**Weight by Category:**

#### Cryptocurrencies
- **Very strong ADX (>40):** +2.5 points
- **Strong ADX (>20):** +2.0 points
- **Moderate ADX (>15):** +1.0 points
- **Continuation Bonus:** 2.0x
- **Why:** Crypto trends can be very strong and persistent. Lower thresholds (20/40) catch trends earlier.

#### Tech Stocks
- **Very strong ADX (>40):** +2.0 points
- **Strong ADX (>25):** +1.5 points
- **Moderate ADX (>20):** +0.5 points
- **Continuation Bonus:** 2.0x
- **Why:** Tech stocks can have strong trends. Standard thresholds work well.

#### FAANG/Hot Stocks
- **Very strong ADX (>40):** +2.0 points
- **Strong ADX (>25):** +1.5 points
- **Moderate ADX (>20):** +0.5 points
- **Continuation Bonus:** 2.0x
- **Why:** Similar to tech stocks, these large-caps trend well.

#### Mining Stocks (Crypto Mining - miner_hpc)
- **Very strong ADX (>35):** +3.0 points
- **Strong ADX (>25):** +2.5 points
- **Moderate ADX (>18):** +1.5 points
- **Continuation Bonus:** 2.5x
- **Why:** Crypto mining stocks have explosive trends. Lower thresholds (18/25/35) with higher bonuses (2.5x) catch these moves.

#### Mining Stocks (Metal Mining - silver_miners_esg)
- **Very strong ADX (>35):** +3.0 points
- **Strong ADX (>25):** +2.5 points
- **Moderate ADX (>18):** +1.5 points
- **Continuation Bonus:** 2.5x
- **Why:** Metal mining stocks share crypto mining's trend characteristics. Same thresholds and bonuses.

#### Precious Metals
- **Very strong ADX (>40):** +2.0 points
- **Strong ADX (>25):** +1.5 points
- **Moderate ADX (>20):** +0.5 points
- **Continuation Bonus:** 2.0x
- **Why:** Precious metals trend strongly during macro cycles. Standard approach.

#### Index ETFs
- **Very strong ADX (>40):** +2.0 points
- **Strong ADX (>25):** +1.5 points
- **Moderate ADX (>20):** +0.5 points
- **Continuation Bonus:** 2.0x
- **Why:** Index ETFs trend well during bull/bear markets. Standard thresholds.

#### Quantum, Battery Storage, Clean Energy Materials, Renewable Energy, Next Gen Automotive
- **Very strong ADX (>35):** +2.0 points
- **Strong ADX (>25):** +1.5 points
- **Moderate ADX (>20):** +0.5 points
- **Continuation Bonus:** 2.0x
- **Why:** These growth sectors can have strong trends. Slightly lower very strong threshold (35) accounts for volatility.

**Timeframe Impact:** None (same across all timeframes)

---

### 10. Bottoming Structures
**Meaning:** Chart patterns indicating potential price reversals (Double Bottom, Inverse Head & Shoulders, Ascending Triangle, Falling Wedge). These patterns historically precede reversals.

**Weight by Category:**
- **All Categories:**
  - Pattern detected: +1.5 to +3.0 points (based on pattern strength)
  - High confidence (>0.5): +1.0 additional points
  - **Why:** Pattern recognition adds confidence to signals across all asset classes. Universal indicator.

**Timeframe Impact:** Multiplied by timeframe multiplier

---

### 11. Elliott Wave Analysis
**Meaning:** Identifies wave positions and price targets based on Elliott Wave theory. Wave 2 and 4 are corrections in uptrends, representing buying opportunities.

**Weight by Category:**
- **All Categories:**
  - Wave 2 or 4 (correction): +1.5 points
  - **Why:** Corrections in uptrends are buying opportunities. Applies universally across all asset classes.

**Timeframe Impact:** Multiplied by timeframe multiplier

---

### 12. Seasonality (Cryptocurrencies Only)
**Meaning:** Historical monthly/quarterly return patterns. Analyzes which months/quarters historically perform better for cryptocurrencies.

**Weight by Timeframe:**
- **1D:** 0.3x multiplier (small adjustment)
- **2D:** 0.4x multiplier
- **1W:** 0.5x multiplier
- **2W:** 0.6x multiplier
- **1M:** 0.8x multiplier
- **2M:** 1.0x multiplier (full weight)
- **3M:** 1.0x multiplier (full weight)

**Adjustment Range:**
- Very strong month (>5% avg return): +1.5 points (base)
- Strong month (>2% avg return): +1.0 points
- Positive month (>0% avg return): +0.5 points
- Negative month: -0.5 to -1.5 points

**Why:** Longer timeframes align better with monthly/quarterly patterns. Only applies to cryptocurrencies as they show strong seasonal patterns.

**Categories:** Cryptocurrencies only

---

### 13. Market Context Adjustments

#### 13a. SPX/Gold Ratio
**Meaning:** Macro indicator of market health, falling ratio indicates bear market. When stocks underperform gold, it suggests risk-off sentiment.

**Weight:** Same across all categories and timeframes
- Crashing (<-5% in 20 days): -2.0 points
- Declining (-2% to -5%): -1.0 points
- Near recent low: -1.0 additional points
- **Why:** Bear markets reduce all asset scores. Universal adjustment.

**Timeframe Impact:** None (same across all timeframes)

#### 13b. VIX (Volatility Index)
**Meaning:** Measures expected market volatility, high VIX = high risk. VIX above 30 indicates fear, below 20 indicates complacency.

**Weight:** Same across all categories and timeframes
- Low VIX (<20): 0.0 points (no adjustment)
- Moderate VIX (20-29): -0.5 points
- High VIX (>29): -1.5 points
- Rising VIX: -0.5 additional points
- **Why:** High volatility increases risk across all assets. Universal adjustment.

**Timeframe Impact:** None (same across all timeframes)

#### 13c. ISM Business Cycle
**Meaning:** Economic expansion/contraction indicator (PMI scale). PMI above 50 indicates expansion, below 50 indicates contraction.

**Weight by Timeframe:**
- **4H:** 0.2x multiplier (very small)
- **1D:** 0.3x multiplier
- **2D:** 0.4x multiplier
- **1W:** 0.6x multiplier
- **2W:** 0.8x multiplier
- **1M:** 1.0x multiplier (full weight)
- **2M:** 1.2x multiplier (above full)
- **3M:** 1.2x multiplier (above full)

**Adjustment Range:**
- Strong expansion (PMI >60): +1.0 points (base)
- Expansion (PMI 50-60): +0.5 points
- Contraction (PMI 40-50): -0.5 points
- Strong contraction (PMI <40): -1.0 points
- Improving trend: +0.3 points
- Deteriorating trend: -0.3 points

**Why:** Business cycles are longer-term, more relevant for longer timeframes. Applies to all categories.

**Timeframe Impact:** Multiplied by timeframe-specific multiplier

---

### 14. Timeframe Multiplier
**Meaning:** Adjusts scores based on timeframe length (shorter = stricter). Shorter timeframes have more noise, longer timeframes have more reliable signals.

**Multipliers:**
- **4H:** 0.6x (reduce by 40%) - Very strict
- **1D:** 0.65x (reduce by 35%) - Strict
- **2D:** 0.7x (reduce by 30%) - Stricter
- **1W:** 0.85x (reduce by 15%) - Slightly stricter
- **2W:** 1.0x (no change) - Standard
- **1M:** 1.1x (increase by 10%) - Slightly lenient
- **2M:** 1.15x (increase by 15%) - More lenient
- **3M:** 1.2x (increase by 20%) - Most lenient

**Why:** Shorter timeframes have more noise, need stricter scoring. Longer timeframes have more reliable patterns.

**Applied to:** All base scores before market context adjustments

---

### 15. Final Score Cap
**Meaning:** Prevents over-optimistic scores. Very high scores may indicate overfitting or unrealistic expectations.

**Cap:** Maximum score of 20 points

**Why:** Prevents unrealistic expectations. Scores above 20 are capped to maintain realism.

---

## Category-Specific Summary

### Cryptocurrencies
- **Lower thresholds** for oversold/ADX (more volatile)
- **Higher bonuses** for explosive moves (more explosive)
- **Seasonality included** (monthly/quarterly patterns)
- **Stronger volume requirements** (2.0x multiplier)
- **Reduced ADX weight** (0.5x multiplier for mean-reversion)

### Tech Stocks & FAANG/Hot Stocks
- **Moderate thresholds** (balanced approach)
- **Standard bonuses** (moderate volatility)
- **No seasonality** (not applicable)
- **Moderate volume requirements** (1.5x multiplier)
- **Reduced ADX weight** (0.5x multiplier)

### Mining Stocks (Crypto Mining & Metal Mining)
- **Lowest thresholds** (most volatile)
- **Highest bonuses** (most explosive)
- **Strongest volume requirements** (1.5x multiplier, 2.5x threshold)
- **Full ADX weight** (1.0x multiplier)
- **Highest explosive bottom bonus** (2.0x multiplier)
- **Highest trend continuation bonus** (2.5x multiplier)
- **Why:** Both crypto mining and metal mining stocks share extreme volatility and explosive move characteristics

### Precious Metals
- **Standard thresholds** (less volatile)
- **Standard bonuses** (moderate moves)
- **Standard volume requirements** (1.0x multiplier)
- **Full ADX weight** (1.0x multiplier)

### Index ETFs
- **Standard thresholds** (diversified, less volatile)
- **Standard bonuses** (moderate moves)
- **Standard volume requirements** (1.0x multiplier)
- **Full ADX weight** (1.0x multiplier)

### Quantum, Battery Storage, Clean Energy Materials, Renewable Energy, Next Gen Automotive
- **Higher thresholds** (volatile growth stocks)
- **Moderate bonuses** (1.5x explosive bottom)
- **Moderate volume requirements** (1.5x multiplier)
- **Reduced ADX weight** (0.75x multiplier)
- **Why:** These are emerging/volatile growth sectors, need balanced approach

---

## Score Calculation Example

### Example: ETH-USD on 1M Timeframe (Crypto Category)

**Base Indicators:**
- RSI: 35 (oversold) → +2.0 points
- ADX: 32 (strong trend) → +2.0 points × 0.5 = +1.0 points
- Momentum: -18% (very negative) → +2.0 points
- Volume: Building → +1.0 points × 2.0 = +2.0 points
- Price < EMA50 (extreme oversold) → +3.0 points
- ATR: Low volatility → +1.0 points
- PI: 65 → +1.5 points
- **Subtotal: 12.5 points**

**Explosive Bottom Detection:**
- All conditions met → +5.0 points (4.0 × 1.5)
- **Subtotal: 17.5 points**

**Pattern Recognition:**
- Double Bottom detected → +2.0 points
- **Subtotal: 19.5 points**

**Seasonality (Crypto, 1M):**
- January (strong month, +14.77% avg) → +1.6 points (1.0 × 0.8 × 2.0)
- **Subtotal: 21.1 points**

**Market Context:**
- SPX/Gold: Crashing → -2.0 points
- VIX: Low → 0.0 points
- ISM: Expansion → +0.5 points (0.5 × 1.0)
- **Subtotal: 19.6 points**

**Timeframe Multiplier (1M):**
- 19.6 × 1.1 = 21.56 points

**Final Cap:**
- min(21.56, 20) = **20.0 points**

---

*Last Updated: 2026-01-19*  
*Version: 3.0 (Complete - All Asset Classes Documented)*
