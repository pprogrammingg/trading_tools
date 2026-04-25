# Shared for run_*.sh: set PYTHON when sourced from technical_analysis root.
# Usage: cd technical_analysis && . scripts/_common.sh
# Prefer single venv at repo root to avoid duplicate venvs and pycache.
if [ -f "../.venv/bin/python" ]; then
    PYTHON="../.venv/bin/python"
elif [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
elif [ -f "../env/bin/python" ]; then
    PYTHON="../env/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Error: Python not found. Create repo root venv: python3 -m venv .venv && .venv/bin/pip install -r technical_analysis/requirements.txt"
    exit 1
fi
export PYTHON
