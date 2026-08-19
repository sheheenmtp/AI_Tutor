#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [[ -f "$BACKEND_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$BACKEND_DIR/.env"
    set +a
fi

if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
    BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"
elif [[ -x "$BACKEND_DIR/venv/bin/python" ]]; then
    BACKEND_PYTHON="$BACKEND_DIR/venv/bin/python"
else
    BACKEND_PYTHON="${PYTHON:-python3}"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "Frontend dependencies are missing. Run: make setup-frontend" >&2
    exit 1
fi

if ! "$BACKEND_PYTHON" -c "import fastapi, sqlalchemy, uvicorn" >/dev/null 2>&1; then
    echo "Backend dependencies are missing. Run: make setup-backend" >&2
    exit 1
fi

JUDGE0_URL="${JUDGE0_URL:-http://localhost:2358}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

check_optional_service() {
    local name="$1"
    local url="$2"

    if curl --fail --silent --max-time 2 "$url" >/dev/null 2>&1; then
        echo "$name: available"
    else
        echo "$name: offline (the core app will still start)"
    fi
}

cleanup() {
    trap - INT TERM EXIT
    [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
    [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

check_optional_service "Judge0" "$JUDGE0_URL/languages"
check_optional_service "Ollama" "$OLLAMA_URL/api/tags"

echo "Starting backend on http://localhost:8000"
(
    cd "$BACKEND_DIR"
    exec "$BACKEND_PYTHON" -m uvicorn app:app --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

sleep 1
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID"
fi

echo "Starting frontend on http://localhost:5173"
(
    cd "$FRONTEND_DIR"
    exec npm run dev -- --host
) &
FRONTEND_PID=$!

echo "AI Tutor is running. Press Ctrl+C to stop."
wait -n "$BACKEND_PID" "$FRONTEND_PID"
