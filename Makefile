SHELL := /bin/bash

APP_DIR := /srv/projects/ai-router
VENV := $(APP_DIR)/.venv
ENVF := $(APP_DIR)/config/.env.local
SERVICE := ai-router
WARM_SERVICE := ai-router-warm
BACKUP_DIR := /srv/backups/ai-router
STAMP := $(shell date +%Y%m%d-%H%M%S)

# Rootless helpers (override via .env.make)
SUDO ?= sudo
-include .env.make

.PHONY: help
help:
	@echo "== AI Router — Atalhos =="
	@echo "  make venv           # cria venv e instala requirements.txt   #comentario_tutor: 1a vez / atualizar deps"
	@echo "  make env            # carrega ENV desta sessão               #comentario_tutor: não afeta outras shells"
	@echo "  make run            # sobe FastAPI (foreground em 8087)      #comentario_tutor: CONFLITA se service ativo"
	@echo "  make run-dev        # sobe FastAPI (reload) em 8087          #comentario_tutor: UNIFICADO (ideal p/ debug)"
	@echo "  make stop           # para o service systemd                 #comentario_tutor: libera 8087"
	@echo "  make free-8087      # força liberar porta 8087               #comentario_tutor: usa fuser/pkill"
	@echo "  make status         # status systemd                          #comentario_tutor: ver se está 'active (running)'"
	@echo "  make restart        # restart + healthz                       #comentario_tutor: reinicia serviço web"
	@echo "  make logs           # últimos logs                            #comentario_tutor: tail curto no journal"
	@echo "  make warm           # dispara warm-up                         #comentario_tutor: precompila e aquece cache"
	@echo "  make smoke          # smoke (texto+código)                    #comentario_tutor: valida roteador básico"
	@echo "  make test-nano      # OpenAI nano                             #comentario_tutor: requer fallback ON + chave"
	@echo "  make test-mini      # OpenAI mini                             #comentario_tutor: idem"
	@echo "  make test-codex     # OpenAI codex (Responses API)            #comentario_tutor: idem"
	@echo "  make test-high      # OpenAI gpt-5 (high)                     #comentario_tutor: idem"
	@echo "  make local-llama    # Llama local                             #comentario_tutor: GPU/CPU local"
	@echo "  make local-deepseek # DeepSeek local                          #comentario_tutor: GPU/CPU local"
	@echo "  make cloud-status   # mostra estado do fallback cloud         #comentario_tutor: ON/OFF e se há chave"
	@echo "  make cloud-on       # liga fallback cloud (não mexe na chave) #comentario_tutor: só ENABLE_OPENAI_FALLBACK=1"
	@echo "  make cloud-off      # desliga fallback cloud                  #comentario_tutor: ENABLE_OPENAI_FALLBACK=0 (custo zero)"
	@echo "  make backup-all     # backup completo                         #comentario_tutor: projeto+lock+.env.local+ollama blobs"
	@echo "  make restore-ollama # dica p/ restore de modelos ollama       #comentario_tutor: onde aplicar o tar"

.PHONY: venv
venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@. $(VENV)/bin/activate && pip install -r $(APP_DIR)/requirements.txt

.PHONY: env
env:
	@set -a; . $(ENVF); set +a; echo "OK: env carregado de $(ENVF)"

.PHONY: run
run:
	@set -a; . $(ENVF); set +a; . $(VENV)/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8087

.PHONY: run-dev
run-dev:
	@echo "#comentario_tutor: iniciando Uvicorn com --reload em 8087 (Unificado)"
	@set -a; . $(ENVF); set +a; . $(VENV)/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8087 --reload

.PHONY: pre-flight
pre-flight:
	@./scripts/PRE_FLIGHT_CHECK.sh

.PHONY: dev
dev: pre-flight run-dev

.PHONY: stop
stop:
	@$(SUDO) systemctl stop $(SERVICE) || true
	@echo "service parado"

.PHONY: free-8087
free-8087:
	@fuser -k 8087/tcp || true
	@pkill -f "uvicorn app.main:app.*8087" || true
	@echo "porta 8087 livre"

.PHONY: status
status:
	@systemctl status $(SERVICE) --no-pager || true

.PHONY: restart
restart:
	@$(SUDO) systemctl restart $(SERVICE)
	@sleep 1; curl -fsS http://localhost:8087/healthz && echo "healthz OK" || (echo "healthz FAIL" && exit 1)

