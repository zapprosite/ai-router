#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://localhost:8082}

banner(){ printf "\n===== %s =====\n" "$*"; }
step(){ printf "[E2E] %s\n" "$*"; }

banner "E2E FULL — Router + Panel + Stress + Recovery"
date +'%F %T %Z'

step "1) Restart service + health"
make restart
curl -fsS "$BASE/healthz" | jq . || true

step "2) /guide reachable"
code=$(curl -fsS -o /dev/null -w '%{http_code}' "$BASE/guide")
echo "GET /guide -> $code"

step "3) Smoke"
make smoke

step "4) Stress (20x short + code)"
for i in $(seq 1 20); do
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Explique em 1 frase o item $i.\"}]}" >/dev/null || true
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Dá um snippet Python soma($i,2).\"}],\"prefer_code\":true}" >/dev/null || true
  printf "."
done; echo

if command -v nvidia-smi >/dev/null 2>&1; then
  step "GPU status"
  nvidia-smi || true
fi

step "Logs (last 50)"
journalctl -u ai-router -n 50 --no-pager || true

step "5) Recovery"
./scripts/RECOVER_SAFE.sh
curl -fsS "$BASE/healthz" | jq . || true

step "6) Evals"
make evals

step "7) /v1/models"
curl -fsS "$BASE/v1/models" | jq '.data[].id' || curl -fsS "$BASE/v1/models" || true

step "8) Backup (optional)"
make backup-all || true

banner "E2E DONE"
date +'%F %T %Z'
