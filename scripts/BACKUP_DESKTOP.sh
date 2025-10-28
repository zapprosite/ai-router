#!/usr/bin/env bash
set -euo pipefail
APP="/srv/projects/ai-router"
VENV="$APP/.venv"
DESK="${HOME}/Desktop"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${DESK}/AI-Router-Backup-${STAMP}"

mkdir -p "${DEST}/ai-router" "${DEST}/ollama"

echo "[1/4] Projeto (sem segredos/venv/__pycache__)"
rsync -a "${APP}/" "${DEST}/ai-router/" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude "repo_tree.txt" \
  --exclude "requirements.backup.tgz" \
  --exclude "config/.env.local"

echo "[2/4] Deps"
if [ -d "$VENV" ]; then
  . "$VENV/bin/activate" && pip freeze > "${DEST}/requirements.lock.txt" || true
else
  echo "# (sem venv no momento)" > "${DEST}/requirements.lock.txt"
fi

echo "[3/4] Ollama (lógico, sem quantizados) → Modelfile por modelo"
if command -v ollama >/dev/null 2>&1; then
  # pega nomes dos modelos (coluna 1). Compatível com versões antigas/novas do CLI.
  MODELS=$(ollama list 2>/dev/null | awk 'NR>1 {print $1}' || true)
  for m in $MODELS; do
    safe="$(echo "$m" | tr '/:' '__')"
    if ollama show --modelfile "$m" > "${DEST}/ollama/${safe}.Modelfile" 2>/dev/null; then
      echo "  - ${m} → ${safe}.Modelfile"
    fi
  done
else
  echo "# ollama não encontrado" > "${DEST}/ollama/README.txt"
fi

echo "[4/4] README de restauração"
cat > "${DEST}/README_BACKUP.md" <<MD
# AI Router — Backup ${STAMP}

Conteúdo:
- \`ai-router/\` — código-fonte **sem** credenciais (\`config/.env.local\` não incluído).
- \`requirements.lock.txt\` — snapshot de dependências (pip freeze).
- \`ollama/*.Modelfile\` — **backup lógico** dos modelos (sem pesos quantizados).

## Restaurar projeto
1. Copie \`ai-router/\` para o servidor de destino.
2. Crie venv e instale deps:
   \`\`\`bash
   cd ai-router
   python3 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   \`\`\`
3. Crie \`config/.env.local\` a partir do seu segredo (ou do \`.env.example\`).
4. (Opcional) systemd:
   \`\`\`bash
   sudo cp /etc/systemd/system/ai-router.service /etc/systemd/system/ # se já tiver
   sudo systemctl daemon-reload && sudo systemctl enable --now ai-router
   \`\`\`

## Restaurar modelos do Ollama (sem pesos)
Para cada \`*.Modelfile\`:
\`\`\`bash
ollama create <nome> -f <arquivo.Modelfile>
# exemplo:
ollama create llama3.1:8b-instruct-q5_K_M -f ollama/llama3.1__8b-instruct-q5_K_M.Modelfile
\`\`\`
> Isso reconstitui os **manifests** e baixa pesos novamente sob demanda (sem carregar blobs do seu backup).

MD

echo "OK: ${DEST}"
