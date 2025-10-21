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
