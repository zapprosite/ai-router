# Arquitetura

Componentes principais e fluxo de decisão. Minimalista, porém robusto.

## Componentes

- `app/` (FastAPI)
  - `GET/HEAD /healthz` — saúde do serviço.
  - `GET /debug/where` — módulos carregados, env ativo e caminhos.
  - `GET /v1/models` — compat OpenAI; IDs do registro de modelos.
  - `POST /route` — roteamento inteligente (Llama ↔ DeepSeek ↔ OpenAI fallback).
- `graph/router.py` — regras LCEL (`RunnableBranch`) em LangChain 1.0/LangGraph 1.0.
- `providers/`
  - `ollama_client.py` — cliente local (ChatOllama, `/api/chat`).
  - `openai_client.py` — fallback Tier‑2 (gpt‑5‑nano/mini/codex/gpt‑5).
- `config/`
  - `.env.local` — variáveis de ambiente (NÃO versionar).
  - `router_config.yaml` — registro de modelos (IDs e nomes reais).
  - `router_policy.yaml` — política de roteamento (heurísticas/SLA).
- `public/Guide.html` — painel web em `/guide` (auto‑sync com `/public/guide_cmds.json`).

Portas
- Produção (systemd): `8082`.
- Desenvolvimento (`make run-dev`): `8083` (sem conflitar com 8082).

## Fluxo (alto nível)

```
Cliente → FastAPI (8082) → Router (LCEL/RunnableBranch)
                  ├─ Código/traceback/prefer_code → DeepSeek Coder v2 (16B, Ollama)
                  └─ Texto curto/explicação       → Llama 3.1 Instruct (8B, Ollama)
                     ↘ (opcional) Fallback → OpenAI (gpt‑5‑nano/mini/codex/gpt‑5)
```

Pré‑requisitos: Ollama em `http://localhost:11434` com os modelos já baixados (`ollama pull`).

## Árvore de decisão (resumo)

```
if prefer_code == true
  → DeepSeek 16B (local)
else if detecta padrões de código (def/class/import/traceback/```…```)
  → DeepSeek 16B (local)
else
  → Llama 8B Instruct (local)

se ENABLE_OPENAI_FALLBACK=1 e (violou SLA TIER2_LATENCY_THRESHOLD_SEC ou houve falha local)
  → escalar para OpenAI (gpt‑5‑mini/nano/codex/gpt‑5 conforme tipo)
```

Observações
- O roteamento é local‑first por padrão; a nuvem é estritamente fallback.
- O painel (`/guide`) permite smokes e testes rápidos sem alterar a lógica.
- Não altere portas, unidades systemd, docker ou segredos via documentação.
