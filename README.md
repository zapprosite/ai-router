# AI Router — Local-first com fallback Tier‑2 (LangChain 1.0 + LangGraph 1.0 + Ollama)

Roteador de prompts simples, eficiente e econômico. Prioriza modelos locais (Ollama) e só escala para nuvem (OpenAI, Tier‑2) quando o SLA exigir.

Fluxo (alto nível)

```
 Cliente → FastAPI (8082) → Router (LCEL/RunnableBranch)
                    ├─ Código/traceback/prefer_code → DeepSeek Coder v2 (16B, Ollama)
                    └─ Texto curto/explicação       → Llama 3.1 Instruct (8B, Ollama)
                       ↘ (opcional) Fallback → OpenAI (gpt‑5‑nano/mini/codex/gpt‑5)
```

- Local: `llama3.1:8b-instruct` (explicações/curto) e `deepseek-coder-v2:16b` (código).
- Fallback: `gpt-5-nano`, `gpt-5-mini`, `gpt-5-codex` (Responses API) e `gpt-5` (high).
- Portas: serviço `8082` (systemd), dev `8083` (`make run-dev`).

Links rápidos
- Painel: abra `http://localhost:8082/guide` (botões copiam somente o comando; Terminal embutido).
- Modelos (compat OpenAI): `GET http://localhost:8082/v1/models`.
- Saúde: `GET/HEAD http://localhost:8082/healthz`.

## Quickstart (3 passos)

1) Ambiente Python (PEP 668 → use venv) e deps
```bash
cd /srv/projects/ai-router
make venv
```

2) Variáveis locais (.env.local) e sessão
```bash
# crie/edite config/.env.local (veja docs/SECRETS_STANDARD.md)
. .venv/bin/activate && set -a; . config/.env.local; set +a
# opcional: make env (confirma leitura do arquivo)
make env
```

3) Reiniciar serviço e validar saúde
```bash
make restart
curl -fsS http://localhost:8082/healthz && echo OK
# depois, abra o painel: http://localhost:8082/guide
```

## Comandos principais (Makefile)

- `make venv` cria venv e instala `requirements.txt`.
- `make env` carrega variáveis do `config/.env.local` (confirmação).
- `make run` sobe FastAPI no foreground em `8082` (conflita com systemd).
- `make run-dev` sobe FastAPI com `--reload` em `8083` (desliga o service antes).
- `make status | restart | logs | warm` operações do serviço (systemd) e aquecimento.
- `make smoke` executa smoke (texto + código) via `/route`.
- `make test-nano | test-mini | test-codex | test-high` exercitam matriz OpenAI (requer fallback ON + chave válida).
- `make local-llama | local-deepseek` testam os modelos locais.
- `make cloud-status | cloud-on | cloud-off` alternam fallback sem reescrever a chave.
- `make backup-all | restore-ollama` backup/restauração (inclui blobs do Ollama).
- `make panel-json | panel-refresh` sincroniza o JSON do painel `/public/guide_cmds.json`.
 - `make guide-open` abre o painel no navegador (fallback: acesse http://localhost:8082/guide).

## Roteamento (resumo)

- Heurística (LangChain 1.0 / LCEL `RunnableBranch`):
  - Sinal de código (def/class/import/traceback/```…``` ou `prefer_code=true`) → DeepSeek 16B.
  - Caso contrário (texto curto/explicativo) → Llama 8B Instruct.
- Fallback (Tier‑2) só se `ENABLE_OPENAI_FALLBACK=1` e houver violação do SLA (`TIER2_LATENCY_THRESHOLD_SEC=6`) ou falha local.

## Endpoints

- `GET/HEAD /healthz` → `{ "ok": true }`.
- `GET /debug/where` → caminhos de config, módulos e env ativos.
- `GET /v1/models` → lista de modelos registrados (compat OpenAI).
- `POST /route` → roteamento inteligente; resposta inclui `model_id` e `usage.resolved_model_name`.
- `GET /guide` e `GET /` → painel; raiz redireciona para `/guide` (302).

## Como rodar testes

- E2E/Smokes: `make smoke`.
- Evals: `make evals` (esperado PASS nos 3 casos de ouro).
- Matriz de modelos: `scripts/TEST_MODELS.py | python3 -m json.tool` (requer cloud ON para gpt‑5*).
- Pytests locais (se aplicável):
```bash
export PYTHONPATH=$PWD
pytest -q -k "not e2e"
```

## Troubleshooting (essencial)

- Porta 8082 ocupada: `make free-8082` (mata processos e libera a porta).
- Status/logs do serviço: `make status` e `make logs`.
- Reinício rápido e validação: `make restart` e `curl -fsS /healthz`.
- Recuperação segura (mata cargas, reinicia Ollama+router e valida): `scripts/RECOVER_SAFE.sh`.
- Painel desatualizado: `make panel-json && make panel-refresh`.
- Fallback quer gastar? Verifique: `make cloud-status`; ligue/desligue com `make cloud-on/off`.

## Segurança de segredos (padrões)

- Segredos ficam em `config/.env.local` e não devem ser commitados. O repositório já ignora `config/.env.local`, `.venv/` e artefatos.
- Ollama não requer chave local; apenas o daemon em `http://localhost:11434`.
- OpenAI (fallback opcional): defina `OPENAI_API_KEY_TIER2` e `ENABLE_OPENAI_FALLBACK=1` quando desejar usar.
- `OPENAI_REASONING_EFFORT∈{low,medium,high}` só se aplica a `gpt-5`. Nunca envie `reasoning_effort` para nano/mini/codex (já implementado).

## Documentação relacionada

- `docs/ARCHITECTURE.md` — componentes e fluxos.
- `docs/LOCAL_USAGE.md` — ambiente, run-dev, systemd, logs, health.
- `docs/EVALS.md` — smoke + evals e interpretação.
- `docs/FRONTEND_INTEGRATION.md` — exemplos de payloads e endpoints.
- `docs/SECRETS_STANDARD.md` — padrões de segredos e toggles cloud.
- `docs/AGENTS.md` — diretrizes para agentes/automação.
- `docs/guide.md` — como usar e sincronizar o painel `/guide`.
- `docs/guia_de_test.md` — roteiro de testes, stress e recuperação.
- `docs/CONTINUE.md` — Continue.dev + router-auto (OpenAI shim + MCP) Quickstart.

## Backup & Restore

- Backup completo: `make backup-all` (projeto, lock, `.env.local` com 600, blobs do Ollama).
- Backup leve para Desktop (sem segredos; Ollama como manifests): `scripts/BACKUP_DESKTOP.sh`.
- Restore Ollama: `make restore-ollama` (instruções de extração + restart ollama).
