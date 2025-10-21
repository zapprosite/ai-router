# Task Master MCP — PRD
Data de referência: 21/10/2025

## Índice
1. Visão e objetivos
2. Personas e JTBD
3. User stories prioritárias
4. Casos de uso e fluxos
5. Requisitos funcionais
6. Requisitos não funcionais
7. Arquitetura de referência (OSS)
8. MCP: desenho e uso
9. Modelo de dados
10. Design de API (REST/GraphQL)
11. Automações (if/then)
12. Segurança e compliance
13. UX e acessibilidade
14. Métricas e analytics
15. Planos e preços
16. Roadmap
17. Riscos e mitigação
18. Licenças e governança OSS
19. Critérios de aceite
20. Anexos

---

## 1) Visão e objetivos
**Visão:** plataforma SaaS multi-tenant de gestão de tarefas e projetos com Kanban, calendários, sprints e time tracking, acoplada a automações seguras via **MCP**, assistente de IA e conectores sem lock-in.

**OKRs (H1):**
- **O1 Crescimento:** 150 contas ativas (5–200 usuários) com NPS ≥ 45. *KRs:* taxa de ativação ≥ 60%, WAU/MAU ≥ 45%.
- **O2 Eficiência:** custo médio por tarefa gerada por automação ≤ US$0,002 e p95 latência API ≤ 300 ms. *KRs:* cache de prompt ≥ 40% de requests, compressão média ≥ 2×.
- **O3 Valor de produto:** 30% das tarefas criadas via automações MCP e 50% dos tickets com SLA cumprido. *KRs:* ≥ 10 receitas de automação “1-clique”.

## 2) Personas e JTBD
- **PM:** prioriza backlog, define sprints e automações. *JTBD:* “Quando recebo sinais do GitHub e Slack, quero tarefas e alerts sem fricção.”
- **Engenheiro:** executa tarefas, comenta, vincula PRs. *JTBD:* “Quero contexto mínimo e links corretos.”
- **Suporte:** trata tickets com SLA e respostas padronizadas. *JTBD:* “Quero triagem automática, tags e escalonamento.”
- **Executivo:** acompanha entregas e saúde de times. *JTBD:* “Quero métricas de throughput, lead/cycle time.”

## 3) User stories prioritárias
1. **Como PM**, importo backlog CSV/Jira e **vejo cards prontos**.  
   *Critérios* (Given/When/Then): Given arquivo CSV válido; When faço upload; Then tarefas criadas com campos mapeados.
2. **Como Engenheiro**, **crio subtarefas por IA** a partir de uma descrição.  
   Given tarefa com descrição; When peço “gerar subtarefas”; Then subtarefas com estimativas e links.
3. **Como Suporte**, **defino SLA** por fila.  
   Given fila “P1”; When crio regra 4h úteis; Then cards mostram contagem regressiva e violação.
4. **Como PM**, **automatizo GitHub→tarefa**.  
   Given PR “opened”; When regra ativa; Then tarefa criada com link e rótulos.
5. **Como Executivo**, **recebo weekly digest no e-mail/Slack**.  
   Given segunda 9h; When dispara automação; Then resumo com métricas chave.

## 4) Casos de uso e fluxos
- **CRUD de tarefa:** criar/editar/arquivar; estados *backlog, todo, doing, in_review, done, blocked*.  
- **Sprint planning:** selecionar tarefas por epic/tag, capacidade do time, rollover automático.  
- **Automações MCP (se/então):** triggers (webhooks MCP GitHub/Slack/Email/HTTP/cron); ações (criar tarefa, comentar, notificar, atualizar SLA, chamar HTTP).  
- **Notificações omnicanal:** Slack, e-mail, in-app; preferências por usuário.

