#!/usr/bin/env python3
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MK   = ROOT / "Makefile"
OUT  = ROOT / "public" / "guide_cmds.json"

# --- 1) Tenta extrair do `make help` ---
items = []
try:
    help_out = subprocess.check_output(["make","help"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
except Exception:
    help_out = ""

# padrão: linhas do help no formato `make alvo  # comentário`
pat = re.compile(r'^\s*make\s+([a-z0-9._-]+)\s+#\s*(.+?)\s*$', re.IGNORECASE|re.MULTILINE)
for m in pat.finditer(help_out):
    cmd = f"make {m.group(1)}"
    cmt = m.group(2)
    items.append({"cmd": cmd, "comment": cmt})

# --- 2) Fallback completo se vier pouca coisa ---
if len(items) < 10:
    defaults = [
        ("sudo bash -lc 'cd /srv/projects/ai-router; . .venv/bin/activate; set -a; . config/.env.local; set +a; exec bash -li'",
         "root+venv+env — abre shell já dentro do projeto (pronto p/ trabalhar)"),
        ("sudo -i",                    "virar root (modo administrativo)"),
        ("cd /srv/projects/ai-router", "entrar na pasta do projeto"),
        (". .venv/bin/activate && set -a; . config/.env.local; set +a",
         "ativar venv e carregar variáveis locais (só nesta janela)"),
        ("make venv",          "criar/atualizar ambiente via requirements.txt"),
        ("make env",           "carregar ENV desta sessão (idempotente)"),
        ("make run",           "subir FastAPI em 8082 (foreground) — conflita com service"),
        ("make run-dev",       "subir FastAPI em 8083 com --reload — debug, sem conflito"),
        ("make stop",          "parar service systemd (liberar 8082)"),
        ("make free-8082",     "forçar liberar porta 8082 (fuser/pkill)"),
        ("make status",        "status systemd (esperado: active/running)"),
        ("make restart",       "restart service + healthz"),
        ("make logs",          "últimos logs (journalctl tail curto)"),
        ("make warm",          "aquecimento (prepara cache/modelos)"),
        ("make smoke",         "smoke (texto + código) — valida roteador"),
        ("make test-nano",     "OpenAI nano (requer fallback ON + chave)"),
        ("make test-mini",     "OpenAI mini (requer fallback ON)"),
        ("make test-codex",    "OpenAI codex/Responses (requer fallback ON)"),
        ("make test-high",     "OpenAI gpt-5 (high) (requer fallback ON)"),
        ("make local-llama",   "Llama local (explicações/diálogo)"),
        ("make local-deepseek","DeepSeek local (código)"),
        ("make cloud-status",  "estado do fallback cloud + presença de chave"),
        ("make cloud-on",      "liga fallback cloud (não mexe na chave salva)"),
        ("make cloud-off",     "desliga fallback cloud (custo zero)"),
        ("make backup-all",    "backup completo (projeto+deps+.env+ollama blobs)"),
        ("make restore-ollama","instruções p/ restaurar modelos do Ollama"),
        ("scripts/BACKUP_DESKTOP.sh", "backup leve p/ Desktop (sem segredos)"),
        ("scripts/RECOVER_SAFE.sh",   "recuperação segura (reinicia e valida)"),
        ("curl -fsS http://localhost:8082/v1/models | jq '.data[].id'",
         "listar modelos expostos (compat. OpenAI)"),
        ("curl -s http://localhost:8082/route -H 'content-type: application/json' -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Explique HVAC em 1 frase.\"}]}' | python3 -m json.tool | sed -n '1,24p'",
         "exemplo de chamada (texto)"),
        ("curl -s http://localhost:8082/route -H 'content-type: application/json' -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Escreva uma função Python soma(n1,n2) com docstring.\"}],\"prefer_code\":true}' | python3 -m json.tool | sed -n '1,24p'",
         "exemplo de chamada (código)"),
        ("curl -fsS http://localhost:11434/api/tags | head",
         "listar modelos instalados no Ollama"),
        ("python -m uvicorn app.main:app --host 0.0.0.0 --port 8082",
         "subir API manual em 8082 (se o service estiver parado)"),
    ]
    items = [{"cmd": c, "comment": k} for (c,k) in defaults]

# --- 3) Numerar e salvar ---
out = {"terminal": [{"num": i+1, **it} for i,it in enumerate(items)]}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(f"Wrote {OUT} with {len(out['terminal'])} items")
