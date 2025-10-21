<!-- idempotency_key: readme-gh-final-2025-10-21-v1 -->
# AI Router · Hybrid LLM Orchestrator

A lightweight router that picks the **most cost-effective LLM** per request. It balances **local GPU models** and **cloud models** based on task type, token size, and latency/cost targets.

<p align="left">
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-blue.svg">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-black.svg">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-FastAPI%20%7C%20Uvicorn-1f425f.svg">
</p>

---

## Why
Not every prompt needs an expensive cloud model. Simple and short prompts go to local Qwen on GPU. Complex or large prompts go to cloud models. The goal is a stable p95 latency and predictable spend.

## Features
- Hybrid routing (GPU ↔ cloud) with model tiers.
- Simple classification by task type and token count.
- OpenAI-compatible surface kept minimal.
- Structured logs and k6 smoke tests.

## Current Endpoints
- `GET /healthz` → `{"ok": true}`
- `GET /v1/models` → `{"data":[{"id":"..."}]}`

> Roadmap (not yet implemented): `POST /v1/chat/completions`, `POST /v1/responses`.

## Folder Structure
ai-router/
├─ app.py
├─ Dockerfile
├─ docker-compose.yml
├─ tests/
│ └─ k6_models.js
└─ docs/
├─ PRD_TASK_MASTER.md # product doc (project scope and phases)
├─ AGENTS.md # agent rules and routing policy
├─ GOVERNANCE.md # ops & security policy
├─ ARCHITECTURE.md # components and data flow
└─ FRONTEND_INTEGRATION.md # UI/UX integration guide

ruby
￼Copiar código

## Routing Policy (initial)
| Task | Tokens | Complexity | Route | Example model |
|-----:|:------:|:----------:|:-----:|:--------------|
| code | ≤ 400  | low        | local | qwen3:14b     |
| code | ≤ 2000 | medium     | cloud | gpt-5-codex   |
| code | >2000 or high | cloud | gpt-5-high |
| docs | ≤ 600  | low        | local | qwen3:8b      |
| docs | ≤ 3000 | medium     | cloud | gpt-5-mini    |
| docs | >3000 or high | cloud | gpt-5-high |

Promotion rule: if latency or confidence breaches targets, promote one tier.

## Quick Start
```bash
docker compose up -d
curl -fsS http://localhost:8082/healthz | python3 -m json.tool
curl -fsS http://localhost:8082/v1/models | python3 -m json.tool
Secrets live outside the repo at /srv-2/secrets/ai-stack/ai-stack.env.
See docs/ai-stack.env.example for a safe template.

Testing
bash
￼Copiar código
docker run --rm --network host \
  -e BASE_URL=http://localhost:8082 \
  -v ./tests:/scripts:ro grafana/k6 run /scripts/k6_models.js
Governance
Minimal OpenAI-compat surface first.

No secrets in logs. No PII. Env only via /srv-2/secrets/ai-stack/ai-stack.env.

Idempotent patches with explicit keys and reviewable diffs.

Roadmap
Router scoring with feedback loop (cost/latency/quality).

/v1/chat/completions.

Dry-run route preview endpoint for CI.

Adaptive policy per org/project.

License
MIT © 2025 William Rodrigues / AI-Stack
