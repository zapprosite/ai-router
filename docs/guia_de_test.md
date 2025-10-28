# Guia de Teste — AI Router 2025 (Local‑first + Tier‑2 Fallback)

Objetivo
- Validar ponta a ponta: FastAPI, roteamento LCEL/LangGraph, modelos locais (Ollama) e matriz OpenAI.
- Cobrir testes rápidos (smoke/evals), stress moderado, showcase e recuperação/backup.
- Custo cloud: mantenha fallback desligado quando quiser gastar zero.

---

## 0) Pré‑requisitos e ambiente

```bash
cd /srv/projects/ai-router
. .venv/bin/activate && set -a; . config/.env.local; set +a

# (opcional) desativar cloud (custo zero)
export ENABLE_OPENAI_FALLBACK=0
unset OPENAI_API_KEY OPENAI_API_KEY_TIER2
```

Critérios gerais de PASS
- `/healthz` retorna `{"ok":true}`.
- Latência local (LLM) < 3–5s em prompts curtos com modelos quantizados.
- Fallback não dispara com `ENABLE_OPENAI_FALLBACK=0`.

## 1) Saúde e descoberta

Healthcheck
```bash
curl -fsS http://localhost:8082/healthz && echo "PASS: healthz"
```

Descoberta de módulos e config
```bash
curl -fsS http://localhost:8082/debug/where | jq '{ok,config_path,modules,env_models}'
# PASS: ok=true, config_path aponta para config/router_config.yaml
```

Lista de modelos (compat OpenAI)
```bash
curl -fsS http://localhost:8082/v1/models | jq '.data[].id'
# PASS: contém llama-3.1-8b-instruct, deepseek-coder-v2-16b, gpt-5-*
```

## 2) Roteador (heurística + SLA)

Texto curto → Llama local
```bash
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' \
  | jq '{model_id,usage}'
# PASS: model_id = "llama-3.1-8b-instruct"
```

Código (prefer_code=true) → DeepSeek local
```bash
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}' \
  | jq '{model_id,usage}'
# PASS: model_id = "deepseek-coder-v2-16b"
```

SLA/fallback
- Com `ENABLE_OPENAI_FALLBACK=1` e latência local > `TIER2_LATENCY_THRESHOLD_SEC` (padrão 6s), deve escalar para gpt‑5‑mini/nano (texto) ou gpt‑5‑codex/mini (código).

## 3) Painel Web (UI)

Abra: `http://localhost:8082/guide`

- Use os botões: `/debug/where`, `/v1/models`, Texto curto, Código.
- Terminal (rodapé): os botões numerados copiam apenas o comando.
- PASS: “Comando copiado ✓”.

## 4) Testes de modelos (matriz)

```bash
scripts/TEST_MODELS.py | python3 -m json.tool
# PASS: cada item {model, ok:true, preview:...}
```

Confirma `gpt-5-nano`, `gpt-5-mini`, `gpt-5-codex`, `gpt-5` quando fallback estiver ligado e a chave válida.

## 5) Showcase (vídeo, GPU ON)

Carga leve e NDJSON
```bash
export CONCURRENCY=4 ROUNDS=20 DELAY_SEC=0.15
/srv/projects/ai-router/scripts/SHOWCASE_LOCAL.sh
# gera /tmp/ai_show_*.ndjson
```

Saídas esperadas (exemplos)
```
[21:05:12] llama-3.1-8b-instruct   |   1150ms |   142ch | text
[21:05:12] deepseek-coder-v2-16b   |   1840ms |   512ch | code
```

Monitorar GPU em paralelo
```bash
watch -n 1 'nvidia-smi --query-gpu=name,utilization.gpu,utilization.memory,memory.total,memory.used --format=csv,noheader'
```

## 6) Stress controlado (custo zero cloud)

Garantir local‑only
```bash
. /srv/projects/ai-router/scripts/STRESS_SAFE_ENV.sh
```

Stress paralelo moderado (router)
```bash
/srv/projects/ai-router/scripts/STRESS_LOCAL.sh
# PASS: finaliza com fails=0 (ou baixo). Ajuste ranges no script conforme necessário.
```

Stress por modelo (direto)
```bash
/srv/projects/ai-router/scripts/STRESS_MATRIX.sh
# PASS: ok e model correto para Llama/DeepSeek.
```

## 7) Recuperação rápida

```bash
/srv/projects/ai-router/scripts/RECOVER_SAFE.sh
curl -fsS http://localhost:8082/healthz && echo "router OK"
# PASS: router OK ao fim.
```

## 8) Systemd e warm‑up

Service ativo
```bash
systemctl status ai-router --no-pager
curl -fsS http://localhost:8082/healthz && echo OK
```

Timer de warm‑up
```bash
systemctl list-timers | grep ai-router-warm || true
sudo systemctl start ai-router-warm.service
# PASS: timer listado; oneshot executa sem erro.
```

## 9) Backup (leve e completo)

Backup leve para Desktop (sem segredos, sem quantizados)
```bash
/srv/projects/ai-router/scripts/BACKUP_DESKTOP.sh
# Cria ~/Desktop/AI-Router-Backup-<STAMP> com:
# - ai-router/ (sem config/.env.local)
# - requirements.lock.txt
# - ollama/*.Modelfile (manifests sem pesos)
```

Backup completo (inclui blobs do Ollama)
```bash
make backup-all
# ou
 # /srv/backups/ai-router/<STAMP>:
 # project.tgz, requirements.lock.txt, .env.local (600), ollama-models.tgz
```

## 10) Testes recomendados (futuros)

Heurística unitária mínima
- curto → Llama (sem fallback)
- prefer_code=true → DeepSeek
- SLA>6s com fallback ON → escala para gpt‑5‑mini/gpt‑5‑codex

Como: `tests/test_router_logic.py` com mocks de latência.

OpenAI codex (Responses API)
- Verificar que `gpt-5-codex` retorna texto sem erro.
- Como: `make test-codex`.

Painel `/guide`
- Verificar que cada botão numerado copia somente o comando (sem `#`).
- Como: inspeção manual + colar no shell.

## 11) Dicas de operação

Cloud barato/ON para fallback real
```bash
export ENABLE_OPENAI_FALLBACK=1
export OPENAI_API_KEY_TIER2=sk-...
```

Reset da UI após editar `public/Guide.html`
```bash
sudo systemctl restart ai-router
# No navegador: Ctrl+F5
```

Apêndice — Comandos úteis
```bash
make help
```
make restart      # reinicia FastAPI e testa /healthz
make smoke        # 2 chamadas (texto+código) via router
make test-nano    # testa gpt-5-nano
make test-mini    # testa gpt-5-mini
make test-codex   # testa gpt-5-codex (Responses)
make test-high    # testa gpt-5
make local-llama  # testa Llama local
make local-deepseek # testa DeepSeek local
make backup-all   # backup completo (inclui modelos)
— Fim.
