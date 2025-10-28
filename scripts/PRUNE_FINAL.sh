#!/usr/bin/env bash
set -euo pipefail
ROOT="/srv/projects/ai-router"
cd "$ROOT"

echo "[check] referências antes de podar…"
rg -n --hidden -g '!__pycache__' \
  -e '\.cursor|\.taskmaster|automations/|\.archive_|^\.local$|docker-compose\.ya?ml$' || true

# 1) remover symlinks de docker-compose na raiz (mantém apenas em docs/config/)
[ -L docker-compose.yml ] && rm -f docker-compose.yml
[ -L docker-compose.ollama.yml ] && rm -f docker-compose.ollama.yml

# 2) arquivos/diretórios de ferramenta local (só enfeite)
[ -d .cursor ]      && rm -rf .cursor
[ -d .taskmaster ]  && rm -rf .taskmaster
[ -d .local ]       && rm -rf .local

# 3) automations de exemplo (se não usa em pipeline)
[ -d automations ]  && rm -rf automations

# 4) pastas de backup/arquivo antigas (já temos config limpo)
find . -maxdepth 1 -type d -name ".archive_*" -print -exec rm -rf {} +
# (se tiver tar.gz antigos, remova também)
find . -maxdepth 1 -type f -name "backup_*.tar.gz" -print -delete

# 5) docs — limpeza leve (opcional, só se não precisar)
[ -d docs/_archive ] && rm -rf docs/_archive
[ -f docs/DEV_MAKEFILE.txt ] && rm -f docs/DEV_MAKEFILE.txt
# se o LICENSE da raiz já cobre, pode remover cópia em docs/
[ -f docs/LEGAL_LICENSE.txt ] && rm -f docs/LEGAL_LICENSE.txt
# samples de docs (remova se não usa)
[ -d docs/samples ] && rm -rf docs/samples

echo "[done] árvore final:"
tree -a -L 2 -I '.git|.venv|__pycache__|*.pyc|*.log|node_modules|dist|build'
