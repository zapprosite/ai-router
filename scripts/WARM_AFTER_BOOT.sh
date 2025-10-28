#!/usr/bin/env bash
set -euo pipefail
BASE="http://localhost:8082"
for i in {1..10}; do
  curl -fsS "$BASE/healthz" && break || sleep 2
done
curl -fsS "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Diga apenas: OK"}]}' >/dev/null || true
curl -fsS "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}' >/dev/null || true
