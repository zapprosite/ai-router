# AI Router Integration Guide

Use AI Router as a drop-in OpenAI replacement in any tool that supports custom OpenAI endpoints.

## Quick Reference

| Setting | Value |
|---------|-------|
| **Base URL** | `http://localhost:8087/v1` |
| **API Key** | Your `AI_ROUTER_API_KEY` from `.env.local` |
| **Model** | `router-auto` (or any configured model) |

---

## IDE Extensions

### VS Code - Continue

Edit `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "AI Router",
      "provider": "openai",
      "model": "router-auto",
      "apiBase": "http://localhost:8087/v1",
      "apiKey": "YOUR_AI_ROUTER_API_KEY"
    }
  ]
}
```

### VS Code - Cody / Sourcegraph

Settings (`Ctrl+,` → search "Cody"):

```
Cody: Custom API Endpoint = http://localhost:8087/v1
Cody: API Key = YOUR_AI_ROUTER_API_KEY
```

### Cursor IDE

1. Open Settings → Models
2. Add Custom OpenAI:
   - **Base URL**: `http://localhost:8087/v1`
   - **API Key**: `YOUR_AI_ROUTER_API_KEY`
   - **Model**: `router-auto`

### JetBrains AI Assistant (Custom)

In IDE settings:

```
AI Assistant → OpenAI Compatible → Base URL: http://localhost:8087/v1
```

---

## CLI Tools

### OpenAI CLI

```bash
export OPENAI_API_BASE=http://localhost:8087/v1
export OPENAI_API_KEY=YOUR_AI_ROUTER_API_KEY
openai api chat.completions.create -m router-auto -g user "Hello"
```

### LiteLLM

```bash
export OPENAI_API_BASE=http://localhost:8087/v1
export OPENAI_API_KEY=YOUR_AI_ROUTER_API_KEY
litellm --model openai/router-auto
```

### aider

```bash
aider --openai-api-base http://localhost:8087/v1 \
      --openai-api-key YOUR_AI_ROUTER_API_KEY \
      --model router-auto
```

---

## Python / Node.js

### Python (openai library)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8087/v1",
    api_key="YOUR_AI_ROUTER_API_KEY"
)

response = client.chat.completions.create(
    model="router-auto",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Node.js

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:8087/v1',
  apiKey: 'YOUR_AI_ROUTER_API_KEY'
});

const response = await client.chat.completions.create({
  model: 'router-auto',
  messages: [{ role: 'user', content: 'Hello!' }]
});
```

---

## SaaS / Web Apps

### Any OpenAI-Compatible App

Most apps have these settings:

| Field | Value |
|-------|-------|
| API Base URL | `http://localhost:8087/v1` |
| API Key | `YOUR_AI_ROUTER_API_KEY` |
| Model | `router-auto` |

### Expose Externally (ngrok)

To use AI Router from external services:

```bash
ngrok http 8087
# Use the ngrok URL as your base: https://abc123.ngrok.io/v1
```

---

## Environment Variables

Set globally in your shell:

```bash
# ~/.bashrc or ~/.zshrc
export OPENAI_API_BASE=http://localhost:8087/v1
export OPENAI_API_KEY=YOUR_AI_ROUTER_API_KEY
```

---

## Verify Connection

```bash
curl http://localhost:8087/v1/models \
  -H "X-API-Key: YOUR_AI_ROUTER_API_KEY"
```

Expected: JSON list with `router-auto` and configured models.