## 5) Requisitos funcionais
**Campos de tarefa:** `title, description, state, priority, assignees[], reporter, epic_id, sprint_id, due_at, estimate, tags[], sla_policy_id, deps[], watchers[], attachments[]`.  
**SLA:** políticas por fila/tag; cálculos em horas úteis (fuso do projeto).  
**Busca e filtros:** texto, tags, estado, responsável, data, epic, sprint; páginação; ordenação.  
**Comentários e @mentions:** rich-text, checklist, code blocks, smart-links (PRs, commits).  
**Anexos:** upload para MinIO, vírus-scan opcional.  
**Dependências:** bloqueia *move to done* se dependente aberto.  
**Watchers:** inscrição automática por `assignee`, `reporter`, `mention`.  
**Importadores:** CSV, Jira (chaves mapeáveis).  
**API pública:** REST e GraphQL; OAuth2/OIDC; chaves de projeto.  
**Assistente de IA:** sumarização, etiquetagem, priorização, geração de subtarefas.  
**Automations builder:** UI “if/then”, prévias, simulação.

## 6) Requisitos não funcionais
- **SLO:** p95 API ≤ 300 ms; uptime 99,9%; cold start Web < 2 s.  
- **A11y:** WCAG 2.1 AA.  
- **i18n:** pt-BR e en-US.  
- **Privacidade:** LGPD/GDPR, DPA, DSR.  
- **Auditoria:** trilhas por usuário/tenant; retenção configurável.  
- **Criptografia:** TLS 1.2+ e AES-256 at-rest.

## 7) Arquitetura de referência (OSS)
- **Frontend:** Next.js 14 (React 18), TanStack Query, Tailwind, Radix UI, i18n.  
- **App server:** Node.js **NestJS** (alt: FastAPI/Go Fiber).  
- **ORM/DB:** PostgreSQL + Prisma; **Redis** para cache/sessão.  
- **Busca:** OpenSearch ou Meilisearch.  
- **Fila/Eventos:** Kafka ou NATS.  
- **Workflows:** Temporal para automações e SLA timers.  
- **Arquivos:** MinIO.  
- **Auth/SSO:** Keycloak (OIDC/OAuth2), RBAC por papel/projeto.  
- **API:** REST + GraphQL; OpenAPI 3.1.  
- **Realtime:** WebSockets/Socket.IO.  
- **Observabilidade:** OpenTelemetry, Prometheus, Grafana; logs estruturados.  
- **Infra:** Docker, Kubernetes, Helm, Argo CD, Terraform; secrets SOPS/Vault.  
- **CI/CD:** GitHub Actions (build, test, SCA, SBOM, canário).  
- **Feature flags:** OpenFeature/flagd. :contentReference[oaicite:1]{index=1}  
- **Testes:** unit, integração, **k6** (carga), **OWASP ZAP** (DAST).

## 8) MCP: desenho e uso
**Alvos:** GitHub, Slack, Google Drive, Email, Filesystem, HTTP, Postgres.  
**Servidores MCP OSS:** usar repositórios oficiais/comunidade quando disponíveis; registrar no host com credenciais por tenant. :contentReference[oaicite:2]{index=2}

**Ferramentas (contratos):**
- `github.create_task_link(issue|pr) → {url, repo, number}`  
- `slack.notify(channel, text, thread_ts?) → {ts}`  
- `drive.attach(file_url|id, task_id) → {attachment_id}`  
- `email.send(to[], subject, html, attachments[]) → {message_id}`  
- `http.request(method, url, headers{}, body?) → {status, headers, body}`  
- `pg.query(conn_alias, sql, params[]) → {rows[], fields[]}`

**Políticas:** timeouts padrão 10 s; retries exponenciais (max 3); idempotência por `request_id`; auditoria de `tool_call` por tenant/projeto; permissões por escopo (org, projeto) e *sandbox* com quotas e rate limits.

**Suporte MCP remoto na API Responses:** centralizar integrações via host compatível. :contentReference[oaicite:3]{index=3}

## 9) Modelo de dados (tabelas resumidas)
- **Organization**(id, name, plan, created_at)  
- **User**(id, org_id, email, name, locale, role) [idx: org_id]  
- **Project**(id, org_id, key, name) [idx: org_id,key]  
- **Board**(id, project_id, name, view_type)  
- **Sprint**(id, project_id, name, start_at, end_at, capacity)  
- **Epic**(id, project_id, title, status)  
- **Task**(id, project_id, epic_id?, sprint_id?, title, description, state, priority, assignees[], reporter, due_at, estimate, sla_policy_id?) [idx: project_id,state,assignees gin]  
- **Comment**(id, task_id, author_id, body, created_at)  
- **Attachment**(id, task_id, url, mime, size)  
- **Tag**(id, org_id, key, name, color)  
- **TaskTag**(task_id, tag_id)  
- **Automation**(id, project_id, name, trigger, condition, action, enabled)  
- **Notification**(id, user_id, chan, payload, status)  
- **AuditLog**(id, org_id, actor_id, action, entity, entity_id, data, at)

