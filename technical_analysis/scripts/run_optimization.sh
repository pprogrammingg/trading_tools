#!/bin/bash

# Script to run optimization backtest
# Usage: ./run_optimization.sh

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Change to parent directory (technical_analysis root)
cd "$SCRIPT_DIR/.." || exit 1

# Determine Python executable
if [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
elif [ -f "../env/bin/python" ]; then
    PYTHON="../env/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Error: Python not found. Please ensure Python 3 is installed."
    exit 1
fi

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
