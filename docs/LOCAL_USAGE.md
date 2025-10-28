# Uso local (ambiente, run, logs e health)

Este guia foca na operação diária em uma máquina local, mantendo local‑first e fallback de nuvem desligado por padrão.

## 1) Ambiente Python e modelos

```bash
cd /srv/projects/ai-router
make venv
```

Baixe os modelos no Ollama (daemon em `http://localhost:11434`):

```bash
ollama pull llama3.1:8b-instruct-q5_K_M
ollama pull deepseek-coder-v2:16b
```

## 2) .env.local (seguro) e sessão

Crie/edite `config/.env.local` (não versionado). Exemplo mínimo:

```
# modelos
OLLAMA_INSTRUCT_MODEL=llama3.1:8b-instruct-q5_K_M
OLLAMA_CODER_MODEL=deepseek-coder-v2:16b

# tuning seguro
OLLAMA_NUM_CTX=4096
OLLAMA_TEMPERATURE=0.15
OLLAMA_TOP_P=0.9
OLLAMA_REPEAT_PENALTY=1.05
OLLAMA_NUM_PREDICT_CHAT=64
OLLAMA_NUM_PREDICT_CODE=640
OLLAMA_KEEP_ALIVE=30m
```

Carregue na sessão atual:

```bash
. .venv/bin/activate && set -a; . config/.env.local; set +a
# opcional: make env (confirma leitura do arquivo)
make env
```

## 3) START/STOP (systemd) e dev (8083)

```bash
# status / restart / logs / warm
make status
make restart && curl -fsS http://localhost:8082/healthz
make logs
make warm

# parar o serviço e liberar 8082
make stop
make free-8082

# desenvolvimento com reload (sem conflitar com 8082)
make run-dev   # usa 8083
```

## 4) Smokes rápidos

```bash
make smoke          # texto + código via /route
make local-llama    # teste Llama local
make local-deepseek # teste DeepSeek local
```

Chamadas diretas:

```bash
# Texto curto → Llama
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' | python3 -m json.tool | sed -n '1,24p'

# Código (prefer_code=true) → DeepSeek
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],"prefer_code":true}' | python3 -m json.tool | sed -n '1,24p'
```

## 5) Painel e sincronização

- Painel: `http://localhost:8082/guide`.
- JSON do painel: `/public/guide_cmds.json`.
- Sincronizar comandos (Makefile → painel):

```bash
make panel-json
make panel-refresh
```
