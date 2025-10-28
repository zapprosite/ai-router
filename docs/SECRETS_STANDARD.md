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
