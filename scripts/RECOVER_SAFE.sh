#!/usr/bin/env bash
set -euo pipefail

echo "[KILL] curls/monitores/stress"
pkill -f STRESS_LOCAL.sh || true
pkill -f STRESS_MATRIX.sh || true
pkill -f GPU_MON.sh || true
pkill -f "curl .*8082/route" || true
pkill -f "curl .*actions/test" || true

echo "[CHECK] GPU"
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true

echo "[RESTART] Ollama (se existir)"
sudo systemctl restart ollama || true

echo "[FREE PORT] 8082 (se preso)"
if ! curl -fsS http://localhost:8082/healthz >/dev/null 2>&1; then
  lsof -i :8082 -P -n || true
  fuser -k 8082/tcp || true
fi

echo "[RESTART] ai-router"
sudo systemctl restart ai-router

echo "[WAIT] healthz até 20s"
for i in {1..20}; do
  if curl -fsS http://localhost:8082/healthz >/dev/null 2>&1; then
    echo "router OK"; break
  fi
  sleep 1
done

echo "[TAIL] últimos logs"
journalctl -u ai-router -n 40 --no-pager | tail -n 20 || true
