<!-- idempotency_key: frontend-guide-final-2025-10-21-v2 -->
# Frontend Integration Guide

Goal: a simple UI that calls the router and shows route decisions, selected tier/model, and latency.

## Minimal UX
- Prompt textarea.
- Select: Task type (`code|docs`).
- Badge: selected tier and model.
- Display: latency and token usage.
- Error banner with diagnostic details.

## API Calls (available now)
- `GET /v1/models` → populate model list.
- `GET /healthz` → status badge.

## API Calls (when ready)
- `POST /v1/chat/completions` and/or `POST /v1/responses`.

## Example (fetch)
```ts
export async function getModels() {
  const r = await fetch('/v1/models');
  const j = await r.json();
  return Array.isArray(j.data) ? j.data.map((m:any) => m.id) : [];
}
Telemetry
Capture: route_decision, model_id, latency_ms, tokens_in/out.

Redact user content before logging.
