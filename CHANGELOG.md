# Changelog

## v0.2.1 — 2025-10-29
- Docs: DEV PRO polish — README com badges/TOC e ajuste de endpoints; `docs/ARCHITECTURE.md` com diagramas Mermaid (flowchart, decision, sequence); `docs/FRONTEND_INTEGRATION.md` com JSON Schemas de requisição/resposta, status e erro; `docs/SECRETS_STANDARD.md` com exemplo concreto de `config/.env.local` + checklist.
- Sem mudanças de API. Serviço estável; testes básicos passando.

## v0.2.0 — 2025-10-28
- Shim **/v1/chat/completions** mapeando para **/route** e refletindo `usage.resolved_model_id`.
- Modelo lógico único **router-auto** para Continue (manual-only).
- **Validator + CI (lychee)** para `.continue/config.yaml` e docs.
- **Docs**: `docs/CONTINUE.md`, integrações no `docs/FRONTEND_INTEGRATION.md`.
- **Tests/Make**: `make test-continue` (venv+PYTHONPATH) e `kill-8082` opcional.
