#!/bin/bash
# Run analysis in batches: refresh yfinance data only on the first batch, then
# build per-category HTML for each batch; after all batches, rebuild index/aggregate once.

set -euo pipefail

cd "$(dirname "$0")/.."
. scripts/_common.sh

BATCH_SIZE="${BATCH_SIZE:-3}"
TOTAL_CATEGORIES=$("$PYTHON" -c "import json; d=json.load(open('configuration.json')); print(len(d.get('categories', {})))" 2>/dev/null || echo 21)
if ! [[ "$TOTAL_CATEGORIES" =~ ^[0-9]+$ ]] || [ "$TOTAL_CATEGORIES" -lt 1 ]; then
  echo "Could not read category count from configuration.json; defaulting to 21"
  TOTAL_CATEGORIES=21
fi

# Calculate number of batches
NUM_BATCHES=$(( (TOTAL_CATEGORIES + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "============================================================"
echo "BATCH ANALYSIS RUNNER"
echo "============================================================"
echo "Batch size: $BATCH_SIZE categories"
echo "Total categories: $TOTAL_CATEGORIES (from configuration.json)"
echo "Will process in $NUM_BATCHES batches"
echo "  • Batch 0 only: --refresh (yfinance cache reset for that run)"
echo "  • Per batch:    per-category score HTML (no full index on each pass)"
echo "  • At end:       full index + aggregate pages"
echo "============================================================"
echo ""

for BATCH in $(seq 0 $((NUM_BATCHES - 1))); do
  echo "============================================================"
  echo "BATCH $((BATCH + 1))/$NUM_BATCHES"
  echo "============================================================"
  echo ""

  REFRESH_FLAG=""
  if [ "$BATCH" -eq 0 ]; then
    REFRESH_FLAG="--refresh"
  fi
  if ! $PYTHON technical_analysis.py --batch-size "$BATCH_SIZE" --batch-index "$BATCH" $REFRESH_FLAG; then
    echo "❌ Batch $((BATCH + 1)) failed!"
    exit 1
  fi

  echo ""
  echo "✅ Analysis batch $((BATCH + 1)) complete!"

  # Per-category pages for this batch only (skip index/aggregate; faster, fewer redundant network calls)
  BATCH_CATEGORIES=$(
    $PYTHON -c "import json; p='configuration.json'; b=int('${BATCH}'); bs=int('${BATCH_SIZE}'); cats=list(json.load(open(p)).get('categories',{}).keys()); [print(c) for c in cats[b*bs:b*bs+bs]]"
  )
  echo "Generating per-category score HTML (no full index)..."
  for category in $BATCH_CATEGORIES; do
    $PYTHON visualize_scores.py --category "$category" --no-index
  done

  echo "Opening visualizations for this batch..."
  $PYTHON - "$BATCH" "$BATCH_SIZE" << 'PYEOF'
import subprocess
import json
import sys
from pathlib import Path

batch_index = int(sys.argv[1])
batch_size = int(sys.argv[2])
config_file = Path("configuration.json")
data = json.loads(config_file.read_text())
all_categories = list(data.get("categories", {}).keys())
batch_start = batch_index * batch_size
batch_categories = all_categories[batch_start:batch_start + batch_size]
print(f"Opening: {', '.join(batch_categories)}")

viz_dir = Path("visualizations_output")
for category in batch_categories:
    html_file = viz_dir / f"{category}_scores.html"
    if html_file.exists():
        try:
            subprocess.Popen(
                ['open', str(html_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"  ✓ Opened {category}")
        except OSError:
            print(f"  ✗ Failed to open {category}")
PYEOF

  if [ "$BATCH" -lt $((NUM_BATCHES - 1)) ]; then
    echo ""
    echo "Press Enter to continue to next batch, or Ctrl+C to stop..."
    read
  fi
  echo ""
done

echo "============================================================"
echo "Rebuilding index + aggregate pages (full visualize, index + extras)..."
echo "============================================================"
$PYTHON visualize_scores.py

echo ""
echo "============================================================"
echo "✅ ALL BATCHES COMPLETE (index and aggregates updated at end)"
echo "============================================================"
