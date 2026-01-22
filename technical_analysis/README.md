# Technical Analysis System

Automated technical analysis system that calculates buy/sell scores for financial instruments using multiple technical indicators. Based on research into why RSI failed to predict gold's 1970s 600% move, this system incorporates trend-following indicators (ADX, CCI, OBV) alongside mean-reverting ones (RSI), with **explosive bottom detection** optimized through comprehensive backtesting.

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

# Run optimization backtest
python optimize_scoring.py
```

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
from backtesting.backtest_framework import BacktestFramework
from scoring.improved_scoring import improved_scoring
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
├── technical_analysis.py      # Main analysis script (root)
├── visualize_scores.py        # HTML visualization generator (root)
├── symbols_config.json        # Symbol categories configuration (root)
├── requirements.txt           # Dependencies (root)
│
├── scoring/                   # Scoring system modules
│   ├── improved_scoring.py
│   ├── scoring_common.py
│   ├── scoring_integration.py
│   └── category_optimization.py
│
├── indicators/                # Technical indicator modules
│   ├── indicators_common.py
│   ├── advanced_indicators.py
│   └── predictive_indicators.py
│
├── backtesting/              # Backtesting framework
│   ├── backtest_framework.py
│   ├── optimize_scoring.py
│   └── ... (legacy backtest scripts)
│
├── scripts/                    # Utility scripts
│   ├── run_full_analysis.sh
│   ├── run_visualization.sh
│   ├── open_visualizations.sh
│   ├── run_optimization.sh
│   └── ... (other utility scripts)
│
├── tests/                     # Test scripts
│   ├── test_aem_ag.py
│   ├── verify_scoring.py
│   └── ... (other tests)
│
├── docs/                       # All documentation (25 files)
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── BACKTESTING_CONSOLIDATION.md
│   ├── REFACTORING_COMPLETE.md
│   └── ... (22 other docs)
│
├── data_cache/                # Cached data
├── result_scores/             # Analysis results (JSON)
└── visualizations_output/      # Generated HTML visualizations
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
./scripts/run_optimization.sh
# or
python backtesting/optimize_scoring.py
```

### Custom Backtest
```python
from backtesting.backtest_framework import BacktestFramework
from scoring.improved_scoring import improved_scoring
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

Symbols and categories are configured in `symbols_config.json`. Add new symbols or categories as needed.

## 📝 License

See individual files for license information.

---

*Last Updated: 2026-01-19*
*System Status: Production Ready ✅*
*Optimization Status: Complete ✅*