.PHONY: logs
logs:
	@journalctl -u $(SERVICE) -n 200 --no-pager

.PHONY: warm
warm:
	@$(SUDO) systemctl start $(WARM_SERVICE).service || true

define _CURL
source $(ENVF) && curl -s http://localhost:8087/route -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d
endef

.PHONY: smoke
smoke:
	@./scripts/SMOKE_NOW.sh

.PHONY: test-nano
test-nano:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"gpt-4.1-nano"}' | python3 -m json.tool | sed -n '1,24p'

.PHONY: test-mini
test-mini:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"gpt-4o-mini"}' | python3 -m json.tool | sed -n '1,24p'

.PHONY: test-codex
test-codex:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"gpt-5.1-codex"}' | python3 -m json.tool | sed -n '1,40p'

.PHONY: test-high
test-high:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"gpt-5.1-high"}' | python3 -m json.tool | sed -n '1,24p'

.PHONY: local-llama
local-llama:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"hermes3:8b"}' | python3 -m json.tool | sed -n '1,24p'

.PHONY: local-deepseek
local-deepseek:
	@. $(ENVF) && curl -s http://localhost:8087/actions/test -H 'content-type: application/json' -H "X-API-Key: $${AI_ROUTER_API_KEY}" -d '{"model":"deepseek-coder-v2:16b"}' | python3 -m json.tool | sed -n '1,24p'

# ==== Cloud toggle sem reescrever segredos ====
define SET_ENV_KEY
@if grep -qE '^$(1)=' $(ENVF); then \
	sed -i 's/^$(1)=.*/$(1)=$(2)/' $(ENVF); \
else \
	printf "\n$(1)=$(2)\n" >> $(ENVF); \
fi
endef

.PHONY: cloud-status
cloud-status:
	@awk -F= 'BEGIN{off="(ausente)"} \
	  $$1=="ENABLE_OPENAI_FALLBACK"{f=$$2} \
	  $$1=="OPENAI_API_KEY_TIER2"{k=$$2} \
	  END{ \
	    m=(k==""?off:("****"substr(k,length(k)-3))); \
	    print "ENABLE_OPENAI_FALLBACK=" (f==""?"(não definido)":f); \
	    print "OPENAI_API_KEY_TIER2=" m ; }' $(ENVF)

.PHONY: cloud-on
cloud-on:
	@$(call SET_ENV_KEY,ENABLE_OPENAI_FALLBACK,1)
	@echo "#comentario_tutor: fallback ligado (usa a chave já presente em $(ENVF))"
	@$(SUDO) systemctl restart $(SERVICE)
	@sleep 1; curl -fsS http://localhost:8087/healthz && echo "healthz OK"

.PHONY: cloud-off
cloud-off:
	@$(call SET_ENV_KEY,ENABLE_OPENAI_FALLBACK,0)
	@echo "#comentario_tutor: fallback desligado (custo zero; mantém a chave no arquivo)"
	@$(SUDO) systemctl restart $(SERVICE)
	@sleep 1; curl -fsS http://localhost:8087/healthz && echo "healthz OK"

# ==== Backup & Restore ====
.PHONY: backup-all
backup-all:
	@mkdir -p $(BACKUP_DIR)/$(STAMP)
	@echo "# backup projeto (sem .venv/__pycache__)"; \
	tar --exclude='.venv' --exclude='__pycache__' -czf $(BACKUP_DIR)/$(STAMP)/project.tgz -C $(APP_DIR) .
	@echo "# deps lock"; \
	. $(VENV)/bin/activate && pip freeze > $(BACKUP_DIR)/$(STAMP)/requirements.lock.txt || true
	@echo "# .env.local (600)"; \
	install -m 600 $(ENVF) $(BACKUP_DIR)/$(STAMP)/.env.local
	@echo "# modelos Ollama"; \
	tar -czf $(BACKUP_DIR)/$(STAMP)/ollama-models.tgz -C $$HOME .ollama/models
	@echo "OK -> $(BACKUP_DIR)/$(STAMP)"

.PHONY: restore-ollama
restore-ollama:
	@echo "# para restaurar modelos do Ollama:"
	@echo "tar -xzf /srv/backups/ai-router/<STAMP>/ollama-models.tgz -C ~"
	@echo "systemctl restart ollama || true"

