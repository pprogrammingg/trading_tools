#!/bin/bash

# Script to run optimization backtest
# Usage: ./run_optimization.sh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.." || exit 1
. scripts/_common.sh
echo "Using Python: $PYTHON"
echo ""

echo "=========================================="
echo "Running Optimization Backtest..."
echo "=========================================="
echo "Running: $PYTHON backtesting/optimize_scoring.py"
echo ""

$PYTHON backtesting/optimize_scoring.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Optimization complete!"
    echo "=========================================="
    echo "Results saved to: backtesting/optimized_backtest_results.json"
else
    echo ""
    echo "Error: Optimization failed!"
    exit 1
fi
