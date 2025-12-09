# System Architecture

The AI Router acts as an intelligent gateway, sitting between your applications and various AI models. It makes real-time decisions to optimize for cost, quality, and speed.

## High-Level Data Flow

```mermaid
graph TD
    User[User / App] -->|Request| API[AI Router API :8087]
    
    subgraph "Decision Engine"
        API --> Class[Classifier (Heuristic/LLM)]
        Class -->|Simple Task| LocalRoute
        Class -->|Complex Task| CloudRoute
        Class -->|Critical Code| EliteRoute
    end
    
    subgraph "Tier 1: Local (Free)"
        LocalRoute --> Llama[Llama 3.1 8B]
        LocalRoute --> Deep[DeepSeek Coder]
    end
    
    subgraph "Tier 3: Cloud Balanced"
        CloudRoute --> GPT4[GPT-4.1 / 4o-mini]
    end
    
    subgraph "Tier 5: Elite (2025)"
        EliteRoute --> GPT5[GPT-5.1 Codex]
        EliteRoute --> O3[O3 Reasoning]
    end
    
    Llama -->|Response| API
    Deep -->|Response| API
    GPT4 -->|Response| API
    GPT5 -->|Response| API
```

## Core Components

### 1. The Classifier
The router analyzes every incoming prompt. It looks for:
- **Keywords**: "traceback", "system design", "write code".
- **Complexity**: Length of input, number of turns.
- **Intent**: Is this a casual chat or a production outage?

### 2. The Routing Policy (`router_config.yaml`)
Defined rules that determine where a prompt goes based on its classification.
- **Low Complexity** -> Tier 1 (Local)
- **Medium Complexity** -> Tier 3 (Cloud Balanced)
- **High/Critical** -> Tier 5 (Elite)

### 3. Stability Layer
If a requested model (e.g., `gpt-5.1-codex`) is temporarily unavailable or if the API key lacks access, the Stability Layer transparently re-routes the request to the nearest equivalent (e.g., `gpt-4.1`). This ensures 100% uptime.

### 4. Observability Layer
The router provides deep visibility into usage and costs:
- **Metrics Endpoint**: `/debug/metrics` provides real-time JSON stats (latency, cost, tokens).
- **Structured Logs**: Requests are logged to `logs/metrics.jsonl` with a unique `prompt_id`.
- **Cost Guard**: Estimates cost *before* execution and blocks queries that exceed the budget.
