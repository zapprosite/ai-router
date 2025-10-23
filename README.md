<!-- idempotency_key: readme-gh-links-2025-10-21-v1 -->
# AI Router · Hybrid LLM Orchestrator

A lightweight router that picks the **most cost-effective LLM** per request. It balances **local GPU models** and **cloud models** using task type, token size, and latency/cost targets.

<p align="left">
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-blue.svg">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-black.svg">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-FastAPI%20%7C%20Uvicorn-1f425f.svg">
</p>

## Why
Not every prompt needs an expensive cloud model. Short, simple prompts go to local Qwen on GPU. Complex or large prompts go to cloud models. The goal is stable p95 latency and predictable spend.

## Features
- Hybrid routing (GPU ↔ cloud) with model tiers
- Simple classification by task type and token count
- Minimal OpenAI-compatible surface
- Structured logs and k6 smoke tests

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
├─ PRD_TASK_MASTER.md
├─ AGENTS.md
├─ GOVERNANCE.md
├─ ARCHITECTURE.md
└─ FRONTEND_INTEGRATION.md

ruby
￼Copiar código

## Documentation
- PRD: [./PRD_TASK_MASTER.md](PRD_TASK_MASTER.md)  
- Agents & Routing Policy: [./AGENTS.md](AGENTS.md)  
- Governance: [docs/GOVERNANCE.md](docs/GOVERNANCE.md)  
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
- Frontend Integration Guide: [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)  
- Env template: [docs/ai-stack.env.example](docs/ai-stack.env.example)

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
Minimal OpenAI-compat surface first

No secrets in logs. No PII. Env only via /srv-2/secrets/ai-stack/ai-stack.env

Idempotent patches with explicit keys and reviewable diffs

Roadmap
Router scoring with feedback loop (cost/latency/quality)

/v1/chat/completions

Dry-run route preview endpoint for CI

Adaptive policy per org/project

License
MIT © 2025 William Rodrigues / AI-Stack

## Status
[![CI](https://github.com/zapprosite/ai-router/actions/workflows/ci.yml/badge.svg)](https://github.com/zapprosite/ai-router/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/zapprosite/ai-router)](https://github.com/zapprosite/ai-router/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Local Smoke

<!-- idempotency_key: readme-local-smoke-2025-10-22-v1 -->

Run a minimal local smoke (no CI, no internet):

1) Pre-req: Install ACL and grant read-only to the current user (never print secrets)

```bash
# Install ACL tools (Debian/Ubuntu). On RHEL/CentOS use: sudo yum install -y acl
sudo apt-get update && sudo apt-get install -y acl

# Grant read-only to current user for the env file (no contents shown)
sudo setfacl -m u:$(whoami):r /srv-2/secrets/ai-stack/ai-stack.env

# Optional: verify ACLs (safe; does not print secrets)
getfacl -p /srv-2/secrets/ai-stack/ai-stack.env || true
```

2) From repo root, bring up and verify endpoints

```bash
cd /srv/projects/ai-router  # repo root
docker compose -f docker-compose.yml up -d --build ai-router
curl -fsS http://localhost:8082/healthz | tee healthz.json
curl -fsS http://localhost:8082/v1/models | tee models.json
```

3) Run k6 models (choose one)

- Host network (simple):

```bash
docker run --rm --network host \
  -e BASE_URL=http://localhost:8082 \
  -v "$PWD/tests:/scripts:ro" \
  -v "$PWD:/out" \
  grafana/k6:latest run --summary-export /out/k6_models.json /scripts/k6_models.js | tee k6_stdout.log
```

- Compose network (hermetic):

```bash
CID=$(docker compose -f docker-compose.yml ps -q ai-router)
NET=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' "$CID")
docker run --rm --network "$NET" \
  -e BASE_URL=http://ai-router:8082 \
  -v "$PWD/tests:/scripts:ro" \
  -v "$PWD:/out" \
  grafana/k6:latest run --summary-export /out/k6_models.json /scripts/k6_models.js | tee k6_stdout.log
```

Extract p95 and error rate:

```bash
P95=$(jq -r '.metrics.http_req_duration.values["p(95)"]' k6_models.json 2>/dev/null || true)
ERR=$(jq -r '(.metrics.http_req_failed.values.rate // .metrics.http_req_failed.rate // 0)' k6_models.json 2>/dev/null || echo 0)
echo "p95_ms=${P95:-NA} err_rate=${ERR:-NA}"
```

Note: A scripted flow may be available in `scripts/ci-smoke-run.sh` and is documented in PRD A3; it is not required to exist for this local smoke.
