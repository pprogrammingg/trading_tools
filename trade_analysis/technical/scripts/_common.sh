# Shared for run_*.sh: set PYTHON when sourced from trade_analysis/technical.
# Usage: cd trade_analysis/technical && . scripts/_common.sh
if [ -f "../../.venv/bin/python" ]; then
    PYTHON="../../.venv/bin/python"
elif [ -f "../../venv/bin/python" ]; then
    PYTHON="../../venv/bin/python"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON="../.venv/bin/python"
elif [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Error: Python not found. Create venv: python3 -m venv trade_analysis/.venv && pip install -r trade_analysis/technical/requirements.txt"
    exit 1
fi
export PYTHON
export TRADE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$TRADE_ROOT/technical:$TRADE_ROOT/fundamentals:$TRADE_ROOT:${PYTHONPATH:-}"
