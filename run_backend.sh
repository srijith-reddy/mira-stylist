#!/bin/bash
# MIRA Stylist — Start Backend

set -e

cd backend

PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.14}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [ ! -x ".venv/bin/python" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

".venv/bin/python" -m pip install -r requirements.txt >/dev/null
".venv/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
