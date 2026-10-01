#!/usr/bin/env bash

set -Eeuo pipefail

# Temporary external demo launcher.
# This wrapper does not modify the application source or .env files. Runtime
# URLs are injected into the backend/frontend child processes only.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ai-smart-factory-cloudflare.XXXXXX")"

BACKEND_PID=""
FRONTEND_PID=""
BACKEND_TUNNEL_PID=""
FRONTEND_TUNNEL_PID=""

cleanup() {
  set +e
  echo
  echo "Stopping temporary Cloudflare demo..."
  for pid in "$FRONTEND_TUNNEL_PID" "$BACKEND_TUNNEL_PID" "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  echo "Logs kept at: $LOG_DIR"
}
trap cleanup EXIT INT TERM

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required command not found: $1" >&2
    exit 1
  }
}

wait_for_url() {
  local log_file="$1"
  local label="$2"
  local url=""
  for _ in $(seq 1 60); do
    url="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$log_file" 2>/dev/null \
      | grep -v '^https://api\.trycloudflare\.com$' | head -n 1 || true)"
    if [[ -n "$url" ]]; then
      printf '%s\n' "$url"
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $label URL. See $log_file" >&2
  exit 1
}

require_command cloudflared
require_command npm

if [[ ! -x "$BACKEND_DIR/.venv/bin/uvicorn" ]]; then
  echo "Backend virtualenv is missing: $BACKEND_DIR/.venv/bin/uvicorn" >&2
  exit 1
fi

echo "Starting backend on http://127.0.0.1:8000 ..."
(
  cd "$BACKEND_DIR"
  exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "Starting backend Quick Tunnel ..."
cloudflared tunnel --url http://127.0.0.1:8000 >"$LOG_DIR/backend-tunnel.log" 2>&1 &
BACKEND_TUNNEL_PID=$!
BACKEND_URL="$(wait_for_url "$LOG_DIR/backend-tunnel.log" "backend")"

echo "Building frontend with backend URL: $BACKEND_URL ..."
(
  cd "$FRONTEND_DIR"
  NEXT_PUBLIC_API_BASE_URL="$BACKEND_URL" npm run build
  NEXT_PUBLIC_API_BASE_URL="$BACKEND_URL" npm run start -- --hostname 127.0.0.1 --port 3000
) >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "Starting frontend Quick Tunnel ..."
cloudflared tunnel --url http://127.0.0.1:3000 >"$LOG_DIR/frontend-tunnel.log" 2>&1 &
FRONTEND_TUNNEL_PID=$!
FRONTEND_URL="$(wait_for_url "$LOG_DIR/frontend-tunnel.log" "frontend")"

# Restart only the backend process so CORS accepts the temporary frontend URL.
kill "$BACKEND_PID" 2>/dev/null || true
wait "$BACKEND_PID" 2>/dev/null || true
echo "Restarting backend with temporary CORS origin: $FRONTEND_URL ..."
(
  cd "$BACKEND_DIR"
  CORS_ORIGINS="$FRONTEND_URL,http://localhost:3000,http://127.0.0.1:3000" exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

cat <<EOF

Temporary external URLs are ready:
  Frontend: $FRONTEND_URL
  Backend:  $BACKEND_URL

Open the Frontend URL in a browser. Press Ctrl+C here to stop all processes.
Logs: $LOG_DIR
EOF

wait "$FRONTEND_PID"
