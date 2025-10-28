#!/usr/bin/env bash
set -euo pipefail
ROOT="/srv/projects/ai-router"
cd "$ROOT"

# 0) Backup do estado atual
TS=$(date +%Y%m%d_%H%M%S)
BACKUP="${HOME}/Desktop/ai-router_${TS}.tgz"
tar --exclude='.git' -czf "$BACKUP" .

echo "Backup criado: $BACKUP"

# 1) Verificações rápidas
curl -fsS http://localhost:8082/healthz >/dev/null || echo "WARN: /healthz não respondeu"
test "$(curl -fsS -o /dev/null -w "%{http_code}" http://localhost:8082/guide)" = "200" || echo "WARN: /guide != 200"
test "$(curl -fsS -o /dev/null -w "%{http_code}" http://localhost:8082/)" = "302" || echo "WARN: /=302"

# 2) Apagar histórico e re-inicializar git
rm -rf .git
git init -b main
git config core.autocrlf false
git add -A
git commit -m "chore: local stable baseline (clean history)"

# 3) Defina o remoto novo (ex.: github vazio criado via UI/gh)
#   export NEW_ORIGIN="git@github.com:<owner>/ai-router.git"
if [ -n "${NEW_ORIGIN:-}" ]; then
  git remote add origin "$NEW_ORIGIN"
  git push -u origin main
  git tag -a "v$(date +%Y.%m.%d)-local-stable" -m "local stable baseline"
  git push origin --tags
else
  echo "INFO: variável NEW_ORIGIN não definida. Repositório local pronto. Exporte NEW_ORIGIN e rode 'git push' quando quiser publicar."
fi

echo "DONE."
