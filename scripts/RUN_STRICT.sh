#!/usr/bin/env bash
set -euo pipefail
ROOT="/srv/projects/ai-router"
cd "$ROOT"

# envs de modelos
export OLLAMA_INSTRUCT_MODEL=${OLLAMA_INSTRUCT_MODEL:-llama3.1:8b-instruct-q5_K_M}
export OLLAMA_CODER_MODEL=${OLLAMA_CODER_MODEL:-deepseek-coder-v2:16b}

# apontar para os arquivos em config/
export ROUTER_CONFIG="$ROOT/config/router_config.yaml"
export ROUTER_POLICY="$ROOT/config/router_policy.yaml"

# opcional: carregar .env.local se existir (agora em config/)
set -a; [ -f "$ROOT/config/.env.local" ] && . "$ROOT/config/.env.local"; set +a

# venv
. "$ROOT/.venv/bin/activate"

# mata porta presa (idempotente)
ss -ltnp | awk '/:8082 /{print $NF}' | sed -E 's/.*pid=([0-9]+).*/\1/' | xargs -r kill || true
sleep 0.3
pgrep -f "uvicorn .*:8082" >/dev/null && kill -9 $(pgrep -f "uvicorn .*:8082") || true

# inicia
nohup uvicorn app.main:app --host 0.0.0.0 --port 8082 > .venv/uvicorn.log 2>&1 &
pid=$!
echo "[RUN_STRICT] pid: $pid log: .venv/uvicorn.log"

# espera /healthz
i=0; until curl -fsS http://localhost:8082/healthz >/dev/null 2>&1; do
  ((i++)); if [ $i -gt 120 ]; then
    echo "[RUN_STRICT] FAIL: /healthz não respondeu. Últimas linhas de log:"
    tail -n 120 .venv/uvicorn.log || true
    exit 1
  fi
  sleep 0.5
done
echo "[RUN_STRICT] API OK"
