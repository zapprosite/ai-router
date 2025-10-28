#!/usr/bin/env bash
set -euo pipefail
ROOT="/srv/projects/ai-router"
DOCS="$ROOT/docs"
cd "$ROOT"

echo "[prune] Removendo docs supérfluos…"
rm -f "$DOCS/AGENTS.md" \
      "$DOCS/PRD_TASK_MASTER.md" \
      "$DOCS/GOVERNANCE.md" \
      "$DOCS/ai-stack.env.example" || true
[ -d "$DOCS/config" ] && rm -rf "$DOCS/config" || true

echo "[write] ARCHITECTURE.md (mínimo)"
cat > "$DOCS/ARCHITECTURE.md" <<'MD'
# Arquitetura (mínimo)

- **app/** FastAPI:
  - `GET /healthz`
  - `GET /debug/where`
  - `POST /route` → roteia para Llama (explicação) ou DeepSeek (código)
  - Compat OpenAI: `GET /v1/models`
- **graph/router.py**: regras LCEL (`RunnableBranch`) — *LangChain/LangGraph 1.0*.
- **providers/**:
  - `ollama_client.py`: `ChatOllama` (API nativa `/api/chat`)
  - `openai_client.py`: fallback opcional (GPT-5*).
- **config/**:
  - `.env.local` (ENV)
  - `router_config.yaml` (registry)
  - `router_policy.yaml` (policy de roteamento)

## Modelos (Ollama)
- **Chat/explicação**: `llama3.1:8b-instruct-q5_K_M`
- **Código**: `deepseek-coder-v2:16b`

> Requisitos: Ollama em `http://localhost:11434` e modelos `pull` feitos.
MD

echo "[write] LOCAL_USAGE.md"
cat > "$DOCS/LOCAL_USAGE.md" <<'MD'
# Uso local

## 1) Modelos (Ollama)
```bash
ollama pull llama3.1:8b-instruct-q5_K_M
ollama pull deepseek-coder-v2:16b
2) ENV básico (config/.env.local)
ini
￼Copiar código
# modelos
OLLAMA_INSTRUCT_MODEL=llama3.1:8b-instruct-q5_K_M
OLLAMA_CODER_MODEL=deepseek-coder-v2:16b

# tuning seguro
OLLAMA_NUM_CTX=4096
OLLAMA_TEMPERATURE=0.15
OLLAMA_TOP_P=0.9
OLLAMA_REPEAT_PENALTY=1.05
OLLAMA_NUM_PREDICT_CHAT=64
OLLAMA_NUM_PREDICT_CODE=640
OLLAMA_KEEP_ALIVE=30m
3) Subir API
bash
￼Copiar código
scripts/RUN_STRICT.sh
curl -fsS http://localhost:8082/healthz
4) Smokes
bash
￼Copiar código
# Chat curto → Llama
curl -sS http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}],"budget":"low"}' | jq

# Código → DeepSeek
curl -sS http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva soma(n1,n2) com docstring."}],"budget":"low","prefer_code":true}' | jq
5) Endpoints
GET /v1/models — compat OpenAI

POST /route — roteamento inteligente (LangChain 1.0)
MD

echo "[write] FRONTEND_INTEGRATION.md"
cat > "$DOCS/FRONTEND_INTEGRATION.md" <<'MD'

Integração Frontend
OpenAI compat — listar modelos
bash
￼Copiar código
GET http://localhost:8082/v1/models
Rota inteligente (recomendada)
bash
￼Copiar código
POST http://localhost:8082/route
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Explique HVAC em 1 frase."}],
  "budget": "low",
  "prefer_code": false
}
model_id resolvido dinamicamente:

Chat/explicação: llama-3.1-8b-instruct

Código: deepseek-coder-v2-16b
MD

echo "[write] SECRETS_STANDARD.md"
cat > "$DOCS/SECRETS_STANDARD.md" <<'MD'

Padrões de Segredos
Ollama não precisa de chave local, apenas o daemon ativo em http://localhost:11434.

OpenAI (fallback opcional):

OPENAI_API_KEY=...

OPENAI_BASE_URL (se proxy)

Variáveis do projeto estão em config/.env.local. Não comitar segredos.
MD

echo "[done] docs minimizados."
tree -a docs
