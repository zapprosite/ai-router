#!/usr/bin/env bash
set -euo pipefail
BASE="http://localhost:8082"
PROMPT_TXT=$(python3 - <<'PY'
print("Escreva um ensaio técnico (1500+ palavras) sobre otimização de dutos HVAC, perdas de carga, equações de Darcy-Weisbach, e exemplifique. " * 20)
PY
)
PROMPT_CODE="Escreva um CLI Python robusto de parsing de nvidia-smi com saída JSON; inclua docstrings e exemplos."

models_local=("llama3.1:8b-instruct-q5_K_M" "deepseek-coder-v2:16b")

echo "[MATRIX] Textos longos → Llama | Código → DeepSeek"
curl -s "$BASE/actions/test" -H 'content-type: application/json' \
  -d "$(jq -cn --arg m "${models_local[0]}" --arg p "$PROMPT_TXT" '{model:$m, prompt:$p}')" | jq -r '.ok,.model' | sed -n '1,2p'

curl -s "$BASE/actions/test" -H 'content-type: application/json' \
  -d "$(jq -cn --arg m "${models_local[1]}" --arg p "$PROMPT_CODE" '{model:$m, prompt:$p}')" | jq -r '.ok,.model' | sed -n '1,2p'
