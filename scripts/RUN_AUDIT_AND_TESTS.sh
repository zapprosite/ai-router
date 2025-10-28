#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8082}"

echo "== Audit: endpoints =="
code_h=$(curl -fsS -o /dev/null -w '%{http_code}' "$BASE/healthz" || echo 000)
code_g=$(curl -fsS -o /dev/null -w '%{http_code}' "$BASE/guide" || echo 000)
code_r=$(curl -fsS -I -o /dev/null -w '%{http_code}' "$BASE/" || echo 000)
echo "healthz: $code_h, guide: $code_g, root: $code_r"

echo "== Smoke =="
set +e
./scripts/SMOKE_NOW.sh
smoke_rc=$?
set -e
echo "smoke_rc=$smoke_rc"

echo "== Evals =="
set +e
pass=0; fail=0
out=$(./scripts/EVALS_RUN.sh 2>&1)
rc=$?
echo "$out" | tail -n 50
if echo "$out" | grep -q 'PASS='; then
  pass=$(echo "$out" | awk -F'[ =]' '/PASS=/{print $2}' | tail -n1)
  fail=$(echo "$out" | awk -F'[ =]' '/FAIL=/{print $2}' | tail -n1)
fi
set -e

echo "== Latency Probe =="
probe=$(./scripts/LATENCY_PROBE.sh || echo '{"local_ms":-1,"sla_ms":6000,"ok":false}')
echo "$probe"

jq -cn --arg ch "$code_h" --arg cg "$code_g" --arg cr "$code_r" \
  --argjson pass "${pass:-0}" --argjson fail "${fail:-0}" \
  --argjson probe "$probe" '{
    smoke:{},
    endpoints:{healthz: ($ch|tonumber), guide: ($cg|tonumber), root: ($cr|tonumber)},
    evals:{pass: $pass, fail: $fail},
    latency_probe: $probe
  }'

