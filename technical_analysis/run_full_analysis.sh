#!/bin/bash

# Script to regenerate data and create visualization
# Usage: ./run_full_analysis.sh [--refresh] [--calculate-potential] [--category CATEGORY]
#
# Options:
#   --refresh              Force refresh all data (ignore cache)
#   --calculate-potential  Calculate relative potential (slower, ~30-45% more time)
#   --category CATEGORY    Process only specific category

set -e  # Exit on error

# Get the directory where this script is located
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
    echo "Error: Python not found. Please ensure Python 3 is installed."
    exit 1
fi

echo "Using Python: $PYTHON"
echo ""

# Step 1: Regenerate data for all categories
echo "=========================================="
echo "Step 1: Regenerating investment score data..."
echo "=========================================="
echo "Running: $PYTHON technical_analysis.py $*"
echo ""

$PYTHON technical_analysis.py "$@"

# Check if data generation was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Data generation failed!"
    exit 1
fi

# Check if results directory was created
if [ ! -d "result_scores" ]; then
    echo ""
    echo "Warning: result_scores directory was not found after data generation."
    echo "Continuing anyway in case visualization can use existing data..."
fi

# Step 2: Generate visualizations for all categories
echo ""
echo "=========================================="
echo "Step 2: Generating visualizations..."
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

# Check if visualizations_output directory was created and has HTML files
if [ -d "visualizations_output" ] && [ -n "$(ls -A visualizations_output/*.html 2>/dev/null)" ]; then
    echo ""
    echo "=========================================="
    echo "✓ Complete! Opening visualizations in browser..."
    echo "=========================================="
    # Use the open_visualizations script
    bash open_visualizations.sh
else
    echo ""
    echo "Error: No HTML visualizations were created!"
    exit 1
fi