.PHONY: init
init:
	@mkdir -p /srv-2/dev/ai-router-codex/{state,logs}
	@echo "OK: estado preparado em /srv-2/dev/ai-router-codex"

.PHONY: health
health:
	@tools/healthcheck.sh


.PHONY: resume
resume:
	@tools/resume.sh
.PHONY: evals
evals:
	@mkdir -p .reports
	@./scripts/EVALS_RUN.sh | tee .reports/evals.out || (echo "EVALS FAIL"; exit 1)


.PHONY: check-unused
	@vars=$$(awk -F= '/^[A-Z0-9_]+[[:space:]]*[:+]?=/{print $$1}' Makefile | sed 's/[[:space:]]*[:+]*$$//'); \
	for v in $$vars; do \
	  pattern='$$('"$$v"')'; \
	  grep -q -F "$$pattern" Makefile || echo "UNUSED: $$v"; \
	done; true
.PHONY: panel-json
panel-json:
	@. .venv/bin/activate && python3 scripts/extract_make_cmds.py

.PHONY: panel-refresh
panel-refresh: panel-json
	@curl -fsS http://localhost:8087/public/guide_cmds.json | jq length
	@echo "OK: painel atualizado"

# Sanity checks for Makefile formatting (tabs, LF)
.PHONY: check-tabs
check-tabs:
	@make -n help >/dev/null 2>&1 || (echo "FAIL: Makefile tabs/separators" && exit 1)
	@LC_ALL=C grep -q $'\r' Makefile && (echo 'FAIL: CRLF found' && exit 1) || echo 'OK: LF only'
	@echo "OK: tabs/targets look fine"

# Painel: lista minimalista, somente comandos (copiáveis) via data-cmd
## data-cmd: make venv
## data-cmd: make env
## data-cmd: make run-dev
## data-cmd: make smoke
## data-cmd: make evals
## data-cmd: curl -fsS http://localhost:8087/healthz
## data-cmd: curl -fsS http://localhost:8087/v1/models | jq '.data[].id'
## data-cmd: curl -s http://localhost:8087/route -H 'content-type: application/json' -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' | python3 -m json.tool | sed -n '1,24p'
## data-cmd: curl -s http://localhost:8087/route -H 'content-type: application/json' -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}' | python3 -m json.tool | sed -n '1,24p'
## data-cmd: scripts/LATENCY_PROBE.sh
## data-cmd: scripts/RUN_AUDIT_AND_TESTS.sh

.PHONY: guide-open
guide-open:
	@xdg-open http://localhost:8087/guide >/dev/null 2>&1 || echo "Abra: http://localhost:8087/guide"

.PHONY: docs-rewrite
docs-rewrite:
	@./scripts/CODEX_RUN_REWRITE_DOCS.sh

.PHONY: docs-verify
docs-verify:
	@echo "== Verificando comandos documentados (README.md + docs/*.md) vs Makefile =="
	@set -e; \
	refs=$$(awk '/^  make /{print}' README.md docs/*.md 2>/dev/null \
	 | cut -d'#' -f1 | sed 's/^ *//;s/ *$$//' | sort -u); \
	fail=0; \
	for r in $$refs; do \
		tgt=$$(printf "%s\n" "$$r" | awk '{print $$2}'); \
		[ -n "$$tgt" ] || continue; \
		if ! grep -qE "^$${tgt}:" Makefile; then \
			echo "FALTA alvo no Makefile p/ linha doc: '$$r'"; \
			fail=1; \
		fi; \
	done; \
	[ $$fail -eq 0 ] && echo "OK: todos os 'make <alvo>' documentados existem no Makefile."

.PHONY: test-continue
test-continue:
	@. $(VENV)/bin/activate && PYTHONPATH=$(PWD) python -m pytest -q tests/test_chat_completions.py

.PHONY: kill-8087
kill-8087:
	@p=$$(ss -ltnp 2>/dev/null | awk '/:8087 /{print $$7}' | sed -n 's/.*pid=\([0-9]*\).*/\1/p'); \
	[ -z "$$p" ] || (echo "Killing $$p" && kill -9 $$p) || true

.PHONY: check-continue-config
check-continue-config:
	python3 scripts/validate_continue_config.py
