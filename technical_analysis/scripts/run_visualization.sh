#!/bin/bash

# Script to run visualization and open HTML files
# Usage: ./run_visualization.sh
# 
# NOTE: This script is now a wrapper that:
# 1. Generates visualizations from existing result files
# 2. Opens all generated HTML files in browser
#
# For full pipeline (data generation + visualization), use: ./run_full_analysis.sh
# To only open existing visualizations, use: ./open_visualizations.sh

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Change to parent directory (technical_analysis root)
cd "$SCRIPT_DIR/.." || exit 1

# Determine Python executable (prefer .venv in technical_analysis)
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f "../venv/bin/python" ]; then
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

# Step 1: Generate visualizations
echo "=========================================="
echo "Generating visualizations from result files..."
echo "=========================================="
echo "Running: $PYTHON visualize_scores.py"
echo ""

$PYTHON visualize_scores.py

# Check if visualization was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Visualization generation failed!"
    exit 1
fi

# Step 2: Open all visualizations
echo ""
echo "=========================================="
echo "Opening visualizations in browser..."
echo "=========================================="
bash scripts/open_visualizations.sh
