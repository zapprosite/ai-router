<!-- idempotency_key: governance-final-2025-10-21-v1 -->
# Governance

## Operating Principles
- Keep the router small: minimal endpoints, predictable behavior.
- Observability first: latency p95, error rate, and route decisions are mandatory logs.

## Secrets & Config
- Secrets live at `/srv-2/secrets/ai-stack/ai-stack.env` (0600).
- Never print secrets. No Anthropic keys per policy.
- Env example provided at `docs/ai-stack.env.example`.

## Security
- No external calls unless explicitly allowed.
- Disable SSRF vectors; prefer allow-listed HTTP clients.
- Structured logs. Redact user content when possible.

## Reliability
- Health endpoints: `/healthz`, `/v1/models`.
- k6 smoke as acceptance gate: p95 ≤ 1200 ms, error < 1%.
- Promotion on failure: if tier breaches targets, promote one step with cooldown.

## Deployment
- Docker Compose, port `8082`.
- Recreate container on env changes.
- Version endpoints and keep changes backward-compatible.
