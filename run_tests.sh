#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then echo "python3 não encontrado"; exit 1; fi
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "Instalando python3-venv..."
  sudo apt-get update && sudo apt-get install -y python3-venv
fi
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
export ROUTER_BASE_URL="${ROUTER_BASE_URL:-http://localhost:8082}"
export PYTHONPATH="${PYTHONPATH:-.}"
pytest -q
