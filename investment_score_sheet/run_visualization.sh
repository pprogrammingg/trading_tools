#!/bin/bash

# Script to run visualization and open HTML
# Usage: ./run_visualization.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Go to parent directory for venv
cd ..

# Activate virtual environment
source venv/bin/activate

# Go back to investment_score_sheet directory
cd investment_score_sheet

# Run the visualization script
echo "Generating visualization..."
python visualize_scores.py

# Check if HTML was created
if [ -f "scores_visualization.html" ]; then
    echo "Opening visualization in browser..."
    open scores_visualization.html
else
    echo "Error: scores_visualization.html was not created!"
    exit 1
fi
