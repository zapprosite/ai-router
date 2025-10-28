Melhorias Planejadas — AI Router

Status: rascunho consolidado para execução futura (não aplicado ainda).

1) .gitignore & higiene de repo
- Normalizar e deduplicar padrões (feito nesta revisão).
- Ignorar diretórios de agentes e debugging: `.codex/`, `.continue/`, `.mcp-debug-tools/`.
- Ignorar caches e artefatos: `.cache/`, `.reports/`, `*.log`, `*.tmp`, `repo_tree.txt`, `k6_out/`.
- Segredos: `config/.env.*` ignorado com exceção `!config/.env.example`.

2) Segredos e exemplos
- Atualizar `config/.env.example` para refletir chaves e toggles reais: `ENABLE_OPENAI_FALLBACK`, `OPENAI_API_KEY_TIER2`, `OPENAI_BASE_URL`, `OPENAI_REASONING_EFFORT`, `OPENAI_TIMEOUT_SEC`, `OPENAI_MAX_RETRIES`, além de `OLLAMA_BASE_URL` e parâmetros seguros.

3) Contrato de API
- Documentar contrato completo do `/route` (request/response, campos de `usage`, erros 5xx) em `docs/FRONTEND_INTEGRATION.md` e resumo no `README.md`.
- Esclarecer `model_id` interno vs `usage.resolved_model_id` e relação com nomes do provider (ex.: `gpt-5-high` → `gpt-5`).

4) Arquitetura & roteamento
- Adicionar diagrama Mermaid ao `docs/ARCHITECTURE.md` (heurística, SLA, fallback) e tabela explicando thresholds/budgets (de `config/router_config.yaml`).
- Documentar log de evento `route_done` (latência e modelo resolvido) como observabilidade mínima.

5) EVALS e CI
- `docs/EVALS.md`: detalhar `make evals` (scripts/EVALS_RUN.sh), interpretação PASS/FAIL e troubleshooting com fallback ON.
- CI: adicionar `tests/k6_models.js` (básico) ou ajustar workflows para não depender do arquivo ausente.

6) Operação & DX
- `README.md`: TOC curto; “Rodar com Docker Compose” como opcional; Troubleshooting mais direto; apontar `panel-json`/`panel-refresh` quando help do Makefile mudar.
- `docs/guide.md`: reforçar sincronização do painel e comportamento dos botões (copiam apenas o comando).

7) Itens futuros
- Unit tests da heurística (`tests/test_router_logic.py` com mocks de latência).
- OpenAPI/Swagger (aproveitar o `/docs` do FastAPI com exemplos) sem alterar endpoints.
- SECURITY.md/CONTRIBUTING.md enxutos apontando guard-rails e fluxo de verificação.

