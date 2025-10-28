# Guard-Rails para alterações automatizadas (Codex CLI)

## Leitura obrigatória
Leia antes de editar:
- README.md
- docs/ARCHITECTURE.md
- docs/LOCAL_USAGE.md
- docs/EVALS.md
- docs/FRONTEND_INTEGRATION.md
- docs/SECRETS_STANDARD.md
- docs/AGENTS.md
- docs/PRD_TASK_MASTER.md (quando presente)

## Zonas proibidas
- Não alterar portas, systemd, segredos ou docker.
- Não reintroduzir Qwen.
- Não remover HEAD/GET /healthz e /guide, nem GET / → 302 /guide.
- Makefile: receitas com TAB real, sem CRLF.

## OpenAI (Tier-2)
- `reasoning_effort` apenas para `gpt-5` e apenas se `OPENAI_REASONING_EFFORT ∈ {low,medium,high}`.
- Jamais enviar `reasoning_effort` para nano/mini/codex.
- Codex via Responses API, extração tolerante.

## Fluxo de verificação
- `make restart` e `curl /healthz`
- `make smoke` e `make evals` (esperado: PASS)
- Detector de TABs no Makefile (sem “missing separator”)
- Se mexer no help do Makefile: `make panel-refresh`.

## Painel
- Guide.html mantém visual/originalidade.
- Botões numerados copiam somente o comando (data-cmd).
- Produção na 8082 (systemd), dev 8083 (run-dev).

## Commits
- Mensagens claras. Não comitar segredos.
- `.gitignore` mantém `config/.env.local`, `.venv/` e artefatos fora do repositório.
