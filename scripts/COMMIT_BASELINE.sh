#!/usr/bin/env bash
set -euo pipefail
cd /srv/projects/ai-router

# git init se necessário
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || git init

# garantir ignore de segredos
grep -qxF "config/.env.local" .gitignore || echo "config/.env.local" >> .gitignore
grep -qxF ".venv" .gitignore || echo ".venv" >> .gitignore
grep -qxF "repo_tree.txt" .gitignore || echo "repo_tree.txt" >> .gitignore
grep -qxF "requirements.backup.tgz" .gitignore || echo "requirements.backup.tgz" >> .gitignore
grep -qxF "*.log" .gitignore || echo "*.log" >> .gitignore

# add + commit
git add -A
git commit -m "baseline: router local-first + Tier-2 fallback (FastAPI+LangGraph), tests e tooling" || true

# resumo
echo "== Baseline commit =="
git --no-pager log -1 --stat
