#!/bin/bash
# Run analysis in batches and open results incrementally

BATCH_SIZE=3  # Process 3 categories at a time
TOTAL_CATEGORIES=21

echo "============================================================"
echo "BATCH ANALYSIS RUNNER"
echo "============================================================"
echo "Batch size: $BATCH_SIZE categories"
echo "Total categories: $TOTAL_CATEGORIES"
echo ""

# Calculate number of batches
NUM_BATCHES=$(( (TOTAL_CATEGORIES + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "Will process in $NUM_BATCHES batches"
echo ""

for BATCH in $(seq 0 $((NUM_BATCHES - 1))); do
    echo "============================================================"
    echo "BATCH $((BATCH + 1))/$NUM_BATCHES"
    echo "============================================================"
    echo ""
    
    # Run analysis for this batch
    cd "$(dirname "$0")/.."
    ../venv/bin/python3 technical_analysis.py --batch-size $BATCH_SIZE --batch-index $BATCH --refresh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Batch $((BATCH + 1)) complete!"
        
        # Generate visualizations for completed categories
        echo "Generating visualizations..."
        ../venv/bin/python3 visualize_scores.py
        
        # Open visualizations for this batch
        echo "Opening visualizations..."
        python3 << 'PYEOF'
import subprocess
from pathlib import Path
import json

# Get categories in this batch
config_file = Path("symbols_config.json")
with open(config_file, 'r') as f:
    config = json.load(f)

batch_size = 3
batch_index = int('${BATCH}')
batch_start = batch_index * batch_size
batch_end = batch_start + batch_size

all_categories = list(config.keys())
batch_categories = all_categories[batch_start:batch_end]

print(f"Opening visualizations for: {', '.join(batch_categories)}")

viz_dir = Path("visualizations_output")
for category in batch_categories:
    html_file = viz_dir / f"{category}_scores.html"
    if html_file.exists():
        try:
            subprocess.Popen(['open', str(html_file)], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            print(f"  ✓ Opened {category}")
        except:
            print(f"  ✗ Failed to open {category}")
PYEOF
        
        echo ""
        echo "Press Enter to continue to next batch, or Ctrl+C to stop..."
        read
    else
        echo ""
        echo "❌ Batch $((BATCH + 1)) failed!"
        exit 1
    fi
done

echo ""
echo "============================================================"
echo "✅ ALL BATCHES COMPLETE!"
echo "============================================================"
