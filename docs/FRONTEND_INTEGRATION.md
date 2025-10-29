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
