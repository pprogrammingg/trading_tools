#!/bin/bash
# Back-compat wrapper — canonical pipeline is trade_analysis/run_full_analysis.sh
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/run_full_analysis.sh" "$@"
