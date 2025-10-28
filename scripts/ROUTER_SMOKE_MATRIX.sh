#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
API="${API:-http://localhost:8082}"

# sobe API se /healthz falhar
if ! curl -fsS "$API/healthz" >/dev/null 2>&1; then
  echo "[boot] starting API..."
  bash "$ROOT/scripts/RUN_STRICT.sh"
fi

# warm
bash "$ROOT/scripts/WARM_LOCAL.sh" >/dev/null || true

jq_expect() {
  local want="$1"
  local got
  got=$(jq -r '.model_id' <(cat) 2>/dev/null || echo "")
  if [[ "$got" != "$want" ]]; then
    echo "[FAIL] expected=$want got=$got"
    exit 1
  else
    echo "[OK] $want"
  fi
}

echo
echo "== DOCS =="
curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}],"budget":"low"}' \
| tee /tmp/out.json | jq_expect "llama-3.1-8b-instruct"

curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Resuma padrões de RAG e quando usar cada um, em bullets."}],"budget":"low"}' \
| tee /tmp/out.json | jq_expect "llama-3.1-8b-instruct"

curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique streaming + backpressure em APIs, cite 3 estratégias com prós/contras."}],"budget":"balanced"}' \
| tee /tmp/out.json | jq_expect "llama-3.1-8b-instruct"

echo
echo "== CODE =="
curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva soma(n1,n2) com docstring."}],"budget":"low","prefer_code":true}' \
| tee /tmp/out.json | jq_expect "deepseek-coder-v2-16b"

curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique e corrija: ValueError: invalid literal for int(). Inclua teste."}],"budget":"low","prefer_code":true}' \
| tee /tmp/out.json | jq_expect "deepseek-coder-v2-16b"

curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"#task:refactor\nRefatore para separar I/O e lógica e cubra com pytest:\n```python\nimport sys\nx=sys.stdin.read()\nprint(sum(int(t) for t in x.split()))\n```"}],"budget":"balanced","prefer_code":true}' \
| tee /tmp/out.json | jq_expect "deepseek-coder-v2-16b"

echo
echo "== MISTO =="
curl -fsS "$API/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique debounce e depois mostre 1 exemplo JS curto."}],"budget":"low"}' \
| jq -r '.model_id' | sed 's/^/[INFO routed-> /;s/$/]/'

echo "[DONE]"
