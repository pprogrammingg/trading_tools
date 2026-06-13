#!/bin/bash
# Full trade analysis pipeline: technical scores + fundamentals + unified index.
#
# Usage (from repo root or trade_analysis/):
#   ./run_full_analysis.sh [--refresh] [--calculate-potential] [--category CATEGORY]
#   ./run_full_analysis.sh --live-fundamentals --stoch-rsi --index-limit 200
#
# Extra flags (this script only):
#   --live-fundamentals   yfinance fundamental scores in index (slow)
#   --stoch-rsi           fill Stoch RSI columns in index (slow)
#   --index-limit N       max rows in index.html (default 150)

set -e

TRADE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TECH="$TRADE_ROOT/technical"
FUND="$TRADE_ROOT/fundamentals"

TECH_ARGS=()
INDEX_ARGS=(--limit 150)
VIZ_ARGS=()
LIVE_FUND=false
STOCH_RSI=false
REFRESH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --live-fundamentals) LIVE_FUND=true; shift ;;
    --stoch-rsi) STOCH_RSI=true; shift ;;
    --index-limit) INDEX_ARGS=(--limit "$2"); shift 2 ;;
    --index-limit=*) INDEX_ARGS=(--limit "${1#*=}"); shift ;;
    --refresh) REFRESH=true; TECH_ARGS+=("$1"); shift ;;
    *) TECH_ARGS+=("$1"); shift ;;
  esac
done

$LIVE_FUND && INDEX_ARGS+=(--live-fundamentals)
$STOCH_RSI && INDEX_ARGS+=(--stoch-rsi)

# Step 2 hits yfinance for ESG, market cap, perf vs SPY. Use cache unless --refresh.
if ! $REFRESH; then
  VIZ_ARGS+=(--no-network --skip-trending)
fi

cd "$TECH" || exit 1
# shellcheck source=technical/scripts/_common.sh
. "$TECH/scripts/_common.sh"
echo "Using Python: $PYTHON"
echo "Trade root:   $TRADE_ROOT"
echo ""

echo "=========================================="
echo "Step 1/4: Technical — regenerate scores"
echo "=========================================="
$PYTHON technical_analysis.py "${TECH_ARGS[@]}"

echo ""
echo "=========================================="
echo "Step 2/4: Technical — category visualizations"
echo "=========================================="
$PYTHON visualize_scores.py "${VIZ_ARGS[@]}"

echo ""
echo "=========================================="
echo "Step 3/4: Fundamentals — hot picks JSON (halal screen)"
echo "=========================================="
$PYTHON "$FUND/generate_fundamental_hot_picks.py" || echo "  (skipped or fallback — check yfinance)"

echo ""
echo "=========================================="
echo "Step 4/4: Combined index — index.html"
echo "=========================================="
$PYTHON "$TRADE_ROOT/build_trade_index.py" "${INDEX_ARGS[@]}"

if [[ -f "$TRADE_ROOT/index.html" ]]; then
  echo ""
  echo "=========================================="
  echo "✓ Complete! Opening trade_analysis/index.html"
  echo "=========================================="
  open -a "${BROWSER:-Safari}" "$TRADE_ROOT/index.html"
else
  echo "Error: index.html was not created at $TRADE_ROOT/index.html"
  exit 1
fi
