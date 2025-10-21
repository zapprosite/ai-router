<!-- idempotency_key: architecture-final-2025-10-21-v2 -->
# Architecture

## Components
- **FastAPI app** on port 8082.
- **Routing policy**: task_type + token_count + complexity → tier.
- **LangGraph (planned)**: routing graph with judge/promotion nodes.
- **Tiers**:
  - Economy: local GPU (Qwen3 8B/14B via Ollama or vLLM).
  - Balanced: cloud (gpt-5-codex).
  - Quality: cloud (gpt-5-high).

## Control Flow
1. Classify request (`code|docs`, approx tokens).
2. Choose tier by thresholds and policy.
3. Execute request on target provider.
4. Measure latency and status.
5. Promote or demote on threshold breach/recovery.

## Interfaces
- **Now**: `GET /healthz`, `GET /v1/models`.
- **Roadmap**: `POST /v1/chat/completions`, `POST /v1/responses`, `/route/preview` (dry-run).

## Observability
- Log fields: `route_decision`, `model_id`, `latency_ms`, `tokens_in`, `tokens_out`.
- k6 smoke as acceptance gate (p95 ≤ 1200 ms, error < 1%).

## Non-Goals
- Training/fine-tuning, user auth, billing. Keep the router focused.
