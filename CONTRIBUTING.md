# Contributing Guide

## 🛠️ Development Setup
## 🛠️ Development Setup
1. **Quick Start**:
    ```bash
    make venv
    source .venv/bin/activate
    ```

2. **Validate Setup**:
    ```bash
    make verify
    ```

## ✅ Verification
Before submitting changes, ALWAYS run the full verification suite:
```bash
make verify
```
This runs:
1. Service Health Check.
2. Linter (Ruff).
3. Unit Tests (`tests/unit`).
4. Integration Tests (`tests/integration`).
5. Chaos/Resilience Tests.

## ➕ Adding a New Model
1. Update `config/router_config.yaml`:
    ```yaml
    models:
      - id: new-model-id
        provider: ollama
        name: new-model
    ```
2. Update Routing Policy if needed.
3. Restart Service: `make restart`.
