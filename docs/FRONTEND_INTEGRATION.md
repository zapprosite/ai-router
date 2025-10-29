Integração Frontend

Esta API é compatível com a listagem de modelos do padrão OpenAI e expõe uma rota inteligente que escolhe o melhor modelo local com base no conteúdo.

Listar modelos (compat OpenAI)
```bash
curl -fsS http://localhost:8082/v1/models | jq
```

Rota inteligente (recomendada)
```bash
POST http://localhost:8082/route
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Explique HVAC em 1 frase."}],
  "budget": "low",
  "prefer_code": false
}
```

Esquemas de Requisição/Resposta (JSON Schema)

Rota principal — `POST /route`

Request
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["messages"],
  "additionalProperties": false,
  "properties": {
    "messages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "properties": {
          "role": {"enum": ["system", "user", "assistant", "tool"]},
          "content": {"type": "string", "minLength": 1}
        },
        "additionalProperties": false
      }
    },
    "latency_ms_max": {"type": "integer", "minimum": 0},
    "budget": {"enum": ["low", "balanced", "high"]},
    "prefer_code": {"type": "boolean"}
  }
}
```

Response
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["output", "usage"],
  "properties": {
    "output": {"type": "string"},
    "usage": {
      "type": "object",
      "required": [
        "prompt_tokens_est",
        "completion_tokens_est",
        "total_tokens_est",
        "resolved_model_id",
        "config_path"
      ],
      "properties": {
        "prompt_tokens_est": {"type": "integer"},
        "completion_tokens_est": {"type": "integer"},
        "total_tokens_est": {"type": "integer"},
        "resolved_model_id": {"type": "string"},
        "config_path": {"type": "string"},
        "latency_ms_router": {"type": "integer"}
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```

OpenAI (shim) — `POST /v1/chat/completions`

Request (mínimo viável)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["model", "messages"],
  "properties": {
    "model": {"const": "router-auto"},
    "messages": {
      "type": "array",
      "items": {"type": "object", "required": ["role", "content"],
        "properties": {"role": {"type": "string"}, "content": {"type": "string"}}}
    },
    "temperature": {"type": "number"},
    "max_tokens": {"type": ["integer", "null"]}
  }
}
```

Response (formato OpenAI)
```json
{
  "id": "chatcmpl-…",
  "object": "chat.completion",
  "created": 1730140000,
  "model": "llama-3.1-8b-instruct",
  "choices": [
    {"index": 0, "message": {"role": "assistant", "content": "…"}, "finish_reason": "stop"}
  ],
  "usage": {"resolved_model_id": "llama-3.1-8b-instruct", "total_tokens_est": 123}
}
```

Status Codes
- 200: sucesso
- 400: payload inválido (pydantic)
- 500: erro interno do provider/roteador

Formato de erro (FastAPI)
```json
{"detail": "<descrição do erro>"}
```

Exemplos curl

Texto curto (esperado Llama 8B)
```bash
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' \
  | python3 -m json.tool | sed -n '1,24p'
```

Código com prefer_code (esperado DeepSeek 16B)
```bash
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}' \
| python3 -m json.tool | sed -n '1,24p'
```

Resolução dinâmica (`model_id`)
- Chat/explicação: `llama-3.1-8b-instruct`.
- Código: `deepseek-coder-v2-16b`.

Cabeçalhos relevantes
- `Content-Type: application/json`.


## Continue.dev (VS Code) — router-auto + MCP

Uso com Continue (28/10/2025) sem referenciar modelos físicos. Configure um único modelo lógico `router-auto` apontando para o nosso shim OpenAI e habilite o MCP do roteador:

Workspace `.continue/config.yaml` (já incluído no repositório):
```yaml
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

No Continue (VS Code):
- Selecione `router-auto` para chat, edit, apply e autocomplete.
- MCP: em agent mode, a ferramenta `ai_router.route` ficará disponível a partir do servidor `ai_router_mcp`. Peça ao agente para “usar a ferramenta ai_router.route” passando `messages`, `budget` (opcional) e `prefer_code` (opcional). A ferramenta chama `POST /route` e retorna `{content, usage}`.

MCP (Opcional)
- O MCP não é necessário para chat/edit/apply/autocomplete quando se usa `router-auto` via shim OpenAI. 
- Use MCP apenas se quiser acionar `/route` como ferramenta (agent mode) ou integrar serviços como tools. Para reativar, adicione ao `.continue/config.yaml`:
```yaml
mcpServers:
  - name: ai_router_mcp
    command: python
    args: ["tools/ai_router_mcp.py"]
```

Screenshot (selecionando `router-auto` nos 4 papéis):

![Continue VS Code — router-auto em chat/edit/apply/autocomplete](docs/images/continue-router-auto.png)

Coloque a captura de tela no caminho `docs/images/continue-router-auto.png`.

Mais detalhes e Quickstart do Continue:
- Consulte `docs/CONTINUE.md` para configuração completa (`.continue/config.yaml`) e passos no VS Code.

### Exemplo: Chat Completions (OpenAI)

O shim adiciona `POST /v1/chat/completions` e mapeia para o roteador. Use `model: "router-auto"`:

```bash
curl -fsS http://localhost:8082/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
        "model": "router-auto",
        "messages": [{"role":"user","content":"Explique HVAC em 1 frase."}]
      }' | jq '.'
```

Resposta (formato OpenAI), onde `model` reflete o modelo real resolvido pelo roteador:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 173014...,
  "model": "llama-3.1-8b-instruct",
  "choices": [
    {"index":0,"message":{"role":"assistant","content":"..."},"finish_reason":"stop"}
  ],
  "usage": {"resolved_model_id":"llama-3.1-8b-instruct", "...": "..."}
}
```

### Verify locally

```bash
curl -fsS http://localhost:8082/healthz
curl -fsS http://localhost:8082/v1/models | jq -r '.data[].id' | grep router-auto
curl -fsS http://localhost:8082/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"router-auto","messages":[{"role":"user","content":"Explain HVAC in one sentence."}]}' | jq .
```

Esperado: o campo `.model` deve ser igual ao backend escolhido (valor de `usage.resolved_model_id`).

### MCP tool usage

Rode o Continue em modo agente (agent mode) e chame a ferramenta:

- Nome do servidor: `ai_router_mcp`
- Ferramenta: `ai_router.route`
- Args:

```json
{
  "messages": [{"role":"user","content":"Summarize the repo structure."}],
  "budget": "balanced",
  "prefer_code": false
}
```

### Troubleshooting

- Se `router-auto` não aparecer em `/v1/models`, reinicie o app e verifique novamente. O shim injeta o `router-auto` em cold start.
- Se o shim de chat responder sem `.choices`, cheque os logs do app e confirme que `/route` está acessível.
