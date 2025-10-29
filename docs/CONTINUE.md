## Continue.dev + `router-auto` (OpenAI shim + MCP)

**Goal:** use a single logical model in Continue, while the AI Router chooses the backend.  
**Endpoints:** `/healthz`, `/v1/models`, `/v1/chat/completions` (shim), and `/route` (internal).

### Quickstart
1. Install the Continue VS Code extension.
2. Ensure the router is running locally and `/healthz` returns `{ "ok": true }`.
3. Use the workspace file `.continue/config.yaml` (see below). No Ollama/OpenAI IDs are referenced in Continue; the router decides.

### Continue config
```yaml
# .continue/config.yaml
%YAML 1.1
---
name: ai-router
version: 0.0.1
schema: v1

models:
  - name: router-auto
    provider: openai
    model: router-auto
    apiBase: http://localhost:8082/v1
    apiKey: ROUTER
    roles: [chat, autocomplete, edit, apply]

agent:
  chatModel: router-auto
  editModel: router-auto
  applyModel: router-auto
  autocompleteModel: router-auto

mcpServers:
  - name: ai_router_mcp
    command: python
    args: ["tools/ai_router_mcp.py"]
```

