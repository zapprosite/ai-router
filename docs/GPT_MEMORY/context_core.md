# Contexto Core — AI Router (LangChain 1.x + LangGraph 1.0)
**Portas**  
- Serviço (systemd): **8082** → `/healthz`, `/route`, `/v1/models`, `/guide`  
- Dev (reload): **8083** (via `make run-dev`)

**Stack**
- LangChain **1.0.x**, LangGraph **1.0.x**, LCEL (`RunnableBranch`)
- FastAPI **0.120.x**, Uvicorn **0.38.x**
- Local (Ollama): `llama3.1:8b-instruct-q5_K_M` (explicação/curto), `deepseek-coder-v2:16b` (código)
- Cloud Tier-2 (fallback, opcional): `gpt-5-nano`, `gpt-5-mini`, `gpt-5-codex` (Responses), `gpt-5` (high)
- SLA fallback: `TIER2_LATENCY_THRESHOLD_SEC=6`

**Regras de Roteamento (heurística)**
- Se detectar padrões de **código** (```/def/class/import/traceback/{}/;… ou `prefer_code=true`) → **DeepSeek 16B** (local)  
- Pedidos curtos/explicativos → **Llama 8B Instruct** (local)  
- Fallback cloud só se **ENABLE_OPENAI_FALLBACK=1** e **violou SLA** ou **falha local**

**Endpoints**
- `POST /route`  body: `{"messages":[{role,user,content}], "prefer_code": bool}`  
  resposta: inclui `model_id` escolhido e `usage.resolved_model_id`
- `GET /v1/models`  lista IDs configurados  
- `GET /healthz`  → `{"ok":true}` (HEAD também aceito)  
- `GET /guide`  painel HTML (HEAD também aceito)  
- `GET /` → redireciona para `/guide`

**Arquivos sensíveis (NÃO editar por agentes)**
- `config/.env.local`, units em `/etc/systemd/system/*.service`

**Comandos frequentes (Makefile)**
- `make status|restart|logs|warm|smoke`  
- `make run-dev` (8083, recarrega), `make stop`, `make free-8082`  
- Cloud: `make cloud-status|cloud-on|cloud-off`  
- Backup: `make backup-all`, `scripts/BACKUP_DESKTOP.sh`

**Decisões**
- Local-first para custo e latência; cloud apenas fallback
- Qwen **removido** do catálogo
