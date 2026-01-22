#!/bin/bash

# Script to open all HTML visualizations in browser
# Usage: ./open_visualizations.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Change to parent directory (technical_analysis root)
cd "$SCRIPT_DIR/.." || exit 1

# Check if visualizations_output directory exists
if [ ! -d "visualizations_output" ]; then
    echo "Error: visualizations_output directory not found!"
    echo "Please run visualize_scores.py first to generate visualizations."
    exit 1
fi

# Count HTML files (excluding test files)
html_count=$(find visualizations_output -name "*.html" -type f ! -name "test_*" | wc -l | tr -d ' ')

if [ "$html_count" -eq 0 ]; then
    echo "Error: No HTML files found in visualizations_output directory!"
    exit 1
fi

echo "=========================================="
echo "Opening $html_count visualization(s) in browser..."
echo "=========================================="

# Open all HTML files (excluding test files)
opened_count=0
for html_file in visualizations_output/*.html; do
    if [ -f "$html_file" ]; then
        filename=$(basename "$html_file")
        # Skip test files
        if [[ "$filename" == "test_"* ]]; then
            continue
        fi
        echo "  Opening $filename..."
        if command -v open >/dev/null 2>&1; then
        open "$html_file"
        else
            echo "    Error: 'open' command not available on this system"
            exit 1
        fi
        opened_count=$((opened_count + 1))
    fi
done

echo ""
echo "✓ Opened $opened_count file(s) in browser"
