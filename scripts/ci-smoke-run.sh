#!/usr/bin/env bash
# idempotency_key: ci-smoke-local-2025-10-22-v1
set -euo pipefail

IDEMPOTENCY_KEY="ci-smoke-local-2025-10-22-v1"
BASE_DIR="/srv/projects/ai-router"
COMPOSE_FILE="$BASE_DIR/docker-compose.yml"
SERVICE_NAME="ai-router"
BASE_URL="${BASE_URL:-http://localhost:8082}"
OUTDIR="/tmp/ai-router-ci.$(date +%s)"
mkdir -p "$OUTDIR"

log() { printf '[ci-smoke] %s\n' "$*" >&2; }

cleanup() {
  set +e
  if [ -f "$COMPOSE_FILE" ]; then
    docker compose -f "$COMPOSE_FILE" logs --no-color >"$OUTDIR/compose.log" 2>&1 || true
    docker compose -f "$COMPOSE_FILE" ps >"$OUTDIR/compose_ps.txt" 2>&1 || true

    # Router container logs
    CID=$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE_NAME" 2>/dev/null || true)
    if [ -n "${CID:-}" ]; then
      docker logs "$CID" >"$OUTDIR/router.log" 2>&1 || true
    fi

    docker compose -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
  fi
  set -e
}
trap cleanup EXIT

run_with_retry() {
  # Runs provided command (as a string) with timeout 10s, up to 3 tries
  local cmd="$*"
  local attempt
  for attempt in 1 2 3; do
    if timeout 10s bash -lc "$cmd"; then
      return 0
    fi
    sleep 2
  done
  return 1
}

to_ms() {
  # Convert a value with unit to milliseconds. Accepts formats like 123ms, 1.2s, 500µs
  local val="$1"
  local num unit
  num=$(printf '%s' "$val" | sed -E 's/([0-9]+\.?[0-9]*).*/\1/')
  unit=$(printf '%s' "$val" | sed -E 's/[0-9]+\.?[0-9]*\s*(.*)/\1/')
  case "$unit" in
    ms|msec|millisecond|milliseconds|ms,) printf '%s\n' "$num" ;;
    s|sec|second|seconds|s,) awk -v n="$num" 'BEGIN { printf("%.3f\n", n*1000) }' ;;
    µs|us|microsecond|microseconds|µs,) awk -v n="$num" 'BEGIN { printf("%.3f\n", n/1000) }' ;;
    *) printf '%s\n' "$num" ;;
  esac
}

extract_p95() {
  local p95=""
  local json="$OUTDIR/k6_models.json"
  local stdout_log="$OUTDIR/k6_stdout.log"

  if command -v jq >/dev/null 2>&1 && [ -s "$json" ]; then
    p95=$(jq -r 'try .metrics.http_req_duration.values["p(95)"] // empty' "$json" 2>/dev/null || true)
    if [ -z "$p95" ] || [ "$p95" = "null" ]; then
      # Alternate possible structure
      p95=$(jq -r 'try .metrics.http_req_duration.p95 // empty' "$json" 2>/dev/null || true)
    fi
    if [ -n "$p95" ] && [ "$p95" != "null" ]; then
      printf '%.3f\n' "$p95"
      return 0
    fi
  fi

  # Fallback: parse from stdout
  if [ -s "$stdout_log" ]; then
    # Look for p(95)=<value><unit>
    local raw
    raw=$(grep -E "http_req_duration.*p\(95\)=" "$stdout_log" | tail -n1 | sed -E 's/.*p\(95\)=([^ ]+).*/\1/' || true)
    if [ -n "$raw" ]; then
      to_ms "$raw"
      return 0
    fi
  fi
  return 1
}

log "Working directory: $OUTDIR"

# Bring up service
run_with_retry "docker compose -f '$COMPOSE_FILE' up -d --build '$SERVICE_NAME'"

# Wait for healthz and save
run_with_retry "curl -sS -f -H 'accept: application/json' --max-time 10 '$BASE_URL/healthz' -o '$OUTDIR/healthz.json'"

# Fetch models
run_with_retry "curl -sS -f -H 'accept: application/json' --max-time 10 '$BASE_URL/v1/models' -o '$OUTDIR/models.json'"

# Run k6 via container, export JSON summary
K6_JSON="$OUTDIR/k6_models.json"
K6_LOG="$OUTDIR/k6_stdout.log"

run_k6() {
  docker run --rm --network host \
    -e BASE_URL="$BASE_URL" \
    -v "$BASE_DIR/tests:/scripts:ro" \
    -v "$OUTDIR:/out" \
    grafana/k6:latest run /scripts/k6_models.js --summary-export /out/k6_models.json | tee "$K6_LOG"
}

attempt=1
k6_ok=1
while [ $attempt -le 3 ]; do
  if run_k6; then
    k6_ok=0
    break
  fi
  attempt=$((attempt+1))
  sleep 2
done

if [ $k6_ok -ne 0 ]; then
  log "k6 run failed after 3 attempts"
fi

P95=""
if P95=$(extract_p95); then
  :
else
  P95="-1"
fi

# Final JSON line
printf '{"run_id":%s,"p95_ms":%s,"outdir":"%s"}\n' "0" "$P95" "$OUTDIR"

