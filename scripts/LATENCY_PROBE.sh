#!/usr/bin/env bash
set -euo pipefail

# Measures local router latency and compares to SLA (ms)
BASE="${BASE:-http://localhost:8082}"
SLA_MS="${SLA_MS:-6000}"

payload='{"messages":[{"role":"user","content":"PING"}]}'
tmp_out="$(mktemp)"

# curl time_total in seconds (float)
secs=$(curl -sS -o "$tmp_out" -w '%{time_total}' -H 'content-type: application/json' -d "$payload" "$BASE/route" || echo 0)
rm -f "$tmp_out" >/dev/null 2>&1 || true

# convert to ms (rounded)
ms=$(awk -v s="$secs" 'BEGIN{printf "%.0f", s*1000}')
ok=false; if [ "$ms" -lt "$SLA_MS" ]; then ok=true; fi

printf '{"local_ms":%s,"sla_ms":%s,"ok":%s}\n' "$ms" "$SLA_MS" "$ok"

