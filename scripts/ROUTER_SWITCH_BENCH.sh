#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
API="${API:-http://localhost:8082}"
N="${N:-12}"

if ! curl -fsS "$API/healthz" >/dev/null 2>&1; then
  echo "[boot] starting API..."
  bash "$ROOT/scripts/RUN_STRICT.sh"
fi

bash "$ROOT/scripts/WARM_LOCAL.sh" >/dev/null || true

docs='{"messages":[{"role":"user","content":"Explique em 1 frase: o que é backpressure?"}],"budget":"low"}'
code='{"messages":[{"role":"user","content":"Implemente fizz_buzz(n) em Python com teste rápido."}],"budget":"low","prefer_code":true}'

lat() { jq -r '.usage.latency_ms // .latency_ms // 0'; }

sum_d=0; sum_c=0; cnt_d=0; cnt_c=0
for i in $(seq 1 $N); do
  out_d=$(curl -fsS "$API/route" -H 'content-type: application/json' -d "$docs")
  ld=$(echo "$out_d" | lat); md=$(echo "$out_d" | jq -r '.model_id')
  echo "[D$i] ${ld}ms ($md)"
  sum_d=$((sum_d+ld)); cnt_d=$((cnt_d+1))

  out_c=$(curl -fsS "$API/route" -H 'content-type: application/json' -d "$code")
  lc=$(echo "$out_c" | lat); mc=$(echo "$out_c" | jq -r '.model_id')
  echo "[C$i] ${lc}ms ($mc)"
  sum_c=$((sum_c+lc)); cnt_c=$((cnt_c+1))
done

avg_d=$((sum_d/cnt_d)); avg_c=$((sum_c/cnt_c))
echo "---"
echo "AVG docs: ${avg_d}ms"
echo "AVG code: ${avg_c}ms"
