#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  uv venv
fi

uv run uvicorn app.main:app --reload --app-dir src &
API_PID=$!

if command -v python3 >/dev/null 2>&1; then
  (cd interface && python3 -m http.server 5173) &
  INTERFACE_PID=$!
else
  echo "python3 not found; skipping interface server." >&2
  INTERFACE_PID=""
fi

if [[ -d "ui" ]]; then
  if command -v npm >/dev/null 2>&1; then
    if [[ ! -d "ui/node_modules" ]]; then
      (cd ui && npm install)
    fi
    (cd ui && npm run dev -- --port 5174) &
    USER_UI_PID=$!
  else
    echo "npm not found; skipping user UI dev server." >&2
    USER_UI_PID=""
  fi
fi

cleanup() {
  if [[ -n "${INTERFACE_PID:-}" ]]; then
    kill "$INTERFACE_PID" 2>/dev/null || true
  fi
  if [[ -n "${USER_UI_PID:-}" ]]; then
    kill "$USER_UI_PID" 2>/dev/null || true
  fi
  kill "$API_PID" 2>/dev/null || true
}

trap cleanup EXIT

wait "$API_PID"
