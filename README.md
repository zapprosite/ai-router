# AI Router (LangGraph Gateway)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/ai-router)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Port](https://img.shields.io/badge/port-8087-orange)](http://localhost:8087)

**An Enterprise-Grade LLM Gateway** that intelligently routes prompts between local models (Ollama) and cloud providers (OpenAI) based on complexity, cost, and code-generation needs.

---

## 🚀 Quick Start

cd /srv/projects/ai-router
source .venv/bin/activate
pytest -q

### 1. Configure Secrets
Copy the command below, replace `sk-proj-...` with your actual OpenAI API Key, and paste it into your terminal. This will securely configure your environment.

```bash
sudo tee /srv/projects/ai-router/config/.env.local > /dev/null << 'EOF'
# === AI ROUTER CONFIGURATION ===
# Replace the key below with your actual OpenAI API Key
OPENAI_API_KEY_TIER2=sk-proj-YOUR_ACTUAL_KEY_HERE_REPLACE_ME

# Router Settings
ENABLE_OPENAI_FALLBACK=1
OPENAI_TIMEOUT_SEC=20
EOF
```

### 2. Launch the Router
Get the system up and running in seconds.

```bash
# Start the server (Development Mode)
make dev
# Service will be available at http://localhost:8087
```

---

## ⚡ Key Features

*   **💡 Intelligent Routing**: Automatically directs simple tasks to local models (Llama 3.1, DeepSeek) and complex reasoning to Cloud/Tier 5 (GPT-5.1, O3).
*   **🛡️ Cost Guard**: Real-time budget protection prevents accidental overspending.
*   **👁️ Observability**: Built-in metrics endpoint and cost reporting scripts.
*   **🔌 Drop-in Replacement**: Compatible with OpenAI's API format.
*   **Multi-Tier Architecture**:
    *   **Tier 1 (Local)**: Llama 3.1 (Fast, Free)
    *   **Tier 2 (Code)**: DeepSeek Coder (Specialized Local)
    *   **Tier 3 (Cloud)**: GPT-4.1 / GPT-4o-mini (Balanced)
    *   **Tier 4 (Reasoning)**: o-series / o3-mini (Complex Logic)
    *   **Tier 5 (Elite)**: GPT-5.1 High / Codex (State of the Art)

---

## ⚙️ Customization

### Changing Models
To modify the available models or routing logic, edit `config/router_config.yaml`.

```bash
nano config/router_config.yaml
```

**Example: Add a new model**
```yaml
  - id: my-new-model
    provider: openai
    name: "gpt-4-turbo"
    tier: 3
    capabilities: ["general", "fast"]
```

### Routing Logic
You can adjust the routing thresholds in the `routing_policy` section of the config file.

```yaml
  code_gen:
    low: ["deepseek-coder-v2-16b"] # Local
    high: ["gpt-5.1-codex-mini"]    # Cloud
    critical: ["gpt-5.1-codex-high"] # Best Available
```

---

## 🛠️ API Usage

### Interactive Dashboard
Visit the **[Mission Control Dashboard](http://localhost:8087/guide)** to see real-time routing decisions and system status.

### Example Request
```bash
curl -X POST http://localhost:8087/route \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SUA_CHAVE_AQUI" \
  -d '{
    "messages": [{"role": "user", "content": "Write a Python function to sort a list"}],
    "prefer_code": true
  }'
```

---

## 📚 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)**: Zero to Hero tutorial.
- **[Architecture](docs/ARCHITECTURE.md)**: How the decision engine works.
- **[Changelog](CHANGELOG.md)**: Version history and updates.

## 🤝 Contributing

Contributions are welcome! Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
