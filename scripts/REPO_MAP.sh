#!/usr/bin/env bash
set -euo pipefail
cd /srv/projects/ai-router

echo "== REPO TREE (filtrado) =="
{ command -v tree >/dev/null \
  && tree -a -I '.git|.venv*|__pycache__|*.pyc|node_modules|.pytest_cache|.mypy_cache|.reports|k6_out|test-results|.cursor|.taskmaster|.local' \
  || find . -not -path './.git/*' -not -path './.venv*/*' -not -path './__pycache__/*' \
            -not -path './node_modules/*' -not -path './.pytest_cache/*' -not -path './.mypy_cache/*' \
            -not -path './.reports/*' -not -path './k6_out/*' -not -path './test-results/*' \
            -not -path './.cursor/*' -not -path './.taskmaster/*' -not -path './.local/*' -print | sort; }

echo
echo "== ARQUIVOS GRANDES (top 20) =="
du -ah . | sort -hr | head -n 20

echo
echo "== SYMLINKS =="
find . -type l -exec ls -l {} \;

echo
echo "== PYTHON TRACK: módulos do app (arquivos efetivos) =="
PY_BIN="${PY_BIN:-python3}"
"$PY_BIN" - <<'PY'
import importlib, pathlib, json
mods = ["app.main","graph.router","providers.openai_client","providers.ollama_client"]
out=[]
for m in mods:
    try:
        mod = importlib.import_module(m)
        f = pathlib.Path(getattr(mod,"__file__","")).resolve()
        out.append({"module":m, "file": str(f)})
    except Exception as e:
        out.append({"module":m, "error":str(e)})
print(json.dumps(out, indent=2))
PY

echo
echo "== CONFIG ATIVA (router_config.yaml) =="
grep -n '.' config/router_config.yaml || true

echo
echo "== POSSÍVEIS SOBRAS (sem .py e sem doc/composer/scripts) =="
# lista itens fora de app|graph|providers|config|scripts|docs|.github|Dockerfile|compose|README|requirements
find . -maxdepth 2 -mindepth 1 -type f \
  | egrep -v '^./(app|graph|providers|config|scripts|docs|.github)/' \
  | egrep -v '(^./(Dockerfile|docker-compose\.yml|README\.md|requirements\.txt|router_config\.yaml|router_policy\.yaml|repo_tree\.txt|requirements\.backup\.tgz)$)' \
  || true
echo "== FIM =="
