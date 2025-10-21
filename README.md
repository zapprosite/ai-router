# Task Master MCP — Repositório mínimo (MCP-first)

Documentos únicos:
- **README.md** — visão geral e uso.
- **AGENTS.md** — contrato do codex CLI (roteamento, MCP, saída).
- **PRD_TASK_MASTER.md** — PRD completo (inclui Fases 1–60).

## Uso com codex CLI (MCP)
1) `codex mcp list` deve mostrar filesystem, github, task_master_ai, etc.
2) **Início**: `codex ask "start"` → o agente lê `PRD_TASK_MASTER.md`, `AGENTS.md`, `README.md` via MCP filesystem e responde `CONTEXT_READY`.
3) **Depois**: peça tarefas objetivas.
   - Ex.: `codex ask "Gerar script k6 500 RPS para /v1/tasks com assert p95<300ms"`
   - Ex.: `codex ask "YAML de automação: PR opened → criar tarefa com tags github, pr"`

### Rotas do Router (Smoke)
- `GET /healthz` → `{"ok": true}`
- `GET /v1/models` → lista de modelos locais/cloud quando disponíveis

### Segurança e segredos
- Somente via `/srv2/secrets/ai-stack/ai-stack.env`. Não exibir nem logar.
# ai-router

## Governança de caminhos
- **Canônico**: `/srv/projects/ai-router` (única fonte de verdade).
- **Compatibilidade MCP**: o servidor `filesystem` enxerga `/home/will`. Expomos o repositório via **bind**:
  - `sudo /usr/local/bin/mcp_bind_repo.sh` cria/garante `/home/will/ai-router -> /srv/projects/ai-router`.
- **Regras**:
  - Comandos de Docker/CI/dev usam **/srv**.
  - O **codex CLI** (MCP filesystem) referencia **/home/will/ai-router**.
  - Não manter cópias; o bind reflete o conteúdo de **/srv**.
