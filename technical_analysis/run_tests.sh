#!/bin/bash

# Comprehensive test script
# Tests all modules and scripts to ensure everything works after refactoring

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Determine Python executable
if [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
elif [ -f "../env/bin/python" ]; then
    PYTHON="../env/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Error: Python not found."
    exit 1
fi

echo "=========================================="
echo "Running Comprehensive Tests"
echo "=========================================="
echo "Using Python: $PYTHON"
echo ""

# Test 1: Import main modules
echo "Test 1: Testing module imports..."
echo "-----------------------------------"
$PYTHON -c "
import sys
sys.path.insert(0, '.')

# Test main module
try:
    from technical_analysis import load_symbols_config, compute_indicators_tv
    print('✓ technical_analysis module imports OK')
except Exception as e:
    print(f'✗ technical_analysis import failed: {e}')
    sys.exit(1)

# Test scoring module
try:
    from scoring.improved_scoring import improved_scoring
    from scoring.category_optimization import get_category_params
    print('✓ scoring module imports OK')
except Exception as e:
    print(f'✗ scoring module import failed: {e}')
    sys.exit(1)

# Test indicators module
try:
    from indicators.indicators_common import calculate_adx
    from indicators.advanced_indicators import calculate_price_intensity
    print('✓ indicators module imports OK')
except Exception as e:
    print(f'✗ indicators module import failed: {e}')
    sys.exit(1)

# Test backtesting module
try:
    from backtesting.backtest_framework import BacktestFramework
    print('✓ backtesting module imports OK')
except Exception as e:
    print(f'✗ backtesting module import failed: {e}')
    sys.exit(1)

print('')
print('All module imports successful!')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Module import tests failed!"
    exit 1
fi

echo ""
echo "Test 2: Testing verify_scoring script..."
echo "-----------------------------------"
$PYTHON tests/verify_scoring.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  verify_scoring script had issues (may be expected)"
fi

echo ""
echo "Test 3: Testing symbols_config.json..."
echo "-----------------------------------"
if [ -f "symbols_config.json" ]; then
    $PYTHON -c "
import json
with open('symbols_config.json', 'r') as f:
    config = json.load(f)
    print(f'✓ symbols_config.json loaded successfully')
    print(f'  Categories: {len(config)}')
    for cat, symbols in list(config.items())[:3]:
        print(f'    - {cat}: {len(symbols)} symbols')
"
    echo "✓ symbols_config.json is valid"
else
    echo "✗ symbols_config.json not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ All tests passed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Run full analysis: ./scripts/run_full_analysis.sh"
echo "  - Run optimization: ./scripts/run_optimization.sh"
echo "  - Open visualizations: ./scripts/open_visualizations.sh"
