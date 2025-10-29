Padrões de Segredos

- Não comitar segredos. O repositório já ignora `config/.env.local`, `.venv/` e artefatos.
- `config/.env.local` contém variáveis de ambiente locais (PEP 668: use venv isolado).

Ollama (local)
- Não requer chave. Apenas o daemon em `http://localhost:11434` e os modelos instalados (`ollama pull`).

OpenAI (fallback opcional)
- `ENABLE_OPENAI_FALLBACK=0|1` — 0 desliga (custo zero), 1 liga fallback.
- `OPENAI_API_KEY_TIER2=...` — chave usada quando o fallback está ligado.
- `OPENAI_BASE_URL=...` — opcional, se usar proxy.
- `OPENAI_REASONING_EFFORT=low|medium|high` — somente para `gpt-5`.
  - Enviar `reasoning_effort` APENAS quando o modelo for exatamente `gpt-5` e o valor pertencer a `{low, medium, high}`.
  - Nunca enviar `reasoning_effort` para nano/mini/codex (já tratado no provider).

Alternar fallback de forma segura (sem reescrever a chave)
```bash
make cloud-status
make cloud-on
make cloud-off
```

Exemplo de arquivo (`config/.env.local`)

> Dica: existe suporte no `.gitignore` para versionar somente `config/.env.example`. Mantenha o seu `.env.local` fora do git.

```dotenv
# --- Core ---
CORS_ALLOW_ORIGINS=*

# --- Ollama ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.1

# --- OpenAI (fallback opcional) ---
ENABLE_OPENAI_FALLBACK=0
OPENAI_API_KEY_TIER2=
OPENAI_BASE_URL=
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_RETRIES=2
OPENAI_TIMEOUT_SEC=20
OPENAI_REASONING_EFFORT=
OPENAI_ORGANIZATION=
OPENAI_PROJECT=

# --- Router ---
ROUTER_CONFIG=config/router_config.yaml
```

Checklist rápido
- Carregar variáveis: `. .venv/bin/activate && set -a; . config/.env.local; set +a`
- Verificar leitura: `make env`
- Validar saúde: `curl -fsS http://localhost:8082/healthz && echo OK`
- Listar modelos: `curl -fsS http://localhost:8082/v1/models | jq` (deve conter `router-auto`)
