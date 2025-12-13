# Contributing Guide

## 🛠️ Development Setup
1. **Install Dependencies**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -e . # Install as package
    ```
2. **Setup Tools**:
    ```bash
    pip install ruff pytest
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
