#!/bin/zsh
set -e

cd "$(dirname "$0")"

PYTHON_BIN=".venv311/bin/python"
PORT="8000"
URL="http://127.0.0.1:${PORT}/"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python 3.11 virtual environment not found."
  echo "Please run:"
  echo "/Users/cullen/.local/bin/python3.11 -m venv .venv311"
  echo ".venv311/bin/python -m pip install -e ."
  read -r "?Press Enter to close..."
  exit 1
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Installing OpenStock AI dependencies..."
  "$PYTHON_BIN" -m pip install -e .
fi

# Phase 1 cutover (page-split migration, commit 7): the backend now serves apps/web-react/dist/
# instead of apps/web/index.html, so this needs a built frontend. Same self-healing pattern as the
# Python venv check above: install/build only if missing.
WEB_REACT_DIR="apps/web-react"
if [ ! -d "$WEB_REACT_DIR/node_modules" ]; then
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "Node.js/npm not found. Please install Node.js (see apps/web-react/README.md) and re-run."
    read -r "?Press Enter to close..."
    exit 1
  fi
  echo "Installing OpenStock AI frontend dependencies..."
  (cd "$WEB_REACT_DIR" && npm install)
fi

if [ ! -f "$WEB_REACT_DIR/dist/index.html" ]; then
  echo "Building OpenStock AI frontend..."
  (cd "$WEB_REACT_DIR" && npm run build)
fi

if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "OpenStock AI is already running at ${URL}"
else
  echo "Starting OpenStock AI at ${URL}"
  "$PYTHON_BIN" -m uvicorn apps.api.main:app --host 127.0.0.1 --port "$PORT" &
fi

sleep 1
open "$URL"

echo ""
echo "OpenStock AI is ready:"
echo "$URL"
echo ""
echo "Keep this window open while using the app."
echo "Press Ctrl+C to stop the server if this window started it."
wait
