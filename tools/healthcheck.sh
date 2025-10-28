#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:8082/healthz >/dev/null && echo "healthy" || { echo "unhealthy"; exit 1; }
