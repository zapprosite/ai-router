# Testing Standards: Senior Dev Edition

This document outlines the "Senior Dev Standard" for testing in the AI Router project. The goal is maintainability, speed, and confidence without boilerplate.

## 1. Philosophy: Minimal Functional & Pragmatic
- **No Fluff**: Test the behavior, not the implementation details.
- **Fail Fast**: Tests should run locally in seconds.
- **AAA Pattern**: Arrange, Act, Assert. Keep it visible.
- **Integration over Mock-Heavy Unit**: Prefer testing the `router.py` flow with a mocked LLM over isolating every internal helper function.

## 2. Directory Structure
```
tests/
├── unit/           # Fast, isolated function/class logic. No IO.
├── integration/    # Component interaction (e.g., Router + Mocked Policy).
├── e2e/            # Full system flow (FastAPI client -> Router).
├── conftest.py     # Global fixtures (Mock Environment, Clients).
```

## 3. The Standard Format

### File Naming
- Must start with `test_`.
- Snake case: `test_routing_eval.py`.

### Code Style
- **Use `pytest` Style**, not `unittest.TestCase` classes (unless beneficial for grouping).
- **Docstrings**: One line explaining *what* it verifies.
- **Fixtures**: Use `client` and `monkeypatch` from `conftest.py`. don't reinvent the wheel.

### Example

```python
import pytest
from graph.router import classify_prompt

def test_critical_security_prompt_escalates():
    """Security vulnerabilities must route to critical complexity."""
    # Arrange
    prompt = [{"role": "user", "content": "I found a SQL injection vulnerability."}]
    
    # Act
    meta = classify_prompt(prompt)
    
    # Assert
    assert meta.complexity == "critical"
    assert meta.task == "code_crit_debug"
```

## 4. Verification Workflow (`make verify`)

We use a unified command to ensure the repo is clean before commit:

```bash
make verify
```

This runs:
1.  **Static Analysis**: `ruff check` (Format & Imports).
2.  **Auth Validation**: `scripts/validate_auth.py` checks for valid key patterns (without making calls).
3.  **Unit & Logic Tests**: `pytest` covering core router logic.
4.  **Resilience Checks**: `pytest tests/resilience/` verifying circuit breakers and auth failovers.

## 5. Resilience & Chaos Strategy

We treat "Cloud Failure" as a normal state, not an exception.

### Key Scenarios Tested (`tests/resilience/`):
- **Cloud Auth Failure (401)**: Must switch to local fallback instantly and cache the failure.
- **Provider Timeout**: Must retry with a cheaper/faster model.
- **Provider 5xx**: Must assume downtime and fallback.

### Code Pattern
```python
def test_cloud_auth_failure_triggers_fallback(client, monkeypatch):
    """If cloud returns 401, router must use local model and flag cloud_available=False."""
    # ... mock 401 response ...
    # Verify usage["cloud_available"] is False
    # Verify usage["resolved_model_id"] is local
```

## 6. Environment & Mocks
- **NEVER** hit real production APIs in default `make verify`.
- The `isolated_env` fixture in `conftest.py` automatically resets global auth caches (`_OPENAI_AUTH_STATUS`) between tests to prevent pollution.

## 7. Coverage Goal
- **100% Path Coverage** on Core Logic (Router).
- **Happy Path + 1 Error Case** on Adapters.
- **100% Resilience Scenarios** (Auth fail, Timeout, Rate Limit).
