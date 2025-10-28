#!/usr/bin/env bash
set -euo pipefail

# === Descobrir Desktop cross-user ===
DESK="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
[ -d "$DESK" ] || DESK="$HOME/Desktop"
mkdir -p "$DESK"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$DESK/AI-Router-Portable-$STAMP"
APP_SRC="/srv/projects/ai-router"

echo "[1/4] Projeto (limpo) → $OUT/app"
mkdir -p "$OUT/app"
rsync -a "$APP_SRC"/ "$OUT/app"/ \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.log' \
  --exclude '.mcp-debug-tools' \
  --exclude 'config/.env.local' \
  --exclude 'requirements.backup.tgz'

# snapshot leve das deps (não é lock, só referência)
echo "[2/4] Deps"
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  PY=""
fi
if [ -n "${PY}" ] && "$PY" -m pip --version >/dev/null 2>&1; then
  "$PY" -m pip freeze > "$OUT/app/requirements.freeze.txt" || true
fi

# === OLLAMA (somente receitas/lista, sem blobs quantizados) ===
echo "[3/4] Ollama (receitas/lista — sem quantizados)"
mkdir -p "$OUT/ollama"
LIST="$OUT/ollama/pull_list.txt"
MODS="$OUT/ollama/recipes"
mkdir -p "$MODS"

# tenta via API; se falhar e tiver cli, tenta 'ollama list --format json'
models_json="$(curl -sS http://localhost:11434/api/tags || true)"
if [ -z "$models_json" ] && command -v ollama >/dev/null 2>&1; then
  models_json="$(ollama list --format json 2>/dev/null || true)"
fi

# extrai nomes (fallback: usa os padrões já observados no projeto)
if [ -n "$models_json" ]; then
  echo "$models_json" | \
    awk '
      /"name":/ {
        gsub(/[",]/,""); 
        # name: x:y
        for(i=1;i<=NF;i++) if($i ~ /name:/){print $(i+1)}
      }' > "$LIST.tmp" || true
else
  # fallback mínimo (com base no que usamos)
  cat > "$LIST.tmp" <<EOF2
llama3.1:8b-instruct-q5_K_M
deepseek-coder-v2:16b
EOF2
fi

# normaliza para "sem quantização" quando aplicável (ex.: remove sufixo -qX_*)
sed -E 's/(-q[0-9][^ ]*)$//; s/:8b-instruct$/:8b-instruct/;' "$LIST.tmp" \
  | awk '!seen[$0]++' > "$LIST"
rm -f "$LIST.tmp"

# gera Modelfile "receita" simples por modelo (quando possível)
# Dica: se o usuári@ quiser reproduzir igual, basta usar 'ollama pull <nome>' do LIST
# Aqui geramos receita básica para facilitar adaptação futura
while read -r tag; do
  [ -n "$tag" ] || continue
  fn="$(echo "$tag" | tr ':/' '__').Modelfile"
  {
    echo "# Portável: baseie-se no modelo público e ajuste parâmetros conforme sua estação"
    echo "FROM $tag"
    echo "# PARAMETER temperature 0.2"
    echo "# TIP: se precisar quantizar em outra máquina, use: ollama run $tag e ajuste hardware"
  } > "$MODS/$fn"
  echo "  - $tag → $fn"
done < "$LIST"

# === README de restauração (multiplataforma) ===
echo "[4/4] RESTORE.md"
cat > "$OUT/RESTORE.md" <<'RMD'
# AI Router — Restauração Portátil

Este pacote contém:
- `app/` — projeto **sem segredos** e sem `.venv`
- `app/requirements.txt` e `app/requirements.freeze.txt` (referência)
- `ollama/pull_list.txt` — nomes de modelos a puxar
- `ollama/recipes/*.Modelfile` — receitas base (opcional)
- este guia

> **Segurança:** crie `config/.env.local` à mão (use `config/.env.example` como base).

## 1) Pré-requisitos

### Linux/macOS
```bash
# Python 3.10+ e pip
python3 --version
python3 -m pip --version
# Ollama (https://ollama.com/download)
ollama --version
Windows
Recomendo WSL (Ubuntu) para seguir os comandos Linux/macOS.

Alternativa nativa: instale Python + Ollama para Windows e adapte os comandos.

2) Restaurar o projeto
bash
￼Copiar código
cd ./app
python3 -m venv .venv
. .venv/bin/activate

# Instalar dependências
python -m pip install -U pip
python -m pip install -r requirements.txt

# Configurar variáveis (crie a sua)
cp -n config/.env.example config/.env.local 2>/dev/null || true
# Edite config/.env.local e preencha o que for necessário (chaves Cloud opcionais)

# Carregar env nesta sessão
set -a; . config/.env.local; set +a
3) Preparar modelos no Ollama
Opção A — puxar dos repositórios
bash
￼Copiar código
# Baixe os modelos listados (pode ajustar/omitir)
while read -r m; do [ -n "$m" ] && ollama pull "$m"; done < ../ollama/pull_list.txt
Opção B — partir das receitas (Modelfile)
bash
￼Copiar código
# (Opcional) construir localmente a partir de recipes
for f in ../ollama/recipes/*.Modelfile; do
  tag="$(basename "$f" .Modelfile | sed 's/__/:/')"   # reverte __ para :
  ollama create "$tag" -f "$f"
done
4) Executar
Produção (systemd não incluso neste backup)
bash
￼Copiar código
# Execute direto (porta 8082). Se já houver um serviço da sua distro, adapte.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
Desenvolvimento (reload, porta 8083)
bash
￼Copiar código
# Em outra aba/terminal:
. .venv/bin/activate && set -a; . config/.env.local; set +a
python -m uvicorn app.main:app --host 0.0.0.0 --port 8083 --reload
5) Testar rápido
bash
￼Copiar código
# Saúde
curl -fsS http://localhost:8082/healthz && echo "OK"

# Roteamento curto (local-first)
curl -s http://localhost:8082/route -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explique HVAC em 1 frase."}]}' | python3 -m json.tool | sed -n '1,40p'
6) Painel
Abra: http://localhost:8082/guide
Os botões numerados copiam apenas o comando (sem o comentário).

7) Dicas
Se quiser automatizar como serviço: crie uma unidade systemd semelhante à original do projeto (não inclusa neste backup).

Para sincronizar os atalhos do painel a partir do Makefile, rode:

make panel-json && make panel-refresh (no diretório do projeto, já com venv/env ativos).

Bom uso!
RMD

echo "OK: $OUT"