## 10) Design de API
**REST principais (exemplos):**
- `POST /v1/tasks` → cria tarefa  
- `GET /v1/tasks?project_id=...&state=doing`  
- `POST /v1/automations` → cria regra  
- `POST /v1/mcp/tools/{tool}/call` → proxy autorizado

**Exemplo payload `POST /v1/tasks`:**
```json
{
  "project_id": "p_123",
  "title": "Adicionar validação de SLA",
  "description": "…",
  "assignees": ["u_45"],
  "tags": ["SLA","backend"],
  "due_at": "2025-10-30T23:59:00Z"
}
GraphQL (SDL recorte):

graphql
￼Copiar código
type Task {
  id: ID!
  projectId: ID!
  title: String!
  description: String
  state: TaskState!
  priority: Int
  assignees: [User!]!
  epicId: ID
  sprintId: ID
  dueAt: DateTime
  estimate: Int
  tags: [Tag!]!
}

type Project { id: ID!, key: String!, name: String! }

type Mutation {
  createAutomation(input: AutomationInput!): Automation!
}
11) Automações (if/then)
Receitas exemplo:

Quando PR abre no GitHub, criar tarefa.

Quando prazo vence, alertar Slack (@assignee).

Quando label “bug” chegar via email/IMAP, criar ticket com SLA P1.

Quando tarefa entra em “in_review”, postar no canal #code-review.

Quando comentário contém “/assign @user”, atribuir.

Pseudo-YAML (5 regras):

yaml
￼Copiar código
- name: pr_open_create_task
  trigger: github.pr_opened
  action: tasks.create
  mapping: {title: "PR: {{pr.title}}", description: "{{pr.url}}", tags: ["github","pr"]}

- name: due_alert_slack
  trigger: scheduler.cron("*/5 * * * *")
  condition: now() > task.due_at - "1h" and task.state != "done"
  action: slack.notify(@assignees, "Vence em 1h: {{task.title}}")

- name: email_bug_p1
  trigger: email.inbox(match: "subject:/\\bbug\\b/i")
  action: tasks.create_with_sla("P1_4h")

- name: review_channel
  trigger: task.state_changed(to: "in_review")
  action: slack.notify("#code-review", "Revisar: {{task.link}}")

- name: assign_command
  trigger: comment.created(match: "^/assign\\s+@(?P<user>\\w+)")
  action: tasks.assign("${user}")
12) Segurança e compliance
OWASP ASVS; CSP estrita; SSRF mitigado no proxy HTTP; webhooks com assinatura HMAC; rotação de chaves; logs de acesso; DPA; DSR.

Permissões MCP por escopo (org/projeto); segregação de dados multi-tenant.

13) UX e acessibilidade
Atalhos teclado; drag-and-drop; tema claro/escuro; perfis de cor; cards com smart-links (PR, issue, doc).

14) Métricas
Ativação, DAU/WAU, tarefas concluídas/usuário, lead time, cycle time, uso de automações, erro p95.

15) Planos e preços (placeholder)
Free: 3 projetos, 5k tarefas.

Pro: SSO, automações avançadas, busca.

Enterprise: SCIM, auditoria, data residency.

16) Roadmap
M1–2: núcleo tarefas + auth + MCP Slack/GitHub.

M3–4: sprints, busca, automações; PWA.

M5–6: GraphQL público, audit log, enterprise.

17) Riscos e mitigação
APIs externas/limites: filas com backoff, circuit-breaker.

Custo de busca: tune de índices, retenção.

Workflows complexos: Temporal + replays e testes.

Segurança MCP: allow-list de ferramentas, escopos mínimos.

18) Licenças e governança OSS
Preferir MIT/Apache-2.0; evitar AGPL no core servidor; SBOM; política de terceiros.

19) Critérios de aceite do PRD
Consistência, completude, traço com stories, APIs exemplificadas, riscos mapeados.

20) Anexos
20.1 Estratégia de roteamento LLM p/ Assistente
Detecção code/docs via Structured Outputs (JSON Schema) para classificar task_type ∈ {code, docs} e complexity ∈ {low, medium, high}. Desativar parallel tool calls quando exigir conformidade estrita ao schema. 
OpenAI

Custo-qualidade: roteamento RouteLLM com threshold calibrado para enviar prompts simples ao Qwen3-8B local e complexos ao “gpt-5-high”/equivalente; ganhos reportados ~80–85% de redução mantendo ~90–95% da qualidade GPT-4 no MT-Bench. 
GitHub
+2
Shekhar Gulati
+2

CARROT (2025): alternativa teórica ciente de custo/accuracy. 
paperswithcode.com

Servir modelos locais: vLLM com batching contínuo, PagedAttention, quantizações INT4/8/FP8; OpenAI-compatible server. 
GitHub

Economia de tokens: Prompt Caching automático p/ prefixos ≥ 1.024 tokens; 50% desconto em tokens cacheados; ideal para system prompts e contextos repetidos. 
OpenAI

Compressão de prompt: LLMLingua/LongLLMLingua para reduzir 2–20× com perda mínima, antes do envio ao LLM. 
GitHub
+1

Heurísticas adicionais: tamanho (approx_tokens ≈ chars/4), presença de trechos de código, n-gramas técnicos; fallback para “juiz” reavaliar e reencaminhar. 
OpenAI Help Center

20.2 Checklist de prontidão para build
￼ OpenAPI 3.1 gerado e validado

￼ RBAC Keycloak por projeto

￼ Mínimo 10 receitas MCP testadas end-to-end

￼ Observabilidade OTel + dashboards Grafana

￼ Testes k6 ≥ 500 RPS p95 ≤ 300 ms

￼ DAST ZAP sem achados críticos

￼ Backups PostgreSQL + recuperação testada

￼ Flags de features via OpenFeature/flagd em produção. 
Flagd


## 21) Fases 1–60 (MCP-first, do zero ao GA)

1. Kickoff do produto e alinhamento MCP-first.  
2. Definir OKRs e métricas base.  
3. Mapear personas e JTBD finais.  
4. Fixar escopo MVP e anti-escopo.  
5. Definir modelo multi-tenant e RBAC.  
6. Especificar entidades e índices críticos.  
7. Padronizar naming e convenções (docs/código).  
8. Preparar repositório e estrutura inicial.  
9. Implantar Keycloak e papéis padrão.  
10. Configurar Postgres com RLS por org.  
11. Subir MinIO e políticas de bucket.  
12. Provisionar Redis para sessão e rate-limit.  
13. Subir Meilisearch/OpenSearch com índice “tasks”.  
14. Criar serviço NestJS (ou alternativa) base.  
15. Implementar CRUD de Task/Epic/Sprint.  
16. Implementar Comments, Mentions, Watchers.  
17. Implementar Uploads e antivírus opcional.  
18. Implementar SLA engine mínimo (timers).  
19. Implementar Search API com filtros.  
20. Entregar Kanban básico no Next.js.  
21. Entregar Calendário e Due dates.  
22. Entregar Sprint planning e capacidade.  
23. Entregar Time tracking simples.  
24. Entregar Importadores CSV/Jira.  
25. Publicar OpenAPI 3.1 e SDK stub.  
26. Expor GraphQL inicial (Task/Project).  
27. Habilitar WebSockets para realtime.  
28. Instrumentar OTel + Prometheus.  
29. Dashboards Grafana iniciais.  
30. Logs estruturados e correlação.  
31. Subir NATS/Kafka para eventos.  
32. Orquestrar automações com Temporal.  
33. MCP Filesystem e HTTP tools seguros.  
34. MCP GitHub (webhooks, issues/PR link).  
35. MCP Slack (notificar/sumarizar thread).  
36. MCP Email (send/receive com filtros).  
37. MCP Drive (upload/attach/share).  
38. MCP Postgres (queries com templates).  
39. Builder de automações If/Then (UI).  
40. Biblioteca de receitas pronta (5+).  
41. Assistente IA: resumo/etiquetas.  
42. Assistente IA: gerar subtarefas.  
43. Roteador LLM custo→qualidade (local Qwen3, cloud gpt-5).  
44. Structured Outputs para classificar code/docs e complexidade.  
45. Prompt Caching em prefixos e policies.  
46. Compressão LLMLingua em chamadas cloud longas.  
47. Rate-limits e quotas por plano.  
48. Auditoria de tool_calls e acesso.  
49. Políticas de segurança (CSP, SSRF, HMAC).  
50. DPA/DSR e retenção de dados.  
51. Testes unitários e integração (80%+ core).  
52. Carga k6 p95≤300ms e erro≤0,5%.  
53. DAST OWASP ZAP sem High.  
54. PWA mobile e offline básico.  
55. Feature flags com OpenFeature/flagd.  
56. CI/CD GitHub Actions + SBOM.  
57. Beta privado: 5–10 orgs.  
58. Hardening e tuning de custos.  
59. Pricing Free/Pro/Enterprise e limites.  
60. GA: migração, comunicação e runbooks.


## 22) Anexos consolidados

### 22.1 Modelo de dados (tabelado)
| Entidade | Campos chave | Índices/FKs |
|---|---|---|
| Organization | id, name, plan, created_at | PK(id) |
| User | id, org_id, email, name, locale, role | PK(id), FK(org_id), IDX(org_id), UNIQUE(org_id,email) |
| Project | id, org_id, key, name | PK(id), FK(org_id), UNIQUE(org_id,key) |
| Board | id, project_id, name, view_type | PK(id), FK(project_id) |
| Sprint | id, project_id, name, start_at, end_at, capacity | PK(id), FK(project_id), IDX(project_id,start_at,end_at) |
| Epic | id, project_id, title, status | PK(id), FK(project_id), IDX(project_id,status) |
| Task | id, project_id, epic_id?, sprint_id?, title, description, state, priority, assignees[], reporter, due_at, estimate, sla_policy_id? | PK(id), FK(project_id,epic_id,sprint_id), GIN(assignees,tags), IDX(project_id,state,due_at) |
| Comment | id, task_id, author_id, body, created_at | PK(id), FK(task_id,author_id), IDX(task_id,created_at) |
| Attachment | id, task_id, url, mime, size | PK(id), FK(task_id), IDX(task_id) |
| Tag | id, org_id, key, name, color | PK(id), FK(org_id), UNIQUE(org_id,key) |
| TaskTag | task_id, tag_id | PK(task_id,tag_id), FK(task_id,tag_id) |
| Automation | id, project_id, name, trigger, condition, action, enabled | PK(id), FK(project_id), IDX(project_id,enabled) |
| Notification | id, user_id, chan, payload, status, created_at | PK(id), FK(user_id), IDX(user_id,status,created_at) |
| AuditLog | id, org_id, actor_id, action, entity, entity_id, data, at | PK(id), FK(org_id,actor_id), IDX(org_id,at), IDX(entity,entity_id) |

### 22.2 Endpoints REST (principais)
| Método | Caminho | Descrição |
|---|---|---|
| POST | /v1/tasks | Criar tarefa |
| GET | /v1/tasks | Listar + filtros (project_id, state, assignee, tag, due_at) |
| GET | /v1/tasks/{id} | Detalhar tarefa |
| PATCH | /v1/tasks/{id} | Atualizar campos |
| POST | /v1/tasks/{id}/comments | Comentar |
| POST | /v1/automations | Criar regra if/then |
| GET | /v1/automations | Listar regras |
| POST | /v1/mcp/tools/{tool}/call | Proxy MCP autorizado |
| GET | /v1/models | Model list (local+cloud) |
| POST | /v1/embeddings | Embeddings |
| GET | /healthz | Health check |

Exemplo `POST /v1/tasks`:
```json
{
  "project_id": "p_123",
  "title": "Adicionar validação de SLA",
  "description": "…",
  "assignees": ["u_45"],
  "tags": ["SLA","backend"],
  "due_at": "2025-10-30T23:59:00Z"
}
22.3 GraphQL (SDL recorte)
graphql
￼Copiar código
enum TaskState { BACKLOG TODO DOING IN_REVIEW DONE BLOCKED }

