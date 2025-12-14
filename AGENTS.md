# 🤖 AI Agent & Contributor Guidelines
> **"Standardization, Resilience, and Verification are our core virtues."**

This document defines the **Senior Dev Standard** for all AI Agents and human contributors working on the **AI Router** project. Deviations from this standard are considered failures.

---

## 🏆 The "Senior Developer" Standard

### 1. Verification First
- **Never Assume**: If you change code, you MUST verify it.
- **Run the Suite**: Use `make verify` before submitting ANY change.
- **Regressions are Unacceptable**: If your change fixes one thing but breaks another (e.g., linting, unit tests), do not submit it. Fix the regression first.
- **Evidence**: Provide logs, screenshots, or terminal outputs proving your verification.

### 2. Code Quality & Structure
- **File Organization**:
  - `app/`: FastAPI application endpoints (interfaces).
  - `graph/`: Core logic (Router, Cost Guard, policies).
  - `providers/`: API Clients (OpenAI, Ollama) - strictly typed.
  - `config/`: YAML configurations + Env vars.
  - `tests/`: Organized by type (`unit`, `api`, `routing`, `resilience`, `performance`, `security`).
- **Style**:
  - Python: Checked by `ruff`. Follow PEP8.
  - Types: Use `TypeDict`, `dataclass`, or `Pydantic` models. No raw `dict` passing without schema where possible.
  - **No Legacy Junk**: Delete unused files. Do not comment out code blocks "just in case" — use git history.

### 3. Architecture Principles
- **Config-Driven**: Logic should be controlled by `router_config.yaml` or Environment Variables (`.env`), not hardcoded strings.
- **Fail-Safe**: If a model fails, fallback to something safer (e.g., Local LLM).
- **Cost-Aware**: Every request is priced. Blocks costly requests unless authorized.
- **Observability**: Logs must be structured (JSON/Key-Value). Metrics must be accessible.

---

## 🛠 Worksapce & Workflow

### Environment Setup
- **System**: Linux / Python 3.12+
- **Virtual Env**: `.venv` (managed by `requirements.txt`).
- **Command Center**: `Makefile` is the entry point for everything.

### Critical Commands
| Command | Purpose | When to use |
|org|---|---|
| `make dev` | Starts server + UI with hot-reload | Development |
| `make test` | Runs unit & routing tests | Quick check |
| `make verify` | **FULL** Test Suite (Lint, Unit, API, E2E) | **MANDATORY** pre-commit |
| `make fix` | Auto-fixes linting issues | If lint fails |

---

## 🧪 Testing Strategy

We follow the **Pyramid of Testing**:

1.  **Unit Tests** (`tests/unit/`):
    - Fast, mocked dependencies.
    - Validate logic (Router policies, Cost Guard math).
    - *Requirement*: 100% pass rate.

2.  **Routing Tests** (`tests/routing/`):
    - Validate decision making (Classification -> Selection).
    - Ensure prompts go to the right model tier.
    - *Requirement*: 100% pass rate.

3.  **API/Integration Tests** (`tests/api/`):
    - Test HTTP endpoints (`/v1/chat/completions`, `/route`).
    - Verify Auth hooks (API Keys).
    - *Requirement*: 100% pass rate.

4.  **Resilience & Chaos** (`tests/resilience/`):
    - Simulate network drops (mocks).
    - Simulate 401/429/500 errors.
    - Verify circuit breakers and fallbacks.

5.  **Performance** (`tests/performance/`):
    - `locustfile.py` for load simulation.
    - Ensure P95 latency is under SLA (<6s for router overhead).

---

## 🚫 Anti-Patterns (Don't Do This)
- ❌ **Hardcoding API Keys**: Always use `os.getenv`.
- ❌ **Hardcoding Model IDs**: Use the `resolve_model_alias` function logic or config lookups.
- ❌ **Ignoring Linter**: "It works on my machine" is not valid if the CI linter fails.
- ❌ **Leaving Dead Code**: If you refactor `eval_routing.py` into a test, DELETE the original script.
- ❌ **Modifying `mock_responses` manually**: Use `challenge_demo.py` or proper fixtures for simulation.

---

## 📝 Documentation
- **Keep it Sync**: If you add a feature, update `README.md` and `Guide.html`.
- **Walkthroughs**: Maintain `walkthrough.md` in the artifacts folder to track progress for the user.
- **Tasks**: Update `task.md` continuously.

Reference this guide whenever you are unsure about the definition of "Done".
