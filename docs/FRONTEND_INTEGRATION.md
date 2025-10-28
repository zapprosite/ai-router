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
