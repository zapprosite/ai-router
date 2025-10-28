#!/usr/bin/env bash
set -euo pipefail
cd /srv/projects/ai-router

# inventário do repo
REPO_TREE="$(
  { command -v tree >/dev/null &&
      tree -a -I '.git|.venv*|__pycache__|*.pyc|node_modules|.pytest_cache|.mypy_cache|.reports|k6_out|test-results|.cursor|.taskmaster|.local' \
    || find . -not -path './.git/*' -not -path './.venv*/*' -not -path './__pycache__/*' \
              -not -path './node_modules/*' -not -path './.pytest_cache/*' -not -path './.mypy_cache/*' \
              -not -path './.reports/*' -not -path './k6_out/*' -not -path './test-results/*' \
              -not -path './.cursor/*' -not -path './.taskmaster/*' -not -path './.local/*' -print | sort; }
)"

r(){ [ -f "$1" ] && sed -n '1,400p' "$1" || true; }

GUARD="$(r .codex/prompts/repo_guardrails.prompt)"
REWRITE="$(r .codex/prompts/rewrite_docs.prompt)"

README="$(r README.md)"
ARCH="$(r docs/ARCHITECTURE.md)"
LUSE="$(r docs/LOCAL_USAGE.md)"
EVALS="$(r docs/EVALS.md)"
FRONT="$(r docs/FRONTEND_INTEGRATION.md)"
SECR="$(r docs/SECRETS_STANDARD.md)"
AGNT="$(r docs/AGENTS.md)"
PRD="$(r docs/PRD_TASK_MASTER.md)"
GUIDE="$(r docs/guide.md)"
GTEST="$(r docs/guia_de_test.md)"

mkdir -p .reports .codex

cat > .codex/.tmp_rewrite_input.txt <<PROMPT
You are Codex CLI operating on the repository "ai-router".

NON-NEGOTIABLE GUARD-RAILS (read & obey strictly):
$GUARD

OBJECTIVE:
Rewrite and uplift ALL docs into a professional, consistent, senior-level documentation set, preserving the current stack and NOT breaking anything. Read first, then propose minimal diffs when needed. Keep local-first routing (Ollama) + Tier-2 fallback (OpenAI) intact.

CURRENT REPO TREE:
-----
$REPO_TREE
-----

CURRENT DOCS:
===== README.md =====
$README

===== docs/ARCHITECTURE.md =====
$ARCH

===== docs/LOCAL_USAGE.md =====
$LUSE

===== docs/EVALS.md =====
$EVALS

===== docs/FRONTEND_INTEGRATION.md =====
$FRONT

===== docs/SECRETS_STANDARD.md =====
$SECR

===== docs/AGENTS.md =====
$AGNT

===== docs/PRD_TASK_MASTER.md =====
$PRD

===== docs/guide.md =====
$GUIDE

===== docs/guia_de_test.md =====
$GTEST

DELIVERABLES (RETURN JSON ONLY):
{
  "README.md": "...final content...",
  "docs/ARCHITECTURE.md": "...",
  "docs/LOCAL_USAGE.md": "...",
  "docs/EVALS.md": "...",
  "docs/FRONTEND_INTEGRATION.md": "...",
  "docs/SECRETS_STANDARD.md": "...",
  "docs/AGENTS.md": "...",
  "docs/guide.md": "...",
  "docs/guia_de_test.md": "..."
}
STRICT RULES:
- DO NOT change ports, systemd units, docker-compose, or secret values.
- Keep HEAD/GET /healthz and /guide; GET / -> 302 /guide.
- Makefile recipes must use real TABs; no CRLF.
- OpenAI: add reasoning_effort only for model == "gpt-5" and env in {low, medium, high}; never for nano/mini/codex.
PROMPT

# Execute o codex lendo tudo de STDIN (ajuste --model se precisar)
codex < .codex/.tmp_rewrite_input.txt | tee .reports/rewrite_docs.out
