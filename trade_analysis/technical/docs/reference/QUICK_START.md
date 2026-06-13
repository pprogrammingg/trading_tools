# Quick Start Guide

## Run Full Analysis
```bash
./run_full_analysis.sh
```

## Run Optimization Backtest
```bash
python optimize_scoring.py
```

## View Results
- Visualizations: `visualizations_output/*.html`
- Backtest results: `optimized_backtest_results.json`
- Documentation: `docs/` folder

## Key Improvements
- ✅ Explosive bottom detection (IREN 1000%+ moves: 0-1.5 → 9.5-15.5 score)
- ✅ PI Indicator integration
- ✅ Category-specific optimizations
- ✅ 24.6% high score catch rate (9.5x improvement)

See `docs/OPTIMIZATION_SUMMARY.md` for details.
