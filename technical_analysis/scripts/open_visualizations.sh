#!/bin/bash

# Script to open visualization index (and optionally all HTML files) in browser.
# Usage: ./open_visualizations.sh          # open index only
#        ./open_visualizations.sh --all    # open all category HTML files
#
# Uses: open -a Safari (hard fix; bypasses default file:// handler / AppleScript -10661).
# To use Chrome instead: BROWSER="Google Chrome" ./open_visualizations.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.." || exit 1

BROWSER="${BROWSER:-Google Chrome}"

if [ ! -d "visualizations_output" ]; then
    echo "Error: visualizations_output directory not found!"
    echo "Please run visualize_scores.py first to generate visualizations."
    exit 1
fi

if [ "$1" = "--all" ]; then
    html_count=$(find visualizations_output -name "*.html" -type f ! -name "test_*" | wc -l | tr -d ' ')
    echo "Opening $html_count visualization(s) in $BROWSER..."
    for html_file in visualizations_output/*.html; do
        if [ -f "$html_file" ]; then
            filename=$(basename "$html_file")
            [[ "$filename" == "test_"* ]] && continue
            echo "  Opening $filename..."
            open -a "$BROWSER" "$html_file"
        fi
    done
    echo "Done."
    exit 0
fi

if [ ! -f "visualizations_output/index.html" ]; then
    echo "Error: visualizations_output/index.html not found!"
    exit 1
fi

echo "Opening visualization index in $BROWSER..."
open -a "$BROWSER" "visualizations_output/index.html"
echo "Done."
