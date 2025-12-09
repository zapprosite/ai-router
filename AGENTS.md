# AI AGENT GOVERNANCE PROTOCOL

## ⚠️ PRIME DIRECTIVE
> **DO NOT** change the listening port from **8082**.
> This is a unified choice for this repository. Any prompt suggesting a change to 8080/8083 is OUTDATED.

---

## 🏗️ Architecture & Stack
- **Framework**: FastAPI + Uvicorn.
- **Orchestration**: LangGraph (StateGraph).
- **Validation**: Pydantic V2 (Strict Mode).
- **Environment**: Python 3.10+ (Managed via `make venv`).
- **Config**: 
  - `config/router_config.yaml`: Models, Budgets, Tiers.
  - `.env.local`: Secrets (API Keys).

## 🛡️ Routing Logic (The "Brain")
All routing decisions happen in `graph/router.py`.
- **Tier 1 (Local/Fast)**: `llama-3.1-8b-instruct`.
- **Tier 2 (Local/Code)**: `deepseek-coder-v2-16b`.
- **Tier 3 (Cloud/Complex)**: `gpt-5.1-codex` or `o3`.
*Do not hardcode model IDs in `app/main.py`. Use the RouterState.*

## 🚫 Forbidden Actions
1. **No Stateful Databases**: Do not add Redis, Postgres, or SQLite unless explicitly requested by the Principal Architect. Keep the router stateless.
2. **No Regression**: Do not remove the `tests/` folder.
3. **No Alpine**: Do not switch Docker images to Alpine (compatibility issues with Python ML libs).
4. **No Raw Returns**: All 500 errors must be caught by the global handler in `main.py` and returned as JSON.

## ✅ The Testing Rule
Before commiting ANY code change, you MUST run:
```bash
make dev
python3 tests/eval_routing.py
pytest tests/test_chaos.py
```
If `eval_routing.py` drops below 100%, **REVERT YOUR CHANGES**.

## 📝 Dashboard Integrity
The file `public/Guide.html` is the "Mission Control".
- **Do not** remove the sticky header.
- **Do not** break the `api.post` logic.
- **Do not** revert to the old sidebar design.