type User { id: ID!, name: String!, email: String! }
type Tag { id: ID!, key: String!, name: String!, color: String }
scalar DateTime

type Task {
  id: ID!
  projectId: ID!
  title: String!
  description: String
  state: TaskState!
  priority: Int
  assignees: [User!]!
  epicId: ID
  sprintId: ID
  dueAt: DateTime
  estimate: Int
  tags: [Tag!]!
}

type Project { id: ID!, key: String!, name: String! }

input AutomationInput { projectId: ID!, name: String!, trigger: String!, condition: String, action: String!, enabled: Boolean! }

type Automation { id: ID!, projectId: ID!, name: String!, enabled: Boolean! }

type Query {
  task(id: ID!): Task
  tasks(projectId: ID, state: TaskState, tag: String, assignee: ID): [Task!]!
}

type Mutation {
  createTask(projectId: ID!, title: String!, description: String): Task!
  createAutomation(input: AutomationInput!): Automation!
}
22.4 Automações MCP (pseudo-YAML, 5 receitas)
yaml
￼Copiar código
- name: pr_open_create_task
  trigger: github.pr_opened
  action: tasks.create
  mapping: {title: "PR: {{pr.title}}", description: "{{pr.url}}", tags: ["github","pr"]}

- name: due_alert_slack
  trigger: scheduler.cron("*/5 * * * *")
  condition: now() > task.due_at - "1h" and task.state != "DONE"
  action: slack.notify(@assignees, "Vence em 1h: {{task.title}}")

