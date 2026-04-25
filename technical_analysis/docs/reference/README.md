# Technical Analysis System (supplemental)

**Commands and copy-paste instructions** live in **[../../README.md](../../README.md)** in the `technical_analysis` package root. Use that file as the single source of truth for *what to run*.

The sections below (features, backtesting, structure, etc.) are **reference and background** only, not a duplicate command list.

## 📊 Features

### Advanced Technical Indicators

**Trend-Following Indicators** (catch major moves RSI misses):
- **ADX (Average Directional Index)**: Measures trend strength
  - ADX > 30: +2 points (very strong trend)
  - ADX > 25: +1.5 points (strong trend)
  - ADX rising from low: +3 points (trend starting) ⭐ NEW
  - Would have caught gold's 1970s move that RSI missed

- **CCI (Commodity Channel Index)**: Better for commodities than RSI
  - CCI < -100: +1.5 points (oversold recovery)
  - CCI > 100: -1.5 points (overbought)
  - Designed for commodities, less false signals

- **OBV & Accumulation/Distribution**: Volume-based indicators
  - OBV trending up: +1 point (accumulation)
  - A/D trending up: +1 point (institutional buying)

**Explosive Bottom Detection** ⭐ NEW:
- Detects bottoms before explosive moves (>30% gains)
- Multi-factor confirmation:
  - Oversold RSI + Strong ADX + Capitulation momentum
  - Price near support
  - Volatility compression OR volume building
- **Category-specific bonuses** (1.0-2.0x multiplier)
- **Impact:** IREN 1000%+ moves now score 9.5-15.5 (was 0-1.5)

**Price Intensity (PI) Indicator** ⭐ NEW:
- Combines momentum, volume, volatility compression
- PI > 70: +2 points (high explosive potential)
- PI 50-70: +1 point
- Normalized to 0-100 scale

**Context-Aware RSI**:
- RSI weight reduced by 50% when ADX > 25 (strong trend)
- Category-specific thresholds (30-40 for different categories)
- Mean-reversion logic for crypto/tech, trend-following for commodities

## 📈 Scoring System

**Starting Score:** 0

**Score Interpretation:**
- **≥6**: Great Buy (Dark Green) - Very strong bullish signals
- **4-5**: Strong Buy (Medium Green) - Strong bullish signals
- **2-3**: OK Buy (Light Green) - Moderate bullish signals
- **0-1**: Neutral (Yellow) - Weak/neutral signals
- **<0**: Bearish (Red) - Bearish signals

**Maximum Possible Score:** ~15-20 points (with explosive bottom detection)

### Category-Specific Scoring

Different categories use different parameters:
- **Cryptocurrencies/Tech Stocks:** Mean-reversion logic (oversold = opportunity)
- **Mining/Commodities:** Trend-following logic (oversold = buy signal)
- **Index ETFs:** Standard trend-following
- **Volatile Assets:** Higher explosive bottom bonuses

## 🧪 Backtesting & Optimization

### Unified Backtesting Framework

All backtesting consolidated into `backtest_framework.py`:

```python
from backtest_framework import BacktestFramework
from improved_scoring import improved_scoring
from technical_analysis import load_symbols_config

framework = BacktestFramework(improved_scoring, load_symbols_config())
results = framework.run_backtest()
analysis = framework.analyze_results(results)
framework.print_analysis(analysis)
```

### Performance Metrics

**Current Performance (After Optimization):**
- **High Score Catch Rate:** 24.6% (9.5x improvement from 0%)
- **Good Score Catch Rate:** 29.3% (12x improvement from 2.4%)
- **IREN 1000%+ Moves:** 9.5-15.5 score (was 0-1.5) ✅

**Category Performance:**
- Index ETFs: 91.3% high score catch rate
- Mining stocks: 46.4% high score catch rate
- Cryptocurrencies: 41.7% high score catch rate
- FAANG stocks: 41.9% high score catch rate

See `docs/OPTIMIZATION_SUMMARY.md` for detailed results.

## 📁 Project Structure

