#!/usr/bin/env bash
set -euo pipefail
pids=$(ss -ltnp 2>/dev/null | awk '/:8082 /{print $NF}' | sed -E 's/.*pid=([0-9]+).*/\1/')
if [ -n "${pids:-}" ]; then
  echo "[KILL_8082] PIDs: $pids"
  kill $pids || true
  sleep 0.5
  pgrep -f "uvicorn .*:8082" >/dev/null && kill -9 $(pgrep -f "uvicorn .*:8082") || true
else
  echo "[KILL_8082] nada ouvindo em :8082"
fi
