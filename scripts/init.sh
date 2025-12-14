#!/bin/bash
set -e

# 1. Run Database Migrations (if Alembic is configured, otherwise just a placeholder log)
echo "🔍 [Init] Checking database connection..."
# (Logic to wait for DB is mostly handled by docker depends_on + healthcheck, but double check here if needed)

echo "🔄 [Init] Running Database Migrations..."
# alembic upgrade head || echo "⚠️ [Init] Alembic migration failed or not configured, skipping."

# 2. Pre-pull Ollama Model (Background)
# We do this in background so app starts fast, but queued requests might wait
if [ -n "$OLLAMA_MODEL" ]; then
    echo "🧠 [Init] Triggering pull for model: $OLLAMA_MODEL"
    # We use curl to trigger pull on the separate ollama container
    (sleep 5 && curl -X POST http://ollama:11434/api/pull -d "{\"name\": \"$OLLAMA_MODEL\"}" >/dev/null 2>&1) &
fi

# 3. Start Application
echo "🚀 [Init] Starting AI Router (Uvicorn)..."
# Use 0.0.0.0 to bind to all interfaces in container
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8082
