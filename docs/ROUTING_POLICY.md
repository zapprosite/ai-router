<!-- idempotency_key: routing-policy-docs-v1; timeout: 10s; retries: 3 -->

# Routing Policy Preview

The `/v1/route/preview` endpoint returns a dry-run decision without contacting any provider. It uses thresholds defined in `router_policy.yaml` and simple heuristics over the estimated prompt token count.

## Inputs
- `kind`: `code` or `docs` (required)
- `tokens`: integer, estimated prompt tokens (required)

## Thresholds (from router_policy.yaml)
```
thresholds:
  docs:
    small_tokens: 600
    medium_tokens: 3000
  code:
    small_tokens: 400
    medium_tokens: 2000
```

## Decision Rules
- kind = `code`:
  - tokens ≤ `code.small_tokens` → route=`local`, model=`qwen3-14b`
  - otherwise → route=`cloud`, model=`gpt-5-codex`
- kind = `docs`:
  - tokens ≤ `docs.small_tokens` → route=`local`, model=`qwen3-14b`
  - otherwise → route=`cloud`, model=`gpt-5-mini` (≤ medium) or `gpt-5-high` (> medium)

## Output Shape
```
{
  "route": "local|cloud",
  "model": "qwen3-14b|gpt-5-codex|gpt-5-high|gpt-5-mini|qwen3-8b",
  "rationale": "...",
  "cost_estimate": {
    "unit": "usd",
    "prompt_tokens": <int>,
    "completion_tokens": 0,
    "total": <float>
  }
}
```

Notes:
- This is a pure function; it does not call external providers.
- No secrets are logged. Only safe metadata is emitted by the middleware.
