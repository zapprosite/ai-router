#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8082}"

echo "[1/3] texto curto"
curl -sS -X POST "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' | python3 -m json.tool | sed -n '1,20p'

echo "[2/3] código simples"
curl -sS -X POST "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true,"budget":"low"}' \
  | python3 -m json.tool | sed -n '1,24p'

echo "[3/3] código complexo"
curl -sS -X POST "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Traceback: ... Faça refactor multi-file com testes pytest e gere patch."}],"prefer_code":true}' \
  | python3 -m json.tool | sed -n '1,24p'

echo "OK"
