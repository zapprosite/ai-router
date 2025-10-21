# AGENTS.md — Contrato do codex CLI (MCP Task Master)

## BOOT (sempre no início)
Ler via **MCP filesystem.read_text_file**:
- `/srv/projects/ai-router/PRD_TASK_MASTER.md`
- `/srv/projects/ai-router/AGENTS.md`
- `/srv/projects/ai-router/README.md`
Resumir cada um em 3–6 bullets e salvar em **MCP memory** com chaves `{doc:"PRD"|"AGENTS"|"README"}`. Responder **CONTEXT_READY**.

## Classificação (JSON estrito)
Schema obrigatório:
`{"task_type":"code|docs","complexity":"low|medium|high","needs_tools":false}`  
`approx_tokens = ceil(len(chars)/4)`.

## Roteamento custo→qualidade
- **code**: `≤400` e `complexity!=high` → `qwen3:14b` (local)  
  `≤2000` → `gpt-5-codex` (cloud)  
  `>2000` ou `high` → `gpt-5-high` (cloud)
- **docs**: `≤600` e `complexity!=high` → `qwen3:8b` (local)  
  `≤3000` → `gpt-5-mini` (cloud)  
  `>3000` ou `high` → `gpt-5-high` (cloud)
Se confiança baixa ou risco de segurança/compilação, **promover** modelo.

## Economia de tokens
- **Prompt Caching** para system/prefixos.  
- **LLMLingua** antes de cloud em textos longos.  
- Não reenviar blocos idênticos.

## MCPs disponíveis (uso criterioso)
filesystem, ripgrep, github, task_master_ai, playwright, tavily, context7, memory, sequentialthinking, testsprite.  
Timeout 10 s; retries exponenciais (máx. 3); `idempotency_key` estável.

## Contrato de saída
Cabeçalho: `[route:{local|cloud}] [model:{id}] [task:{code|docs}] [complexity:{low|medium|high}]`  
**code**: sumário curto → blocos `sudo tee <<'EOF' … EOF` por arquivo → teste mínimo → passos de verificação.  
**docs**: Markdown claro com títulos/listas/tabelas; citar PRD/AGENTS/README quando útil.

## Procedimento por solicitação
1) Se contexto não em memória → **BOOT**  
2) Classificar → imprimir JSON  
3) Escolher modelo  
4) Planejar em 3–6 bullets e listar MCPs  
5) Executar MCP com parcimônia  
6) Entregar no formato do contrato  
7) Sugerir próximo passo curto

## Segurança
Segredos: `/srv-2/secrets/ai-stack/ai-stack.env`. HTTP tool com allow-list; bloquear RFC1918; HMAC em webhooks; respeitar RBAC; sem PII em logs.
