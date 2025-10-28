# AGENTS — Contrato Operacional

Objetivo
- Manter o AI Router estável (local‑first), econômico e previsível, com fallback Tier‑2 apenas quando o SLA exigir.

Papéis
- Orchestrator: quebra metas em passos verificáveis.
- Coder: produz diffs mínimos com testes; não toca segredos/systemd/ports.
- Doc Writer: atualiza documentação após VERIFY.
- Judge: verifica critérios de aceite/rollback.

Permissões
- Pode: ler/escrever em `app/`, `graph/`, `providers/`, `public/`, `docs/`, `tests/`.
- Não pode: alterar `config/.env.local`, units systemd, portas, docker ou chaves. Não reintroduzir Qwen.
- Mudanças de roteamento/políticas exigem label `ops-approve` + 2 owners.

Critérios de merge
- `pytest -q` ok (se houver), `make smoke` ok, `scripts/TEST_MODELS.py` ok (se cloud ON).
- `make evals` igual ou acima do baseline, sem regressão de latência p95.

Checklist de execução (JSONL)
```
{"ts":"...","step":12,"agent":"Orchestrator","goal":"Fase 3 — Router & modelos",
 "cmd":"...","status":"started|ok|err","verify":{"cmd":"...","expected":"..."}}
```

Boas práticas obrigatórias
- Ler: README.md, docs/ARCHITECTURE.md, docs/LOCAL_USAGE.md, docs/EVALS.md,
  docs/FRONTEND_INTEGRATION.md, docs/SECRETS_STANDARD.md, docs/AGENTS.md,
  docs/PRD_TASK_MASTER.md (se presente).
- Respeitar guard‑rails: não alterar portas (8082/8083), systemd, docker, segredos.
- Makefile: receitas com TAB real; sem CRLF. Se alterar o help, rode `make panel-json` e `make panel-refresh`.
- OpenAI: só enviar `reasoning_effort` para `gpt-5` quando `OPENAI_REASONING_EFFORT∈{low,medium,high}`; jamais para nano/mini/codex.

Painel `/guide`
- Mantém estilo/layout. Os botões numerados copiam SOMENTE o comando (`data-cmd`).
- Auto‑sync do painel lê `/public/guide_cmds.json`. Gere com `make panel-json` e valide com `make panel-refresh`.
