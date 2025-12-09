# Getting Started with AI Router

Welcome! This guide will take you from "Zero" to "AI Hero" in about 2 minutes.

## Prerequisites
- **Linux/Mac/WSL**
- **Python 3.10+**
- **OpenAI API Key** (optional, but needed for Tier 3/5 models)

## Step 1: Clone & Setup

Download the repository and enter the directory (if you haven't already).

```bash
# In your terminal
make dev
```
*This command creates a virtual environment, installs all dependencies, and starts the server.*

## Step 2: Configure Secrets

You need to tell the router your API keys. We use a `.env.local` file for this.

**Run this magic command:**
(Replace `sk-...` with your actual key)

```bash
sudo tee config/.env.local > /dev/null << 'EOF'
OPENAI_API_KEY_TIER2=sk-proj-YOUR_REAL_KEY_HERE
ENABLE_OPENAI_FALLBACK=1
EOF
```

## Step 3: Run the Mission Control

Access the dashboard to see your router in action.

**Open in Browser:** [http://localhost:8087/guide](http://localhost:8087/guide)

## Step 4: Make Your First Request

Open a new terminal window and try sending a request.

**Simple Chat (Goes to Local Model):**
```bash
curl -X POST http://localhost:8087/route \
  -H "Content-Type: application/json" \
  -d '{ "messages": [{"role": "user", "content": "Hello!"}] }'
```

**Complex Code (Goes to GPT-5.1):**
```bash
curl -X POST http://localhost:8087/route \
  -H "Content-Type: application/json" \
  -d '{ 
    "messages": [{"role": "user", "content": "CRITICAL: Fix this deadlock in the payment gateway"}],
    "prefer_code": true 
  }'
```

## Step 5: Monitor Costs

Check your usage and costs against the "90% Local / 10% Cloud" goal:

```bash
python3 scripts/cost_report.py
```

## What's Next?
- Check out [ARCHITECTURE.md](ARCHITECTURE.md) to understand how it works.
- Customize models in `config/router_config.yaml`.
