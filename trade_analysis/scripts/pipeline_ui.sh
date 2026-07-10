# shellcheck shell=bash
# Pretty pipeline logging for run_full_analysis.sh (source, do not execute directly).

pipeline_ui_init() {
  PIPELINE_T0=${SECONDS:-0}
  PIPELINE_STEP=0
  PIPELINE_STEP_NAMES=()
  PIPELINE_STEP_DURS=()
  if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    _PUI_BOLD=$(tput bold 2>/dev/null || true)
    _PUI_DIM=$(tput dim 2>/dev/null || true)
    _PUI_CYAN=$(tput setaf 6 2>/dev/null || true)
    _PUI_GREEN=$(tput setaf 2 2>/dev/null || true)
    _PUI_YELLOW=$(tput setaf 3 2>/dev/null || true)
    _PUI_MAG=$(tput setaf 5 2>/dev/null || true)
    _PUI_RESET=$(tput sgr0 2>/dev/null || true)
  else
    _PUI_BOLD="" _PUI_DIM="" _PUI_CYAN="" _PUI_GREEN="" _PUI_YELLOW="" _PUI_MAG="" _PUI_RESET=""
  fi
}

pipeline_format_duration() {
  local s=${1:-0}
  if (( s >= 3600 )); then
    printf '%dh %02dm %02ds' $((s / 3600)) $(((s % 3600) / 60)) $((s % 60))
  elif (( s >= 60 )); then
    printf '%dm %02ds' $((s / 60)) $((s % 60))
  else
    printf '%ds' "$s"
  fi
}

pipeline_now() {
  date '+%Y-%m-%d %H:%M:%S'
}

pipeline_print_header() {
  local title=$1
  echo ""
  echo "${_PUI_CYAN}╔══════════════════════════════════════════════════════════════════════╗${_PUI_RESET}"
  printf "${_PUI_CYAN}║${_PUI_RESET}${_PUI_BOLD} %-68s${_PUI_RESET}${_PUI_CYAN}║${_PUI_RESET}\n" "$title"
  echo "${_PUI_CYAN}╚══════════════════════════════════════════════════════════════════════╝${_PUI_RESET}"
}

pipeline_print_run_config() {
  pipeline_print_header "TRADE ANALYSIS — INDEX PIPELINE"
  echo ""
  echo "${_PUI_BOLD}Started${_PUI_RESET}  $(pipeline_now)"
  echo "${_PUI_BOLD}Python${_PUI_RESET}   ${PYTHON:-python}"
  echo "${_PUI_BOLD}Root${_PUI_RESET}     ${TRADE_ROOT}"
  echo ""
  echo "${_PUI_BOLD}Run mode${_PUI_RESET}"
  local mode="standard (cached OHLCV where possible)"
  if $REFRESH && $LIVE_FUND && $STOCH_RSI; then
    mode="full refresh — OHLCV + live fundamentals + Stoch RSI"
  elif $REFRESH; then
    mode="refresh — fresh technical data"
  fi
  echo "  · ${mode}"
  echo "  · Technical refresh: $( $REFRESH && echo yes || echo no )"
  echo "  · Live fundamentals (index): $( $LIVE_FUND && echo yes || echo no )"
  echo "  · Stoch RSI (index): $( $STOCH_RSI && echo yes || echo no )"
  if ((${#TECH_ARGS[@]})); then
    echo "  · Extra technical args: ${TECH_ARGS[*]}"
  fi
  if ((${#INDEX_ARGS[@]})); then
    echo "  · Index args: ${INDEX_ARGS[*]}"
  fi
  echo ""
  local total_steps=${PIPELINE_TOTAL_STEPS:-2}
  echo "${_PUI_DIM}Stages: 1 technical scores → ${total_steps} unified index (index.html)${_PUI_RESET}"
  echo ""
}

pipeline_step_begin() {
  local num=$1
  local title=$2
  local detail=${3:-}
  PIPELINE_STEP=$num
  PIPELINE_STEP_NAMES[$num]=$title
  PIPELINE_STEP_T0=$SECONDS
  local total=${PIPELINE_TOTAL_STEPS:-2}
  echo ""
  echo "${_PUI_BOLD}┌──────────────────────────────────────────────────────────────────────┐${_PUI_RESET}"
  printf "${_PUI_BOLD}│ STEP %s/%s — %s\n" "$num" "$total" "$title"
  if [[ -n "$detail" ]]; then
    echo "│ ${detail}"
  fi
  echo "│ started $(pipeline_now)"
  echo "${_PUI_BOLD}└──────────────────────────────────────────────────────────────────────┘${_PUI_RESET}"
  echo ""
}

pipeline_step_end() {
  local status=$1
  local msg=${2:-done}
  local dur=$((SECONDS - PIPELINE_STEP_T0))
  PIPELINE_STEP_DURS[$PIPELINE_STEP]=$dur
  local icon color
  case "$status" in
    ok) icon="✓"; color="${_PUI_GREEN}" ;;
    warn) icon="⚠"; color="${_PUI_YELLOW}" ;;
    fail) icon="✗"; color="${_PUI_MAG}" ;;
    *) icon="·"; color="${_PUI_DIM}" ;;
  esac
  echo ""
  printf "${color}${icon} Step %s done in %s — %s${_PUI_RESET}\n" \
    "$PIPELINE_STEP" "$(pipeline_format_duration "$dur")" "$msg"
}

pipeline_print_summary() {
  local total=$((SECONDS - PIPELINE_T0))
  echo ""
  pipeline_print_header "PIPELINE COMPLETE"
  echo ""
  echo "${_PUI_BOLD}Total time${_PUI_RESET}  $(pipeline_format_duration "$total")"
  echo "${_PUI_BOLD}Output${_PUI_RESET}      ${TRADE_ROOT}/index.html"
  echo ""
}
