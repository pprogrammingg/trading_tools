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

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.." || exit 1
. scripts/_common.sh
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
