# agents.md — Regras do MCP Task Master
Data: 21/10/2025

## Classificação JSON
{"task_type":"code|docs","complexity":"low|medium|high","needs_tools":false}

## Rotas disponiveis p/ smoke (hoje)
- GET /healthz
- GET /v1/models
(Não chamar /v1/responses nem /v1/chat/completions até implementação.)

## Contrato de saída
- code: blocos `sudo tee` + verificação por curl nos endpoints acima.
- docs: markdown claro e sucinto.

## Playbook CI Smoke Debug

- Checklist
  - Triggers: `workflow_dispatch`, `push` em `main`, `pull_request`.
  - Compose up: `docker compose -f docker-compose.yml up -d --build ai-router` com readiness de `/healthz`.
  - Validações HTTP: `GET /healthz` e `GET /v1/models` com saída válida.
  - k6 summary: executar testes com `--summary-export` para JSON de métricas.
  - Upload de artifacts sempre: `actions/upload-artifact@v4` com `if: always()`, `if-no-files-found: warn`, `retention-days` definido.
  - Gate p95 após upload: extrair `p(95)` e falhar quando `p95_ms >= 1200`, posicionado depois do upload.
  - Teardown: `docker compose -f docker-compose.yml down -v` sob `if: always()`.

- MCPs a usar
  - github: `get_file_contents`, `create_branch`, `create_or_update_file`, `create_pull_request`, `get_pull_request_status`.
  - ripgrep: varredura de termos no repositório (e.g., `workflow_dispatch`, `upload-artifact`, `p(95)`, `docker compose`).
  - playwright: navegar no run do Actions, capturar “Artifacts” e confirmar “smoke-artifacts”.
  - task_master_ai: criar/atualizar backlog, definir próxima ação e acompanhar execução.