```
technical_analysis/
├── technical_analysis.py      # Main analysis script
├── improved_scoring.py       # Improved scoring with explosive bottom detection
├── backtest_framework.py      # Unified backtesting framework
├── category_optimization.py   # Category-specific parameters
├── optimize_scoring.py        # Optimization script
├── scoring_integration.py     # Integration layer
├── advanced_indicators.py     # PI and Hash Ribbon indicators
├── scoring_common.py          # Common scoring logic (shared)
├── indicators_common.py      # Common indicator calculations (shared)
├── predictive_indicators.py   # Predictive indicator helpers
├── visualize_scores.py        # HTML visualization generator
├── configuration.json         # Categories, aliases, tf_rules
├── run_full_analysis.sh       # Full pipeline script
├── docs/                      # All documentation (23 files)
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── BACKTESTING_CONSOLIDATION.md
│   ├── EXPLOSIVE_MOVES_ANALYSIS.md
│   └── ... (20 other docs)
└── README.md                  # This file
```

## 📚 Documentation

All documentation organized in `docs/` folder:

- **Setup & Usage:**
  - `docs/SCRIPTS_README.md` - Script usage guide
  - `docs/BACKTESTING_README.md` - Backtesting quick start
  
- **Optimization & Analysis:**
  - `docs/OPTIMIZATION_SUMMARY.md` - Optimization results
  - `docs/EXPLOSIVE_MOVES_ANALYSIS.md` - Explosive moves analysis
  - `docs/SCORING_IMPROVEMENTS.md` - Scoring improvements
  
- **Research:**
  - `docs/GOLD_RSI_RESEARCH.md` - Gold RSI research findings
  - `docs/PREDICTIVE_SCORING_RESEARCH.md` - Predictive indicators research
  
- **Implementation:**
  - `docs/BACKTESTING_CONSOLIDATION.md` - Framework documentation
  - `docs/REFACTORING_SUMMARY.md` - Code refactoring summary
  - `docs/FINAL_OPTIMIZATION_REPORT.md` - Final optimization report

## 🎯 Key Improvements

Based on comprehensive backtesting across 700+ explosive moves:

1. **Explosive Bottom Detection** - Catches bottoms before big moves
2. **Category-Specific Parameters** - Different strategies per asset class
3. **PI Indicator Integration** - Price Intensity for explosive move prediction
4. **ADX Rising Detection** - Catches trends as they start (+3 points)
5. **Improved Oversold Handling** - Oversold + Strong ADX = Opportunity

## 📊 Example: IREN Case Study

**IREN (Iris Energy) - April 2025:**
- Entry: $5.59
- Peak: $62.90 (6 months later)
- **Return: 1025%**
- **Score at Entry: 9.5-15.5** ✅ (was 0-1.5)

**Why It Worked:**
- Explosive bottom detection triggered
- Oversold RSI (32-36) + Strong ADX (30+) + Capitulation (-50%)
- All conditions aligned = High score

## 🔧 Advanced Usage

### Run Optimization Backtest
```bash
python optimize_scoring.py
```

### Custom Backtest
```python
from backtest_framework import BacktestFramework
from improved_scoring import improved_scoring
from technical_analysis import load_symbols_config

framework = BacktestFramework(improved_scoring, load_symbols_config())
results = framework.run_backtest(
    categories=['miner_hpc', 'cryptocurrencies'],
    symbols_per_category=5,
    min_move_pct=50
)
analysis = framework.analyze_results(results)
framework.print_analysis(analysis)
```

## 📈 Categories Analyzed

- `quantum` - Quantum computing stocks
- `miner_hpc` - Mining/HPC companies
- `faang_hot_stocks` - FAANG + hot tech
- `tech_stocks` - Other tech stocks
- `cryptocurrencies` - Crypto pairs (BTC, ETH, SOL)
- `precious_metals` - Futures (Gold, Silver, etc.)
- `index_etfs` - ETFs (SPY, IWM, etc.)
- `clean_energy_materials` - Clean energy materials
- `silver_miners_esg` - ESG silver miners
- `renewable_energy` - Renewable energy stocks
- `battery_storage` - Battery storage companies
- `next_gen_automotive` - Next-generation automotive (EV, autonomous)

## ⚙️ Configuration

Symbols and categories are in `configuration.json` under `"categories"`.

## 📝 License

See individual files for license information.

---

*Last Updated: 2026-01-19*
*System Status: Production Ready ✅*
*Optimization Status: Complete ✅*
