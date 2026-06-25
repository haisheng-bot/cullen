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
