#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8082}"
CONCURRENCY="${CONCURRENCY:-4}"   # quantas requisições simultâneas
ROUNDS="${ROUNDS:-24}"            # quantas requisições no total
DELAY_SEC="${DELAY_SEC:-0.20}"    # pequeno espaçamento entre disparos
LOG="/tmp/ai_show_$(date +%Y%m%d-%H%M%S).ndjson"

# Cloud off (garante custo zero nesta sessão)
export ENABLE_OPENAI_FALLBACK=0
unset OPENAI_API_KEY OPENAI_API_KEY_TIER2

# prompts de TEXTO (Llama) e CÓDIGO (DeepSeek)
TEXT_PROMPTS=(
  "Explique HVAC em 1 frase."
  "Resuma: como dimensionar dutos (Darcy–Weisbach) em 3 passos."
  "Liste 5 erros comuns em instalações de HVAC."
  "Explique COP e EER rapidamente."
  "Como equilibrar fluxo de ar por ambiente? Resposta curta."
  "Diga 3 boas práticas de manutenção preventiva em HVAC."
)
CODE_PROMPTS=(
  "Escreva uma função Python soma(n1,n2) com docstring."
  "Implemente um CLI Python que lê JSON de stdin e imprime só as chaves."
  "Escreva um parser de logs (regex) com testes unitários mínimos (pytest)."
  "Crie uma classe Python CacheLRU<K,V> simples, com docstring e exemplo."
  "Escreva SQL p/ criar tabela leituras_hvac(id, ts, temp, umid)."
  "Dê um snippet Python que chama requests.get('https://example.com') com timeout e trata exceções."
)

# confere que a API está viva
if ! curl -fsS "$BASE/healthz" >/dev/null; then
  echo "ERRO: $BASE/healthz indisponível"; exit 1
fi

echo "== SHOWCASE START =="
echo "# NDJSON -> $LOG"
touch "$LOG"

# função que dispara e imprime: corpo JSON -> request /route
req() {
  local body="$1"
  local when="$(date -Is)"
  local resp http
  resp="$(curl -sS -H 'content-type: application/json' -d "$body" -w '\nHTTP_CODE:%{http_code}' "$BASE/route")" || {
    echo "[$(date +%H:%M:%S)] ERRO curl" >&2; return
  }
  http="${resp##*HTTP_CODE:}"
  json="${resp%HTTP_CODE:*}"
  # guarda NDJSON (anexa timestamp e http)
  echo "$json" | jq --arg ts "$when" --arg http "$http" '. + {ts:$ts,http:$http}' >> "$LOG"
  # imprime resumo bonito de uma linha
  echo "$json" | jq -r '
    . as $r |
    [
      (.model_id // "unknown"),
      ((.usage.latency_ms_router|tostring)+"ms"),
      (( ($r.output|tostring)|length )|tostring + "ch"),
      (if .prefer_code then "code" else "text" end)
    ] | @tsv' \
  | awk -v t="$(date +%H:%M:%S)" 'BEGIN{FS="\t"}{printf("[%s] %-24s | %7s | %6s | %s\n",t,$1,$2,$3,$4)}'
}

# gerador de requisições alternando TEXTO/CÓDIGO
i=0
while [ "$i" -lt "$ROUNDS" ]; do
  # controla paralelismo simples
  while [ "$(jobs -rp | wc -l)" -ge "$CONCURRENCY" ]; do wait -n; done

  if (( i % 2 == 0 )); then
    # TEXTO (vai para Llama local)
    p="${TEXT_PROMPTS[$((i % ${#TEXT_PROMPTS[@]}))]}"
    body="$(jq -cn --arg p "$p" '{messages:[{role:"user",content:$p}] }')"
  else
    # CÓDIGO (vai para DeepSeek local)
    p="${CODE_PROMPTS[$((i % ${#CODE_PROMPTS[@]}))]}"
    body="$(jq -cn --arg p "$p" '{messages:[{role:"user",content:$p}], prefer_code:true }')"
  fi

  req "$body" &
  i=$((i+1))
  sleep "$DELAY_SEC"
done

# aguarda todas as pendências
wait
echo "== SHOWCASE DONE =="
echo "# arquivo NDJSON: $LOG"
