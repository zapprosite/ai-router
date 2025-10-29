# Changelog

## v0.2.0 — 2025-10-28
- Shim **/v1/chat/completions** mapeando para **/route** e refletindo `usage.resolved_model_id`.
- Modelo lógico único **router-auto** para Continue (manual-only).
- **Validator + CI (lychee)** para `.continue/config.yaml` e docs.
- **Docs**: `docs/CONTINUE.md`, integrações no `docs/FRONTEND_INTEGRATION.md`.
- **Tests/Make**: `make test-continue` (venv+PYTHONPATH) e `kill-8082` opcional.
