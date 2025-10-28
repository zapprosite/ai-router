#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://localhost:8082}
pass=0; fail=0

run_case(){ # name expected_model json_payload
  local name="$1" exp="$2" payload="$3"
  local out
  out=$(curl -sS -H 'content-type: application/json' -d "$payload" "$BASE/route" || true)
  local model=$(printf "%s" "$out" | jq -r '.model_id // .usage.resolved_model_id // "null"' 2>/dev/null || echo null)
  if [[ "$model" == "$exp" ]]; then
    echo "{\"case\":\"$name\",\"expected\":\"$exp\",\"got\":\"$model\",\"status\":\"PASS\"}"
    pass=$((pass+1))
  else
    echo "{\"case\":\"$name\",\"expected\":\"$exp\",\"got\":\"$model\",\"status\":\"FAIL\",\"raw\":$(
      printf "%s" "$out" | jq -c . 2>/dev/null || echo '"unparsable"'
    )}"
    fail=$((fail+1))
  fi
}

# 1) Texto curto → Llama
run_case "texto_curto_llama" "llama-3.1-8b-instruct" \
'{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}'

# 2) Código explícito → DeepSeek (prefer_code)
run_case "codigo_prefer_deepseek" "deepseek-coder-v2-16b" \
'{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}'

# 3) Ruído de código / traceback → DeepSeek
run_case "traceback_deepseek" "deepseek-coder-v2-16b" \
'{"messages":[{"role":"user","content":"Corrija o traceback: ValueError: x inválido; ```python\ndef foo(x):\n    return x*2\n```"}]}'

echo "---"
echo "PASS=$pass FAIL=$fail"
[[ $fail -eq 0 ]]
