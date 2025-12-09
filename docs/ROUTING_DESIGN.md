# AI Router - Automatic Complexity-Aware Routing Design

## Overview

The AI Router implements **zero-configuration, complexity-aware multi-LLM routing**. Users never need to set flags like `critical=true` or `budget=high`. The router automatically infers task type and complexity from the prompt itself.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                              │
│        {"messages": [...], "model": "router-auto"}              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Classify Node                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  classify_prompt(messages) → RoutingMeta                 │   │
│  │  - Task detection (keywords + regex)                     │   │
│  │  - Complexity analysis (tokens, patterns, signals)       │   │
│  │  - Optional: LLM-assisted refinement if uncertain        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                        RoutingMeta:
                        {
                          "task": "code_crit_debug",
                          "complexity": "high",
                          "confidence": 0.85,
                          "classifier_used": "heuristic"
                        }
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Route Node                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  select_model_from_policy(meta) → model_id              │   │
│  │  - Consults routing_policy config                        │   │
│  │  - Checks model availability (local vs cloud)            │   │
│  │  - Returns first available model from policy list        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Invoke Node                                   │
│  - Executes LLM chain with SLA monitoring                       │
│  - Automatic fallback on error or timeout                       │
│  - Returns response with full routing telemetry                 │
└─────────────────────────────────────────────────────────────────┘
```

## Task Types

The router recognizes these task types (configurable in `router_config.yaml`):

| Task | Description | Default Models |
|------|-------------|----------------|
| `chitchat` | Casual conversation, greetings | Llama (local) |
| `simple_qa` | Factual questions | Llama (local) |
| `translation` | Language translation | Llama (local) |
| `summary` | Summarization | Llama (local) |
| `code_gen` | Code generation | DeepSeek (local) |
| `code_review` | Code review, simple debugging | DeepSeek (local) |
| `code_crit_debug` | Critical debugging (deadlocks, race conditions) | O3/Codex (cloud) |
| `system_design` | Architecture, distributed systems | O3/Codex (cloud) |
| `data_analysis` | Data analysis, statistics | DeepSeek (local) |
| `research` | Multi-step research, comparison | O3-mini (cloud) |
| `reasoning` | Complex reasoning, proofs | O3 (cloud) |

## Complexity Levels
### 3. "Poor Dev" Optimization (High Quality, Low Cost)
The router is tuned to maximize local model usage (Tier 1/2) while retaining cloud failover for critical tasks.

**Strategy:**
1. **Aggressive Context Usage**: We leverage DeepSeek Coder V2's large context (128k) for "high" complexity tasks (e.g. stack traces, scaffolding) that would normally go to Codex.
2. **Regex Boosting**: Strong intent signals (e.g. `def `, `class `, `import `) boost heuristic confidence to 0.8+, bypassing the slower/costly LLM classifier.
3. **Optimized Fallback**:
   - **Low/Medium Code**: `DeepSeek` -> `Codex Mini` (Failover)
   - **High Code/Debug**: `DeepSeek` -> `Codex` -> `O3` (Escalation)
   - **Critical/Arch**: `O3` (Direct)

This results in ~85-90% of traffic handled locally, with Cloud tiers reserved for true reasoning/critical incidents.

| Level | Indicators | Typical Models |
|-------|-----------|----------------|
| `low` | Short prompts (<50 tokens), greetings | Tier 1 (Llama) |
| `medium` | Code snippets, specific questions | Tier 2 (DeepSeek) |
| `high` | Stack traces, multi-file, design requests | Tier 3 (Codex) |
| `critical` | Production incidents, security, deadlocks | Tier 4 (O3) |

## Routing Policy

The routing policy is defined in `config/router_config.yaml`:

```yaml
routing_policy:
  chitchat:
    low: ["llama-3.1-8b-instruct"]
    medium: ["llama-3.1-8b-instruct", "gpt-5-mini"]
  
  code_gen:
    low: ["deepseek-coder-v2-16b"]
    medium: ["deepseek-coder-v2-16b", "gpt-5.1-codex-mini"]
    high: ["gpt-5.1-codex", "o3-mini-high"]
  
  code_crit_debug:
    high: ["o3", "o3-mini-high"]
    critical: ["o3"]
```

The router selects the **first available model** from the list. If cloud models are unavailable (no API key or fallback disabled), it falls back to local models.

## Adding/Removing Models

### Add a New Model

1. Add to `models` section in `router_config.yaml`:
```yaml
- id: new-model-id
  provider: openai  # or ollama
  name: "actual-model-name"
  tier: 3
  capabilities: ["code_gen", "reasoning"]
```

2. Add to relevant policies:
```yaml
routing_policy:
  code_gen:
    high: ["new-model-id", "existing-model"]
```

3. Restart the server.

### Remove a Model

1. Remove from `models` section.
2. Remove from all `routing_policy` entries.
3. Restart the server.

## LLM-Assisted Classifier

For ambiguous prompts, an optional LLM judge can refine the classification:

```yaml
classifier:
  llm_assisted: true
  llm_model: "gpt-5-nano"
  heuristic_confidence_threshold: 0.7
```

The LLM classifier is invoked **only when**:
1. `llm_assisted: true` in config
2. Heuristic confidence is below threshold
3. Cloud fallback is enabled

This keeps costs low while improving accuracy for edge cases.

## Response Telemetry

Every response includes routing metadata:

```json
{
  "output": "...",
  "usage": {
    "resolved_model_id": "deepseek-coder-v2-16b",
    "routing_meta": {
      "task": "code_gen",
      "complexity": "medium",
      "confidence": 0.85,
      "classifier_used": "heuristic"
    },
    "attempts": [
      {"model": "deepseek-coder-v2-16b", "status": "success"}
    ],
    "latency_ms_router": 342
  }
}
```

## Debug Endpoint

To inspect routing decisions without invoking models:

```bash
curl -X POST http://localhost:8082/debug/router_decision \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze this deadlock in production"}'
```

Response:
```json
{
  "routing_meta": {
    "task": "code_crit_debug",
    "complexity": "high",
    "confidence": 0.9
  },
  "selected_model_id": "o3",
  "fallback_available": true
}
```

## Backwards Compatibility

Legacy flags are still supported as **optional overrides**:

```json
{
  "messages": [...],
  "critical": true,    // Force critical complexity
  "prefer_code": true, // Hint for code tasks
  "budget": "high"     // Optional budget hint
}
```

However, these are **no longer required**. The router will infer the correct routing automatically.

## Environment Variables

The router automatically detects cloud availability based on API keys.

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Presence enables cloud models automatically | - |
| `ENABLE_OPENAI_FALLBACK` | **Optional override**. Set to `0` to force-disable cloud. | `1` (Auto) |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `ROUTER_CONFIG` | Path to config file | `config/router_config.yaml` |

## Testing

Run the routing evaluation:
```bash
pytest tests/integration/eval_routing.py -v
```

This tests:
- Task classification accuracy
- Complexity detection
- Policy-based routing
- End-to-end routing decisions