- name: email_bug_p1
  trigger: email.inbox(match: "subject:/\\bbug\\b/i")
  action: tasks.create_with_sla("P1_4h")

- name: review_channel
  trigger: task.state_changed(to: "IN_REVIEW")
  action: slack.notify("#code-review", "Revisar: {{task.link}}")

- name: assign_command
  trigger: comment.created(match: "^/assign\\s+@(?P<user>\\w+)")
  action: tasks.assign("${user}")
22.5 Plano de testes e SLOs
SLOs: uptime 99,9%; p95 API ≤ 300 ms; cold start Web < 2 s.
Testes:

Unitários: serviços e validadores (≥80% core).

Integração: CRUD tasks, comentários, automações MCP em sandbox.

Carga (k6): /healthz e /v1/models p95<300ms; /v1/tasks lista 200 RPS p95<300ms; erro<0,5%.

DAST (ZAP): 0 High.

Segurança: assinatura HMAC webhooks, SSRF deny RFC1918.

22.6 Matriz RACI (resumo)
Entrega	PM	Eng	DevOps/SRE	Security	CX	Exec
PRD & Roadmap	R	C	I	I	C	A
Backend APIs	C	R	C	I	I	I
Frontend & UX	R	R	I	I	C	I
MCP Connectors	C	R	C	C	I	I
Observabilidade	I	C	R	I	I	I
Segurança & Compliance	C	I	C	R	I	I
Release GA	A	R	R	C	C	A
￼
22.7 Riscos e mitigação
Risco	Impacto	Prob.	Mitigação
Limites de APIs externas	Alto	Médio	Fila + backoff + circuit-breaker; quotas por plano
Custo de busca/LLM	Médio	Médio	Cache, compressão, roteamento local-first
Complexidade de workflows	Médio	Médio	Temporal + testes de replays
Segurança MCP/webhooks	Alto	Baixo	HMAC, allow-list HTTP, RBAC mínimo
Vazamento de dados	Alto	Baixo	Criptografia, logs sem PII, auditoria e DLP
Latência p95 > 300ms	Médio	Médio	Indexação, tuning DB/cache, k6 contínuo
￼
22.8 Checklist de prontidão para build
￼ OpenAPI 3.1 publicada e validada

￼ RBAC Keycloak por projeto

￼ 10+ receitas MCP validadas end-to-end

￼ OTel + Prometheus + dashboards Grafana

￼ k6: p95 ≤ 300 ms nas rotas alvo

￼ ZAP: sem achados High

￼ Backups Postgres + restore testado

￼ Flags via OpenFeature/flagd em prod
