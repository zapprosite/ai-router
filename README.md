# 🧠 AI Router (LangGraph + LiteLLM Pattern)

> **High-Performance, Cost-Aware Model Gateway for Enterprise & Local AI.**  
> *Unified Interface for OpenAI, Ollama, DeepSeek, and Custom Models with Intelligent Routing.*

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Status](https://img.shields.io/badge/status-production--ready-green)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Architecture](https://img.shields.io/badge/architecture-local--first-orange)

---

## 📖 Overview

**AI Router** is a robust "Local-First" gateway designed to optimize cost and privacy by prioritizing local models (Llama 3.1, DeepSeek-Coder) and only escalating to Cloud AI (OpenAI, Claude) when strictly necessary.

It acts as a **Smart Middleware** between your application and LLMs, handling:
- **Automatic Routing**: Zero-config classification of prompt complexity.
- **Cost Guard**: Real-time budget enforcement to prevent unexpected bills.
- **Resilience**: Automatic fallbacks, circuit breakers, and quality gates.

### 🔑 Key Features

- **🚀 Local-First Architecture**: Handles ~90% of traffic locally. Only "Critical" or "High Complexity" tasks escalate to cloud models.
- **🛡️ Cloud Gating**: Strict control over cloud access. If the internet is down, auth fails (401), or `ENABLE_OPENAI_FALLBACK=0`, the router **blocks** cloud calls and forces local handling with **Complexity Boost**.
- **✅ Cascade Quality Gate**: Evaluates local model responses. If they fail specific criteria (e.g., missing code blocks, no structured data), the router automatically escalates to a smarter model (if allowed).
- **🔄 Universal API**: Drop-in compatible with OpenAI SDKs (`/v1/chat/completions`).
- **⚡ Performance**: <15ms routing overhead.
- **📊 Observability**: Structured JSON logs with `cloud_available` and `escalation_reason` tags. Built-in metrics dashboard.

---

## 🏗️ Architecture

The system uses a **LangGraph** workflow with a strict **Local-First** policy:

1.  **Request Ingestion**: Standard OpenAI Chat Completions API.
2.  **Cloud Availability Check**:
    - Checks Config (`ENABLE_OPENAI_FALLBACK`).
    - Checks API Key presence.
    - Checks Auth Status Cache (prevents 401 spam).
3.  **Classification & Routing**:
    - If Cloud **Unavailable**: Forces local models + **Complexity Boost** (prefers larger local models like DeepSeek-33B).
    - If Cloud **Available**: Classifies into `Low`, `Medium`, `High`, `Critical`.
4.  **Model Invocation & Quality Gate**:
    - **Attempt 1**: Primary Model (usually Local).
    - **Quality Check**: Validates output (Code blocks present? JSON valid?).
    - **Attempt 2 (Escalation)**: If Quality Check fails + Cloud Available -> Escalate to GPT-4o/O3.
    - **Fallback**: If Cloud Auth fails dynamically, fallback to local immediately.
5.  **Metrics & Logging**: Telemetry recorded for every request.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com/) running locally (default: `localhost:11434`).
- (Optional) OpenAI API Key for fallback.

### Installation

1.  **Clone the Repo**
    ```bash
    git clone https://github.com/your-org/ai-router.git
    cd ai-router
    ```

2.  **Quick Setup (Makefile)**
    ```bash
    make venv      # Create virtualenv and install deps
    make verify    # Run full verification suite (Lint + Unit + Resilience)
    ```

3.  **Configure Environment**
    ```bash
    cp config/.env.example config/.env.local
    # Edit config/.env.local to set your keys
    ```

4.  **Run Server**
    ```bash
    make run-dev
    # API: http://localhost:8082
    # Dashboard: http://localhost:8082/guide
    ```

---

## ⚙️ Configuration

### 1. Cloud Fallback Toggle
Control cloud usage instantly via environment variables (no restart needed for policy changes, just restart service to picking up env):

```bash
# Enable fallback (requires Key)
make cloud-on

# Disable fallback (Forces Local-Only Mode)
make cloud-off
```

### 2. Routing Policy (`router_config.yaml`)

Define behavior in `config/router_config.yaml`:

```yaml
routing_policy:
  code_gen:
    low: ["local-code"]           # Llama 3.1 8B
    high: ["deepseek-coder"]      # DeepSeek 33B (Local)
    critical: ["gpt-4o-mini"]     # Cloud Escalation
```

---

## 🛠 Development & Verification ("Senior Dev Standard")

We enforce a strict "Verify First" workflow. Never push broken code.

### ✅ Full Verification Suite
Before committing, always run:
```bash
make verify
```
This runs:
1.  **Linter** (Ruff) - Checks style and unused imports.
2.  **Auth Validation** - Verifies keys are present (if needed).
3.  **Unit Tests** (Pytest) - Runs 100+ tests including:
    - Routing Logic
    - Cloud Gating
    - Model Resolution
4.  **Resilience Tests** - Simulates chaos (auth failures, provider down).

### Testing Commands
| Command | Description |
|---|---|
| `make test` | Run strict unit tests. |
| `make test-chaos` | Run chaos engineering tests. |
| `make smoke` | Run E2E smoke tests against running server. |
| `make cloud-status` | Check if cloud is enabled/configured. |

---


## 📦 Deployment (Coolify)

Ready for production? We support one-click deployment on **Coolify** with **Cloudflare Tunnels**.
See [DEPLOYMENT.md](DEPLOYMENT.md) for the full guide on setting up:
- 🏭 Production Docker Stack
- 🛡️ Cloudflare Tunnel (Access from anywhere)
- 🧠 Local GPU Queue (Ollama)

---

## 🤝 Contribution

See [AGENTS.md](AGENTS.md) for LLM Agent guidelines.
See [CONTRIBUTING.md](CONTRIBUTING.md) for human developer guidelines.

---

**Built for Resilience.**
*Status: Production Ready | Coverage: 100%*
