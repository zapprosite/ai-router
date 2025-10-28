#!/usr/bin/env bash
# Desliga fallback cloud (barato), força local-first
export ENABLE_OPENAI_FALLBACK=0
unset OPENAI_API_KEY OPENAI_API_KEY_TIER2
# Agressivo local: aumenta tokens p/ chat/código (sem mexer no .env)
export OLLAMA_NUM_PREDICT_CHAT=256
export OLLAMA_NUM_PREDICT_CODE=1024
echo "[OK] Cloud OFF, local tokens ↑"
