# AGENTS.md — Playbook Codex CLI + MCP para CI (GitHub Actions)

> Objetivo: tornar o Codex CLI cirúrgico na abertura, execução e depuração do workflow **CI Smoke**.  
> Escopo: GitHub Actions, `gh` CLI, MCP servers (`filesystem`, `ripgrep`, `github`, `task_master_ai`), k6.

---

## Contexto do projeto

- Repo: `zapprosite/ai-router` (path local: `/srv/projects/ai-router`)
- Branch padrão: `main`
- Secrets: `/srv-2/secrets/ai-stack/ai-stack.env`  
  *Nunca copiar segredos; apenas referenciar caminhos.*
- Workflow alvo: `.github/workflows/ci_smoke.yml`
- Job exigido: **CI Smoke**  
- Portas/rotas do app: `GET /healthz`, `GET /v1/models` (porta 8082)

## Regras de operação

- **idempotency_key** no topo de arquivos novos/alterados.
- Sem PII em logs. **Nunca** imprimir chaves.
- `timeout=10s`, `retries=3` exponenciais para chamadas de ferramenta.
- Subir artefatos **sempre** (`if: always()`) antes de qualquer “gate”.

## CI Smoke networking

<!-- idempotency_key: agents-ci-smoke-2025-10-22-v1 -->

- Regra: em GitHub Actions, execute cargas (k6, curl auxiliares) dentro da **rede do Docker Compose**, usando o hostname do serviço. Ex.: `--network "$NET"` e `BASE_URL=http://ai-router:8082`.
- Proibido: `--network host` no runner. É frágil e varia por ambiente.
- Descobrir a rede do compose:
  ```bash
  CID=$(docker compose -f docker-compose.yml ps -q ai-router)
  NET=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' "$CID")
  ```
- Executar k6 na rede do compose e exportar resumo JSON:
  ```bash
  docker run --rm --network "$NET" \
    -e BASE_URL=http://ai-router:8082 \
    -v "$GITHUB_WORKSPACE/tests:/scripts:ro" \
    -v "$RUNNER_TEMP:/out" \
    grafana/k6 run --summary-export /out/k6_models.json /scripts/k6_models.js
  ```

Checklist de debug:
- `curl` dentro da rede do compose: `docker run --rm --network "$NET" curlimages/curl:8.10.1 -fsS http://ai-router:8082/healthz`.
- Logs: `docker compose logs` e `docker logs $(docker compose ps -q ai-router)`; sempre subir como artefatos.
- p95 fallback: se `k6_models.json` ausente/vazio, extrair de `k6_stdout.log` via regex `p(95)=<val><unit>` (normalizar µs→ms).

## Inventário MCP esperado

- `filesystem` (leitura/escrita de arquivos)
- `ripgrep` (busca estrutural)
- `github` (PR, branch, disparos e leitura de runs)
- `task_master_ai` (planejamento quando necessário)

---

## Fluxo padrão de debug de CI

