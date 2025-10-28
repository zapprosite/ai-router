Bug Report — Rootless Makefile & Panel Sync

Primary bug
- On constrained hosts (no sudo/systemd), Makefile targets that call sudo/systemctl/journalctl/fuser fail. This breaks restart/status/logs/free-8082/backup-all and can cascade into false negatives for smoke/evals when service control is attempted.

Secondary risk
- SLA fallback logic must only escalate to cloud when ENABLE_OPENAI_FALLBACK=1 AND local path exceeded the SLA (6s) or failed. Ensure we always attempt local first, measure, then respect SLA before trying cloud.

Tertiary issue
- Panel JSON should be generated only from explicit commands intended for copy/paste. Use only lines marked as: `## data-cmd: <command>` from the Makefile to build `public/guide_cmds.json`. Avoid injecting privileged or environment-specific defaults.

Fix summary (this PR)
- Makefile: add `SUDO ?= sudo` and `-include .env.make` to allow rootless operation without changing systemd/ports/secrets. Replace `sudo` with `$(SUDO)` where used.
- New `.env.make`: sets `SUDO=` by default and allows optional `BACKUP_DIR` override on desktops.
- scripts/extract_make_cmds.py: generate `public/guide_cmds.json` exclusively from `## data-cmd:` lines (no fallbacks). Added a small, safe set of data-cmd commands to Makefile.
- scripts/LATENCY_PROBE.sh: simple local latency vs SLA probe. JSON output.
- scripts/RUN_AUDIT_AND_TESTS.sh: rootless audit (endpoints, smoke, evals, latency probe) with a compact JSON summary.

Constraints / not changed
- No changes to ports (8082/8083), systemd units, docker compose, or secrets.
- No model catalog changes; Qwen not reintroduced.
- API endpoints unchanged: GET/HEAD /healthz, GET/HEAD /guide, GET / → 302 /guide, GET /v1/models, POST /route.

Next steps (optional)
- CI can call `scripts/RUN_AUDIT_AND_TESTS.sh` in rootless runners.
- If desired, expand data-cmd set or user-specific `.env.make` without modifying tracked Makefile.

