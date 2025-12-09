# AI Router Deployment Guide

## Production Requirements
- **OS**: Linux (Ubuntu 22.04+ recommended)
- **Python**: 3.10+
- **Hardware**: 
  - Minimum: 16GB RAM (for local 8B models)
  - Recommended: NVIDIA GPU (24GB VRAM) for 16B+ models.

## Installation

1. **Clone & Setup**
   ```bash
   git clone ...
   cd ai-router
   make venv
   ```

2. **Configuration**
   - Copy `.env.example` to `config/.env.local`.
   - Set `ENABLE_OPENAI_FALLBACK=1` and add API keys if using cloud fallback.

3. **Service Management**
   - The project includes systemd integration.
   - `make run` runs in foreground (port 8082).
   - `make start` (custom) or use `systemctl start ai-router`.

## Docker
(Dockerfile provided in root)
```bash
docker build -t ai-router .
docker run -p 8082:8082 --env-file config/.env.local ai-router
```

## Monitoring
- **Health Check**: `GET /healthz`
- **Dashboard**: `http://localhost:8082/guide`
- **Metrics**: See logs or `/route` return headers.
