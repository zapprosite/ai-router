# 🚀 Deployment Checklist for Coolify

Before triggering the deployment in Coolify, verify the following items to ensure a smooth "Push-to-Production" experience.

## 📋 Pre-Flight Checks

- [ ] **Environment Variables Prepared**:
    - [ ] `AI_ROUTER_API_KEY` (Generated unique key)
    - [ ] `CLOUDFLARE_TUNNEL_TOKEN` (Valid token from Zero Trust Dashboard)
    - [ ] `OLLAMA_MODEL` (e.g., `deepseek-coder:6.7b` or `llama3`)
    - [ ] `GPU_QUEUE_MAX_WORKERS` set to `1` (for consumer GPUs) or `2` (for 24GB+ VRAM).

- [ ] **GitHub Repository**:
    - [ ] All recent changes pushed to `main` branch.
    - [ ] `Dockerfile` and `docker-compose.prod.yml` are present in root.

- [ ] **Target Server (Coolify)**:
    - [ ] **GPU Drivers**: NVIDIA Drivers & Container Toolkit installed on host.
    - [ ] **Docker**: Running and able to access GPU (`docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi`).

## 🛠 Deployment Steps

1.  **Coolify UI**:
    - [ ] Create Resource -> Git Repository.
    - [ ] Point to `zapprosite/ai-router`.
    - [ ] Build Pack: **Docker Compose**.
    - [ ] Docker Compose File Location: `/docker-compose.prod.yml`.

2.  **Configuration**:
    - [ ] Paste Environment Variables into Coolify secrets.

3.  **Launch**:
    - [ ] Click "Deploy".
    - [ ] Watch Logs: Ensure `init.sh` runs migrations and starts `uvicorn`.

4.  **Verification**:
    - [ ] Check `/health` endpoint via the Cloudflare public URL.
    - [ ] Metric `gpu_queue.active_workers` should be 0.
