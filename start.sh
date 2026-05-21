#!/usr/bin/env bash
set -e

# Check uv is available
if ! command -v uv &> /dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing dependencies..."
uv sync

echo "Starting Event Ledger API..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
