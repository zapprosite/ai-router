<!-- idempotency_key: prd-tm-local-smoke-2025-10-22-v2 -->
# PRD · Local Smoke & Debug

Escopo: validar o backend localmente (sem CI, sem internet) com foco em disponibilidade e latência básica do endpoint `/v1/models`, guiando coleta de evidências e documentação mínima.

## Fases e Critérios de Aceite (v2)

### A1 — Backend UP e Endpoints OK
- Backend escuta em `8082` via `docker-compose`.
- `GET /healthz` retorna `200` com corpo `{ "ok": true }` salvo em `healthz.json`.
- `GET /v1/models` retorna `200` com corpo contendo `data` (lista) salvo em `models.json`.
- Proibições: não alterar `app.py` nem `docker-compose.yml`; não imprimir segredos.
- Pré‑requisitos: ACL de leitura em `/srv-2/secrets/ai-stack/ai-stack.env`.

### A2 — k6 Models Gate
- Executar `tests/k6_models.js` via container `grafana/k6` contra o backend local.
- Métricas de aceite (p95 em ms; erro em %):
  - `http_req_duration{ep:models} p(95) < 1200` ms
  - `http_req_failed < 1%`
- Artefatos obrigatórios: `k6_models.json` (summary export) e `k6_stdout.log`.
- Fallback: se `k6_models.json` indisponível, extrair p95 do `k6_stdout.log` (normalizar µs→ms).

### A3 — Playbook documentado
- README possui seção “Local Smoke” com comandos:
  1) Ajuste de ACL do env_file
  2) `docker compose up` + curls de verificação
  3) Execução do k6 via container (host/compose network)
- `scripts/ci-smoke-run.sh` está descrito (opcional; não é necessário criá‑lo neste passo).

### Fases adicionais (síntese)
As fases abaixo são objetivos incrementais para consolidação do smoke local e preparação para CI. Priorize A1–A3 antes.

- A4 — Script local opcional `scripts/smoke-local.sh` com coleta automática.
- A5 — Normalizar cálculo de p95 (µs→ms) em fallback.
- A6 — Validação do schema de `models.json` (contém campo `data` array).
- A7 — Capturar versão do Docker e Compose em `runs/sysinfo.txt`.
- A8 — Limpeza: `docker compose down -v` opcional pós‑teste.
- A9 — Retentativa automática de curls (3x, timeout 10s) no script.
- A10 — Make target `make smoke-local` (wrapper de conveniência).
- A11 — Documentar troubleshooting de porta 8082 ocupada.
- A12 — Gate local automatizado `p95<1200ms` via `awk`.
- A13 — Exportar métrica `http_req_failed` para `runs/metrics.txt`.
- A14 — Estruturar pasta `runs/` com timestamp `runs/YYYYMMDD-HHMM/`.
- A15 — Ignorar `runs/` no `.gitignore` (a critério do time).
- A16 — Variável `BASE_URL` parametrizável no k6 local.
- A17 — Coleta de `docker inspect` do serviço em `runs/inspect.json`.
- A18 — Log de build (`docker compose build --progress=plain`) opcional.
- A19 — Verificação de ACL com `getfacl -p` salvando saída.
- A20 — Doc: proibir impressão de segredos (reforço em README/AGENTS).
- A21 — Script auxiliares para `jq` indisponível (sed/awk fallback).
- A22 — Padronizar `k6_out/k6_models.json` como destino do resumo.
- A23 — Validar existência de `tests/k6_models.js` antes de rodar.
- A24 — Adicionar tags de cenário no k6 (ep:models).
- A25 — Contar tentativas/erros no script e retornar código apropriado.
- A26 — Registrar `compose_ps.txt` para estado dos containers.
- A27 — Guardar `router.log` via `docker logs` do serviço.
- A28 — Capturar `compose.log` com `--no-color` para legibilidade.
- A29 — Validar `uvicorn` em logs (startup OK) antes de k6.
- A30 — Fallback de rede: rodar k6 em host ou rede do compose.
- A31 — Sinalizar sucesso/fracasso em `runs/status.json`.
- A32 — Encurtar tempo de warmup antes do k6 (sleep configurável).
- A33 — Parametrizar VUs/duration do k6 via env (leve).</n+- A34 — Incluir README snippet para Windows WSL notas rápidas.
- A35 — Checagem de disponibilidade de `jq`; instruir instalação.
- A36 — Verificar `docker context` atual e anotar em `sysinfo`.
- A37 — Doc: impedir alterações em `app.py`/`docker-compose.yml` nesta fase.
- A38 — Reforçar “um commit por mudança” no fluxo local.
- A39 — Mapear variáveis sensíveis e confirmar ausência em logs.
- A40 — Criar `runs/README.md` com formato dos artefatos.
- A41 — Atalho `make k6-host` e `make k6-compose` (opcional).
- A42 — Extrair p95 do `k6_stdout.log` por regex como fallback.
- A43 — Registrar latência média além do p95 (se disponível).
- A44 — Guardar tamanho de resposta de `/v1/models` (bytes).
- A45 — Documentar requisitos mínimos de CPU/RAM locais.
- A46 — Checagem do mapeamento `8082:8082` via `rg` automatizada.
- A47 — Checklist pré‑execução (Docker up, ACL ok, portas livres).
- A48 — Template de issue para smoke falho com campos de anexos.
- A49 — Planejar migração do smoke local para CI Smoke.
- A50 — Revisão periódica das metas de p95 e erro (<1%).

## Notas de Operação
- Segredos residem somente em `/srv-2/secrets/ai-stack/ai-stack.env`.
- Não mover nem copiar o `env_file`; apenas garantir leitura.
- Mudanças de código não fazem parte deste PRD — somente docs e scripts auxiliares.
