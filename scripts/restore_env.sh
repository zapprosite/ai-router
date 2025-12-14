#!/bin/bash
# scripts/restore_env.sh
# Utility to restore environment variables from a backup location (e.g. USB mount or secret volume)

BACKUP_PATH="${1:-/mnt/secrets/.env}"
TARGET_PATH=".env"

if [ -f "$BACKUP_PATH" ]; then
    echo "✅ Restoring .env from $BACKUP_PATH..."
    cp "$BACKUP_PATH" "$TARGET_PATH"
    chmod 600 "$TARGET_PATH"
else
    echo "⚠️ .env backup not found at $BACKUP_PATH. Assuming env vars are injected via runtime."
fi
