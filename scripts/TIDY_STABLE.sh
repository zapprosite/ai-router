#!/usr/bin/env bash
set -euo pipefail
cd /srv/projects/ai-router

PY_BIN="${PY_BIN:-python3}"
command -v "$PY_BIN" >/dev/null || { echo "ERRO: python3 não encontrado no PATH"; exit 1; }

echo "==[TIDY] Auditoria inicial"
echo "PWD: $(pwd)"
"$PY_BIN" - <<'PY'
import importlib, pathlib, hashlib
def sha(p):
    try: return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]
    except: return "NA"
mods = {}
for m in ("app.main","graph.router"):
    try:
        mod = importlib.import_module(m)
        p = pathlib.Path(getattr(mod,"__file__","n/a")).resolve()
        print(f"{m}: {p}  sha16={sha(p)}")
    except Exception as e:
        print(f"{m}: ERROR {e}")
PY

echo "==[TIDY] Unificar requirements (manter ./requirements.txt como canônico)"
if [ -d requirements ]; then
  tar -czf requirements.backup.tgz requirements || true
  rm -rf requirements
  echo "removido: ./requirements (backup: requirements.backup.tgz)"
fi

echo "==[TIDY] Garantir symlinks de config canônica"
mkdir -p config
[ -f config/router_config.yaml ] || { echo "ERRO: config/router_config.yaml ausente"; exit 2; }
[ -L router_config.yaml ] || ln -sfn config/router_config.yaml router_config.yaml
[ -f config/router_policy.yaml ] && [ ! -L router_policy.yaml ] && ln -sfn config/router_policy.yaml router_policy.yaml || true

sha() { "$PY_BIN" - "$1" <<'PY'
import sys,hashlib, pathlib
p=pathlib.Path(sys.argv[1])
print(f"{p}  sha16="+(hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else 'NA'))
PY
}

echo "==[TIDY] SHAs"
sha app/main.py
sha graph/router.py
sha providers/openai_client.py
sha providers/ollama_client.py
sha config/router_config.yaml
sha requirements.txt
sha scripts/SMOKE_NOW.sh

echo "==[TIDY] Health + smoke curto (não falha se OFF)"
set +e
curl -fsS http://localhost:8082/healthz && echo || echo "WARN: /healthz off"
RESP=$(curl -sS http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}')
if [ -n "$RESP" ]; then
  echo "$RESP" | "$PY_BIN" -m json.tool | sed -n '1,40p'
else
  echo "INFO: /route não respondeu (server pode estar parado)"
fi
set -e

echo "==[TIDY] Tree final (curto)"
{ command -v tree >/dev/null \
  && tree -a -I '.git|.venv*|__pycache__|*.pyc|node_modules|.pytest_cache|.mypy_cache|.reports|k6_out|test-results|.cursor|.taskmaster|.local' \
  || find . -not -path './.git/*' -not -path './.venv*/*' -not -path './__pycache__/*' \
            -not -path './node_modules/*' -not -path './.pytest_cache/*' -not -path './.mypy_cache/*' \
            -not -path './.reports/*' -not -path './k6_out/*' -not -path './test-results/*' \
            -not -path './.cursor/*' -not -path './.taskmaster/*' -not -path './.local/*' -print | sort; } \
| sed -n '1,120p'
echo "==[TIDY] OK"
