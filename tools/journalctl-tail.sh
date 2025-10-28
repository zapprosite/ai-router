#!/usr/bin/env bash
set -euo pipefail
journalctl -u ai-router -n "${1:-120}" --no-pager
