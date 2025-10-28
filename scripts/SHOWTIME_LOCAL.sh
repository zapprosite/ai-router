#!/usr/bin/env bash
set -euo pipefail
BASE="http://localhost:8082"

# Cloud OFF (somente sessão)
export ENABLE_OPENAI_FALLBACK=0
unset OPENAI_API_KEY OPENAI_API_KEY_TIER2

# Cores
cyan=$'\033[36m'; amber=$'\033[38;5;214m'; green=$'\033[32m'; dim=$'\033[2m'; reset=$'\033[0m'

# Arquivo de log
LOG="showtime.jsonl"; : > "$LOG"

short() {  # trunca texto pra caber na linha
  python3 - <<PY
import sys, textwrap, json
s = sys.stdin.read()
try:
  o = json.loads(s)
  out = {
    "model_id": o.get("model_id") or o.get("usage",{}).get("resolved_model_id"),
    "latency_ms_router": o.get("usage",{}).get("latency_ms_router"),
    "output": o.get("output","").replace("\n"," ")[:180]
  }
  print(json.dumps(out, ensure_ascii=False))
except Exception:
  print(s.strip()[:180])
PY
}

send_text() {
  local prompt="$1"
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d "$(jq -cn --arg t "$prompt" '{messages:[{role:"user",content:$t}]}')"
}

send_code() {
  local prompt="$1"
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d "$(jq -cn --arg t "$prompt" '{messages:[{role:"user",content:$t}], prefer_code:true}')"
}

banner() {
  echo -e "${amber}== ${1} ==${reset}"
}

banner "SHOWTIME • Local GPU • Llama (chat) + DeepSeek (código) • JSON em linha"
echo -e "${dim}Dica: log completo em ${LOG}${reset}"

# Prompts
CHAT_LONG="$(python3 - <<'PY'
print(("Explique, com exemplos práticos, fundamentos de HVAC, cálculo de carga térmica, "
       "dimensionamento de dutos (Darcy-Weisbach) e checklist de instalação. ")*8)
PY
)"
CODE_PROMPT="Implemente em Python uma função parse_nvidia_smi() que retorne dict; inclua docstring, validação e exemplo de uso rápido."

# Rodadas
ROUNDS=${ROUNDS:-12}
for i in $(seq 1 "$ROUNDS"); do
  if (( i % 2 == 1 )); then
    # Llama (texto)
    RAW=$(send_text "$CHAT_LONG") || RAW='{}'
    echo "$RAW" >> "$LOG"
    LINE=$(printf "%s\n" "$RAW" | short)
    mdl=$(echo "$LINE" | jq -r '.model_id // "?"' 2>/dev/null || echo "?")
    lat=$(echo "$LINE" | jq -r '.latency_ms_router // "?"' 2>/dev/null || echo "?")
    out=$(echo "$LINE" | jq -r '.output // ""' 2>/dev/null || echo "")
    echo -e "${cyan}[CHAT]${reset} model=${mdl} ${dim}lat=${lat}ms${reset} → ${out}"
  else
    # DeepSeek (código)
    RAW=$(send_code "$CODE_PROMPT") || RAW='{}'
    echo "$RAW" >> "$LOG"
    LINE=$(printf "%s\n" "$RAW" | short)
    mdl=$(echo "$LINE" | jq -r '.model_id // "?"' 2>/dev/null || echo "?")
    lat=$(echo "$LINE" | jq -r '.latency_ms_router // "?"' 2>/dev/null || echo "?")
    out=$(echo "$LINE" | jq -r '.output // ""' 2>/dev/null || echo "")
    echo -e "${green}[CODE]${reset} model=${mdl} ${dim}lat=${lat}ms${reset} → ${out}"
  fi
done

banner "FIM • Linhas completas em ${LOG}"
