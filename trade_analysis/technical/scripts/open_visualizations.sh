#!/bin/bash
# Open the main trade analysis index (trade_analysis/index.html).

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TRADE_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
BROWSER="${BROWSER:-Safari}"

if [ -f "$TRADE_ROOT/index.html" ]; then
    echo "Opening $TRADE_ROOT/index.html in $BROWSER..."
    open -a "$BROWSER" "$TRADE_ROOT/index.html"
    exit 0
fi

if [ -f "$SCRIPT_DIR/../visualizations_output/index.html" ]; then
    echo "Opening technical visualizations index..."
    open -a "$BROWSER" "$SCRIPT_DIR/../visualizations_output/index.html"
    exit 0
fi

echo "Error: No index.html found. Run build_trade_index.py or visualize_scores.py first."
exit 1
