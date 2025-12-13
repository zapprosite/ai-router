#!/bin/bash
# PRE_FLIGHT_CHECK.sh - Bulletproof port 8087 safety check
# Usage: ./scripts/PRE_FLIGHT_CHECK.sh
# Called automatically by: make dev

set -e

PORT=8082
TIMEOUT=5
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== PRE-FLIGHT CHECK: Port $PORT ==="

# Check if port is in use
check_port() {
    ss -tlnp 2>/dev/null | grep -q ":$PORT " && return 0 || return 1
}

get_pids() {
    lsof -ti :$PORT 2>/dev/null | tr '\n' ' ' || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | tr '\n' ' '
}

if ! check_port; then
    echo -e "${GREEN}✅ Port $PORT is FREE. Proceeding.${NC}"
    exit 0
fi

# Port is in use - identify and kill
PIDS=$(get_pids)
echo -e "${YELLOW}⚠️  Port $PORT is IN USE. PIDs: $PIDS${NC}"

# Show what's holding it
echo "Process details:"
for pid in $PIDS; do
    ps -p $pid -o pid,ppid,user,cmd --no-headers 2>/dev/null || echo "  PID $pid (no details)"
done

# Attempt graceful kill
echo -e "${YELLOW}Attempting graceful shutdown (SIGTERM)...${NC}"
for pid in $PIDS; do
    kill -TERM $pid 2>/dev/null || true
done

# Wait for graceful shutdown
for i in $(seq 1 $TIMEOUT); do
    sleep 1
    if ! check_port; then
        echo -e "${GREEN}✅ Port $PORT freed after $i second(s).${NC}"
        exit 0
    fi
    echo "  Waiting... ($i/$TIMEOUT)"
done

# Still in use? Force kill
if check_port; then
    PIDS=$(get_pids)
    echo -e "${RED}Port still in use. Force killing (SIGKILL)...${NC}"
    for pid in $PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 1
fi

# Final check
if check_port; then
    echo -e "${RED}❌ FATAL: Port $PORT still in use after force kill.${NC}"
    echo "Manual intervention required:"
    echo "  1. Run: sudo fuser -k $PORT/tcp"
    echo "  2. Or:  sudo systemctl stop ai-router"
    echo "  3. Check: ss -tlnp | grep $PORT"
    exit 1
fi

echo -e "${GREEN}✅ Port $PORT is now FREE. Proceeding.${NC}"
exit 0
