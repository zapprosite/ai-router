#!/usr/bin/env bash
set -euo pipefail
STATE="/srv-2/dev/ai-router-codex/state"
J="$STATE/journal.jsonl"; INF="$STATE/last.inflight"
[[ -s "$INF" && -s "$J" ]] || { echo "nada a retomar"; exit 0; }
STEP=$(cat "$INF")
CMD=$(tac "$J" | jq -r --arg s "$STEP" 'select(.step|tostring==$s) | .cmd' | head -n1)
[[ -n "$CMD" && "$CMD" != "null" ]] || { echo "passo não encontrado"; exit 1; }
echo "[resume] reexecutando: $CMD"
bash -lc "$CMD"
echo ok > "$STATE/last.ok"; rm -f "$INF"
