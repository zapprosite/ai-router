# 🚀 AI Router Deployment Guide (Coolify)

This guide helps you deploy **AI Router** as a production-ready Microservice with **Local GPU Support** (Ollama), **Redis Queue** for concurrency management, and **Cloudflare Tunnel** for secure public access.

## Architecture

```mermaid
graph LR
    User[User / Internet] -->|HTTPS| Cloudflare[Cloudflare Tunnel]
    Cloudflare -->|Localhost:8082| Router[AI Router (FastAPI)]
    
    subgraph "Docker Stack (Coolify)"
        Router --> Postgres[(Postgres DB)]
        Router --> Redis[(Redis Queue)]
        
        Router -->|Low Conf / Code| Ollama[Ollama (GPU)]
        Router -->|Critical / Logic| OpenAI[OpenAI API (Cloud)]
        
        Redis <-->|Lock/Limit| Router
    end
    
    Ollama -.-> GPU[NVIDIA GPU]
```

## Prerequisites

1.  **Server**: A Linux VPS/Server with a dedicated NVIDIA GPU (e.g., RTX 3090/4090).
2.  **OS**: Ubuntu 22.04+ with **NVIDIA Container Toolkit** installed.
3.  **Coolify**: Installed and running (`curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash`).
4.  **Cloudflare**: A Cloudflare account and a Domain.

---

## 📦 Step-by-Step Deployment

### 1. Prepare Environment
Ensure your server recognizes the GPU inside Docker:
```bash
sudo docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
*If this fails, install `nvidia-container-toolkit`.*

### 2. Coolify Setup
1.  **Create New Resource**: Go to your Coolify Project -> "New" -> "Git Repository".
2.  **Repository URL**: `https://github.com/your-org/ai-router` (or your fork).
3.  **Build Pack**: Select **Docker Compose**.
4.  **Docker Compose File**: Paste the content of `docker-compose.prod.yml` (or select path if connected to GitHub app).

### 3. Environment Variables
In Coolify's "Environment Variables" section, add the keys from `.env.example`.

| Variable | Value (Example) | Description |
|---|---|---|
| `AI_ROUTER_API_KEY` | `sk-prod-secret` | Protects your API. |
| `CLOUDFLARE_TUNNEL_TOKEN` | `eyJh...` | **Required** for Public Access. Get this from Zero Trust Dashboard. |
| `OLLAMA_MODEL` | `deepseek-coder:6.7b` | Model to auto-pull on startup. |
| `GPU_QUEUE_MAX_WORKERS` | `1` | **Crucial**: Keep at 1 or 2 for consumer GPUs to prevent OOM. |
| `ENABLE_OPENAI_FALLBACK` | `1` | Enable/Disable Cloud Backup. |

### 4. Deploy
Click **Deploy**.
- Coolify will pull images, build the app, and start the stack.
- The `scripts/init.sh` will automatically:
    1.  Wait for DB.
    2.  Run Migrations.
    3.  Trigger Ollama to pull `deepseek-coder`.
    4.  Start the Router.

### 5. Verify
Check the Application Logs in Coolify to see the startup process.
Once "Healthy", your API is accessible via the Cloudflare Tunnel URL you configured (e.g., `https://ai.your-domain.com`).

**Health Check**:
```bash
curl https://ai.your-domain.com/health
# Returns: {"status":"ok", "gpu_queue": {"active_workers": 0, "queue_depth": 0}}
```

---

## 🔧 Queue Testing

To verify the GPU Queue is protecting your hardware:
1.  Set `GPU_QUEUE_MAX_WORKERS=1`.
2.  Send 5 concurrent requests to the API.
3.  Observe logs:
    - You will see 4 requests "Enqueued".
    - 1 Request "Active".
    - As one finishes, the next is popped from Redis.

---

## 🛑 Troubleshooting

**Ollama GPU Not Found?**
- Verify `docker-compose.prod.yml` has the `deploy: resources: reservations: devices: - driver: nvidia` block (it does).
- Verify Host OS driver version.

**Cloudflare Tunnel Fail?**
- Check `CLOUDFLARE_TUNNEL_TOKEN`. It must be a valid token for the tunnel created in CF Dashboard.
