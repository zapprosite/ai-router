# AI Router Refactor Checklist

- [x] **PHASE 1: INGESTION & DIAGNOSTIC**
    - [x] Full Context Scan (Makefile, app/main.py, public/Guide.html, config, router.py)
    - [x] Identify port inconsistencies (8080, 8083, 8082)

- [x] **PHASE 2: INFRASTRUCTURE REFACTORING (Target: 8082)**
    - [x] Refactor `Makefile` (dev/test targets to 8082)
    - [x] Update `app/main.py` (ensure port agnostic or standardized)
    - [x] Update `public/Guide.html` (unify fetch origin)
    - [x] Update Systemd/Scripts matches

- [x] **PHASE 3: INTELLIGENT ROUTING LOGIC**
    - [x] Implement Tier 1 (Simple/General -> llama3.1)
    - [x] Implement Tier 2 (Code -> deepseek-coder-v2)
    - [x] Implement Tier 3 (Cloud Fallback -> OpenAI)
    - [x] Implement Complexity Heuristics (Regex, Token Count)
    - [x] Update `router_config.yaml` to match new tiers

- [x] **PHASE 4: SIMULATION & VERIFICATION**
    - [x] Create `scripts/verify_router.py`
    - [x] Run Scenario A (Simple)
    - [x] Run Scenario B (Medium Code)
    - [x] Run Scenario C (Complex/Fallback)

- [x] **PHASE 5: FINAL POLISH ("Gold Plating")**
    - [x] **Repository Cleanup**: Archived legacy scripts to `scripts/legacy/`.
    - [x] **Endpoint Hardening**: Added global JSON exception handler.
    - [x] **Dashbard UX**: Refactored `Guide.html` into "Mission Control".

- [x] **PHASE 6: ENTERPRISE QA & HARDENING**
    - [x] **Planning & Analysis**: Gap analysis vs RouteLLM/LiteLLM.
    - [x] **Hardening**:
        - [x] Input Validation (Pydantic strictness).
        - [x] Security Headers & CORS audit.
        - [x] Error Masking (No stack traces).
    - [x] **Advanced Testing**:
        - [x] Semantic Routing Eval (`tests/eval_routing.py`).
        - [x] Chaos Testing (`tests/test_chaos.py`).
        - [x] Load Testing (`tests/performance/locustfile.py`).
    - [x] **Documentation & Cleanup**:
        - [x] `docs/DEPLOYMENT.md` & `docs/TESTING.md`.
        - [x] Final formatting check (PEP8).

- [x] **PHASE 7: DOCUMENTATION & GOVERNANCE**
    - [x] **README.md**: Complete rewrite (Mission Control, Architecture, Badges).
    - [x] **AGENTS.md**: Governance file for future AI Agents.
    - [x] **Cleanup**: Remove `rascunho.md`, legacy docs.

- [ ] **PHASE 8: FINAL CONSOLIDATION & AUDIT**
    - [ ] **The Purge**: Remove legacy scripts, backups, technical debt.
    - [ ] **Restructure Tests**: Organize `tests/` into Unit, Integration, E2E, Performance.
    - [ ] **Verification**: Run full regression suite (Smoke, Eval, Chaos).
