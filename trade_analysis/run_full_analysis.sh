#!/bin/bash
# Trade analysis pipeline: technical scores → index.html
#
# Usage (from trade_analysis/):
#   ./run_full_analysis.sh
#   ./run_full_analysis.sh --refresh --live-fundamentals --stoch-rsi
#
# Flags:
#   --refresh             Re-download OHLCV for technical_analysis.py
#   --live-fundamentals   yfinance fundamental scores in index (slow)
#   --stoch-rsi           Fill Stoch RSI columns in index (slow)
#   --index-limit N       Max total rows in index.html (default 250)
#   --max-picks-per-sector N   Max picks per sector (default 10)

set -e

TRADE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TECH="$TRADE_ROOT/technical"
# shellcheck source=scripts/pipeline_ui.sh
. "$TRADE_ROOT/scripts/pipeline_ui.sh"

TECH_ARGS=()
INDEX_ARGS=(--limit 250 --max-picks-per-sector 10 --etfs-per-industry 2)
LIVE_FUND=false
STOCH_RSI=false
REFRESH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --live-fundamentals) LIVE_FUND=true; shift ;;
    --stoch-rsi) STOCH_RSI=true; shift ;;
    --index-limit) INDEX_ARGS=(--limit "$2" --max-picks-per-sector 10 --etfs-per-industry 2); shift 2 ;;
    --index-limit=*) INDEX_ARGS=(--limit "${1#*=}" --max-picks-per-sector 10 --etfs-per-industry 2); shift ;;
    --max-picks-per-sector) INDEX_ARGS+=(--max-picks-per-sector "$2"); shift 2 ;;
    --max-picks-per-sector=*) INDEX_ARGS+=(--max-picks-per-sector "${1#*=}"); shift ;;
    --refresh) REFRESH=true; TECH_ARGS+=("$1"); shift ;;
    --full) REFRESH=true; LIVE_FUND=true; STOCH_RSI=true; TECH_ARGS+=(--refresh); shift ;;
    *) TECH_ARGS+=("$1"); shift ;;
  esac
done

$LIVE_FUND && INDEX_ARGS+=(--live-fundamentals)
$STOCH_RSI && INDEX_ARGS+=(--stoch-rsi)

export PIPELINE_TOTAL_STEPS=2
INDEX_STEP=2

cd "$TECH" || exit 1
# shellcheck source=technical/scripts/_common.sh
. "$TECH/scripts/_common.sh"

pipeline_ui_init
pipeline_print_run_config

# ── Step 1: Technical scores ────────────────────────────────────────────────
pipeline_step_begin 1 "Technical scores" \
  "Download OHLCV, compute indicators, write technical/result_scores/*_results.json"
$PYTHON technical_analysis.py "${TECH_ARGS[@]}"
pipeline_step_end ok "result JSON updated"

# ── Unified trade index ─────────────────────────────────────────────────────
pipeline_step_begin "$INDEX_STEP" "Unified trade index" \
  "Merge technical + fundamental columns → trade_analysis/index.html"
$PYTHON "$TRADE_ROOT/build_trade_index.py" "${INDEX_ARGS[@]}"
INDEX_ROWS=""
if [[ -f "$TRADE_ROOT/index.html" ]]; then
  INDEX_ROWS="index.html ready"
else
  echo "Error: index.html was not created at $TRADE_ROOT/index.html"
  pipeline_step_end fail "index.html missing"
  exit 1
fi
pipeline_step_end ok "$INDEX_ROWS"

pipeline_print_summary

if [[ -f "$TRADE_ROOT/index.html" ]]; then
  open -a "${BROWSER:-Safari}" "$TRADE_ROOT/index.html" 2>/dev/null || true
fi
