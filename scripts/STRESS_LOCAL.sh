#!/usr/bin/env bash
set -euo pipefail
BASE="http://localhost:8082"
TEXT_LONG=$(python3 - <<'PY'
print("Explique em detalhes técnicas de HVAC, variáveis de projeto, balanceamento, cálculo de carga térmica, exemplos e fórmulas. " * 200)
PY
)

# 1) Smoke quente pra aquecer cache
curl -s "$BASE/route" -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Diga: WARM"}]}' >/dev/null || true

# 2) Lotes paralelos (8x texto longo no Llama + 4x código no DeepSeek)
run_text() {
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d "$(jq -cn --arg t "$TEXT_LONG" '{messages:[{role:"user",content:$t}] }')" >/dev/null
}
run_code() {
  curl -s "$BASE/route" -H 'content-type: application/json' \
    -d '{"messages":[{"role":"user","content":"Implemente um parser de logs (Python, robusto) com docstring e testes minimalistas."}],"prefer_code":true}' >/dev/null
}

echo "[STRESS] disparando 8x texto + 4x código (paralelo controlado)"
pids=()
for i in {1..8}; do run_text & pids+=($!); done
for i in {1..4}; do run_code & pids+=($!); done

# 3) Espera e sumariza
fail=0; for p in "${pids[@]}"; do wait "$p" || fail=$((fail+1)); done
echo "[STRESS] concluído. fails=$fail"