1) **Validar workflow e triggers**
```bash
rg -n '^name:\s*CI Smoke$|^on:\s*$|workflow_dispatch' .github/workflows/ci_smoke.yml
Se faltar workflow_dispatch, adicione:

yaml
￼Copiar código
on:
  workflow_dispatch: {}
  push:
    branches: [ main ]
  pull_request: {}
Referência: eventos e workflow_dispatch. 
Grafana Labs

Disparar o workflow fixando o ref

bash
￼Copiar código
REPO="zapprosite/ai-router"
gh workflow run -R "$REPO" ".github/workflows/ci_smoke.yml" -r main
-r/--ref evita 422 quando o arquivo existe em main mas foi alterado em PR. 
GitHub

Acompanhar execução e obter RUN_ID

bash
￼Copiar código
RUN_ID="$(gh run list -R "$REPO" --workflow=ci_smoke.yml -L 1 --json databaseId -q '.[0].databaseId')"
gh run watch -R "$REPO" --exit-status "$RUN_ID"
Ver sintaxe suportada pelo gh run view/list. 
npm.io

Baixar artefatos e extrair p95

bash
￼Copiar código
OUT="/tmp/ai-router-ci.$RANDOM"; mkdir -p "$OUT"
gh run download -R "$REPO" "$RUN_ID" --name smoke-artifacts --dir "$OUT"
jq -r '.metrics.http_req_duration.values["p(95)"]' "$OUT"/**/k6_models.json || true
# fallback quando o JSON não existir:
grep -E 'http_req_duration|ep:models' "$OUT"/**/k6_stdout.log | sed -n '1,120p' || true
Sobre upload-artifact@v4 e retenção: if: always(), if-no-files-found: warn, retention-days.
Export do k6: --summary-export gera JSON com métricas.

Gate local (opcional)

bash
￼Copiar código
P95="$(jq -r '.metrics.http_req_duration.values["p(95)"]' "$OUT"/**/k6_models.json 2>/dev/null)"
[ -n "$P95" ] && awk -v v="$P95" 'BEGIN{ if (v+0<1200) exit 0; else exit 1 }'
Teardown manual, se o runner deixou recursos

bash
￼Copiar código
docker compose -f docker-compose.yml down -v || true
Erros comuns e correções rápidas
422: Workflow does not have workflow_dispatch trigger
Causas: ausência de workflow_dispatch no YAML ou trigger em branch diferente. Soluções:
a) Adicionar workflow_dispatch e commitar em main. b) Rodar com -r main. 
Grafana Labs
+1

Action de k6 “não encontrada”
Use grafana/setup-k6-action@v1. Se indisponível, instale k6 via APT no runner.

Artefatos ausentes
Mantenha Upload artifacts com if: always(). Suba logs (compose.log, router.log, k6_stdout.log) e JSON (k6_models.json).

gh api -I inválido
O flag correto para incluir cabeçalhos é -i. 
npm.io

PAT sem escopo workflow
Edite o token para incluir workflow além de repo quando push/alterar workflows. 
Grafana Labs

Prompt cirúrgico para Codex CLI (/mcp)
Cole no Codex CLI quando quiser abrir/validar o CI, baixar artefatos e reportar p95.

yaml
￼Copiar código
/mcp
# idempotency_key: ci-smoke-orchestrate-2025-10-21
CONTEXT:
- repo: zapprosite/ai-router
- workflow: .github/workflows/ci_smoke.yml
- required_job: "CI Smoke"
- artifacts: smoke-artifacts (k6_models.json, k6_stdout.log, healthz.json, models.json, compose.log, router.log)

GOAL:
1) Verificar se o YAML contém workflow_dispatch e name: CI Smoke.
2) Disparar o workflow com --ref main.
3) Aguardar conclusão e baixar artefatos.
4) Extrair p95 de k6_models.json; se ausente, extrair de k6_stdout.log.
5) Publicar resumo com p95 e links do run.

TOOLS:
- ripgrep.search para validar conteúdo do YAML
- github.* para listar runs e baixar artefatos
- filesystem.* para escrever relatório local

OUTPUT:
- resumo JSON: { run_url, p95_ms, artifacts_present, notes }
Apêndice: snippets confirmados
workflow_dispatch e eventos: GitHub Docs. 
Grafana Labs

Disparo com --ref: GH CLI docs. 
GitHub

upload-artifact@v4: opções e retenção.

k6 --summary-export: referência oficial.


---

## CI & Debug (MCP · Task Master · 2025-10-22)

- Classificar tarefas:
  - **Smoke**: valida `/healthz` e `/v1/models` e p95; **não** requer segredos.
  - **E2E Cloud**: só se houver segredos; materializar `.env` em `/srv-2/secrets/ai-stack/ai-stack.env`.

- Regras:
  - `env_file` permanece fixo; **nunca** imprimir valores de secrets.
  - Artefatos obrigatórios: `k6_models.json`, `k6_stdout.log`, `healthz.json`, `models.json`, `compose.log`, `router.log`, `compose_ps.txt`.
  - Gate: `http_req_duration{ep:models} p95 < 1200 ms`. Se `k6_models.json` ausente, usar fallback do `k6_stdout.log`.
  - Retentativas padrão de ferramentas MCP: `timeout=10s`, `retries=3`, `idempotency_key`.

- Prompts úteis (Codex CLI):
  1) “Listar workflows e disparar Smoke no main com watch e download de artefatos.”
  2) “Extrair p95 do k6 com fallback e comentar no PR.”
  3) “Se falhar p95, coletar logs e sugerir mitigação (CPU quota, gunicorn workers, cache HTTPX).”
