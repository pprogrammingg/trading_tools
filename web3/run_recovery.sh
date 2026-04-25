#!/usr/bin/env bash
# Single entry point for wallet recovery. Uses repo venv.
#   ./run_recovery.sh [guess.json]              # baseline run
#   ./run_recovery.sh run [guess.json]
#   ./run_recovery.sh uncertain 1|2|3|4 [guess.json]
#   ./run_recovery.sh check-target
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
. scripts/_common.sh
"$PYTHON" recovery.py "$@"
