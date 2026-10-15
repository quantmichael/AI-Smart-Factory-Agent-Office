#!/usr/bin/env bash

set -Eeuo pipefail

# Production launcher for the Cloudflare custom-domain routes:
#   https://factory.aipath.kr/*     -> http://127.0.0.1:3000
#   https://factory.aipath.kr/api/* -> http://127.0.0.1:8000
#
# The empty public API base is intentional. It makes both REST and SSE use
# same-origin /api/v1 paths in the browser bundle. The separate Quick Tunnel
# launcher keeps injecting its temporary backend URL for demos.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
RUNTIME_DIR="$PROJECT_ROOT/artifacts/cloudflare_external/custom_domain"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  set +e
  echo
  echo "Stopping custom-domain application processes..."
  for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  rm -f "$RUNTIME_DIR/backend.pid" "$RUNTIME_DIR/frontend.pid"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required command not found: $1" >&2
    exit 1
  }
}

port_is_busy() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_health() {
  local label="$1"
  local url="$2"
  for _ in $(seq 1 60); do
    if curl --fail --silent --show-error "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $label: $url" >&2
  return 1
}

require_command curl
require_command grep
require_command lsof
require_command npm

if [[ ! -x "$BACKEND_DIR/.venv/bin/uvicorn" ]]; then
  echo "Backend virtualenv is missing: $BACKEND_DIR/.venv/bin/uvicorn" >&2
  exit 1
fi

for port in 3000 8000; do
  if port_is_busy "$port"; then
    echo "Port $port is already in use. Stop the existing app launcher first." >&2
    exit 1
  fi
done

mkdir -p "$RUNTIME_DIR"

echo "Building frontend with same-origin API paths..."
(
  cd "$FRONTEND_DIR"
  NEXT_PUBLIC_API_BASE_URL="" npm run build
)

if grep -R -E -q 'https://[a-z0-9-]+\.trycloudflare\.com' \
  "$FRONTEND_DIR/.next/static" "$FRONTEND_DIR/.next/server"; then
  echo "Build rejected: a trycloudflare.com URL remains in the frontend bundle." >&2
  exit 1
fi

echo "Starting backend on http://127.0.0.1:8000 ..."
(
  cd "$BACKEND_DIR"
  exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
) >"$RUNTIME_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
printf '%s\n' "$BACKEND_PID" >"$RUNTIME_DIR/backend.pid"

wait_for_health "backend" "http://127.0.0.1:8000/api/v1/health"

echo "Starting frontend on http://127.0.0.1:3000 ..."
(
  cd "$FRONTEND_DIR"
  exec env NEXT_PUBLIC_API_BASE_URL="" npm run start -- --hostname 127.0.0.1 --port 3000
) >"$RUNTIME_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
printf '%s\n' "$FRONTEND_PID" >"$RUNTIME_DIR/frontend.pid"

wait_for_health "frontend" "http://127.0.0.1:3000"

cat <<EOF

Custom-domain application processes are ready:
  Frontend: https://factory.aipath.kr
  API:      https://factory.aipath.kr/api/v1

REST and SSE use same-origin /api/v1 paths.
Press Ctrl+C here to stop the application processes.
Logs: $RUNTIME_DIR
EOF

wait "$FRONTEND_PID"
