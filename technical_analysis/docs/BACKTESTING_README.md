# Backtesting Framework - Quick Start

## Unified Framework

All backtesting is now consolidated into `backtest_framework.py` - a robust, reusable framework.

## Quick Start

### Run Optimization Backtest
```bash
python optimize_scoring.py
```

This will:
- Test all categories
- Find explosive moves (>30% in 60 days)
- Analyze scoring performance
- Save results to `optimized_backtest_results.json`

### Custom Backtest
```python
from backtest_framework import BacktestFramework
from improved_scoring import improved_scoring
from technical_analysis import load_symbols_config

# Initialize
framework = BacktestFramework(improved_scoring, load_symbols_config())

# Run backtest
results = framework.run_backtest(
    categories=['miner_hpc', 'cryptocurrencies'],  # Specific categories
    symbols_per_category=5,  # Test more symbols
    min_move_pct=50  # Only 50%+ moves
)

# Analyze
analysis = framework.analyze_results(results)
framework.print_analysis(analysis)
```

## Key Features

- **Explosive Bottom Detection:** Catches bottoms before big moves
- **Category-Aware:** Different parameters per category
- **PI Indicator:** Price Intensity for explosive move prediction
- **Comprehensive Analysis:** Category performance, catch rates, best opportunities

## Results

Current performance:
- **24.6%** high score catch rate (>=6)
- **29.3%** good score catch rate (>=4)
- IREN 1000%+ moves: **9.5-15.5 score** (was 0-1.5)

See `OPTIMIZATION_SUMMARY.md` for details.
