#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
BASE="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "[warm] llama3.1:8b-instruct-q5_K_M"
curl -fsS "$BASE/api/chat" -H 'content-type: application/json' \
  -d '{"model":"llama3.1:8b-instruct-q5_K_M","messages":[{"role":"user","content":"Diga apenas: OK"}],"stream":false}' >/dev/null || true

echo "[warm] deepseek-coder-v2:16b"
curl -fsS "$BASE/api/chat" -H 'content-type: application/json' \
  -d '{"model":"deepseek-coder-v2:16b","messages":[{"role":"user","content":"Escreva soma(n1,n2) com docstring."}],"stream":false}' >/dev/null || true

echo "OK"
