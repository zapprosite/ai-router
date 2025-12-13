# Deployment Guide

## 🔑 Environment Variables
Configuration is handled via `.env.local` in the `config/` directory.

| Variable | Description | Required? |
| :--- | :--- | :--- |
| `AI_ROUTER_API_KEY` | Key clients use to access the router. | **Yes** |
| `OPENAI_API_KEY_TIER2` | Enables Cloud Tier 4/5 models. | No (Local-only mode) |
| `ENABLE_OPENAI_FALLBACK` | `1` to enable Cloud, `0` for Local-Only. | No (Default: `0`) |
| `OLLAMA_BASE_URL` | URL of local Ollama instance. | No (Default: localhost:11434) |
| `CORS_ALLOW_ORIGINS` | Comma-separated list of allowed origins. | No (Default: `*`) |
| `LOG_LEVEL` | Logging verbosity (INFO, DEBUG). | No (Default: INFO) |

---

## � Docker Deployment

### Build Image
```bash
docker build -t ai-router:latest .
```

### Run Container
```bash
docker run -d --name ai-router \
  -p 8082:8082 \
  --env-file config/.env.local \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --restart unless-stopped \
  ai-router:latest
```

> **Note for Mac/Windows**: Use `host.docker.internal` to connect to Ollama on the host.
> **Note for Linux**: Use `--network host` or the host's IP address.

---

## ☁️ Coolify Deployment

Coolify is a self-hosted PaaS. Follow these steps:

### 1. Create Application
1.  In Coolify, create a new **Docker Compose** or **Nixpacks** application.
2.  Connect your **GitHub repository**.

### 2. Configure Environment Variables
In Coolify's **Environment Variables** section, add:

| Variable | Value |
| :--- | :--- |
| `AI_ROUTER_API_KEY` | `your-strong-secret-key` |
| `OLLAMA_BASE_URL` | `http://YOUR_OLLAMA_HOST:11434` |
| `ENABLE_OPENAI_FALLBACK` | `0` (or `1` if you have a cloud key) |
| `OPENAI_API_KEY_TIER2` | `sk-proj-...` (only if cloud enabled) |
| `CORS_ALLOW_ORIGINS` | `https://your-domain.com` |

> ⚠️ **IMPORTANT**: Do NOT set `CORS_ALLOW_ORIGINS=*` in production!

### 3. Health Check
Coolify will use the `HEALTHCHECK` directive in the Dockerfile. No extra config needed.

### 4. Deploy
Trigger the deployment. Monitor the logs for:
```
INFO: Config validated. X models registered.
INFO: Uvicorn running on http://0.0.0.0:8082
```

### 5. Verify
```bash
curl https://your-domain.com/healthz
# Should return: {"status":"ok"}
```

---

## �🐧 Systemd Service (Linux - Alternative)
To run as a background service without Docker:

1. Copy service file:
    ```bash
    sudo cp ops/ai-router.service /etc/systemd/system/
    ```
2. Enable and Start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable --now ai-router
    ```
3. Logs:
    ```bash
    journalctl -u ai-router -f
    ```
