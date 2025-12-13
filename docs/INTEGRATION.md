# Integration Guide

## 🔌 API Endpoints
The router exposes two primary interfaces:

### 1. Smart Router (`POST /route`)
Recommended for new integrations. Returns detailed routing metadata.

```bash
curl -X POST http://localhost:8082/route \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Write a Python script"}]}'
```
**Response:**
```json
{
  "output": "def script(): ...",
  "usage": {
    "resolved_model_id": "deepseek-coder-v2-16b",
    "routing_meta": {"task": "code_gen", "complexity": "medium"}
  }
}
```

### 2. OpenAI Compatibility (`POST /v1/chat/completions`)
Drop-in replacement for any OpenAI-compatible client.

```bash
curl http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer any" \
  -d '{
    "model": "router-auto",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 💻 VS Code (Continue.dev) Integration

1. Install **Continue** extension.
2. Edit `~/.continue/config.yaml`:
    ```yaml
    models:
      - name: router-auto
        provider: openai
        model: router-auto
        apiBase: http://localhost:8082/v1
        apiKey: ROUTER
    ```
3. Reload VS Code. The router will now intelligently handle your code completion and chat!

---

## 🌐 Frontend Integration (React/JS)

```javascript
async function askRouter(prompt) {
  const res = await fetch('http://localhost:8082/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: prompt }]
    })
  });
  return await res.json();
}
```
