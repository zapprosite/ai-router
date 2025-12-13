# Changelog

All notable changes to this project will be documented in this file.

## [2.5.0] - 2025-12-09

### 🚀 Major Features
- **Tier 5 Integration**: Added support for `gpt-5.2-high` (Creative/Reasoning) and `gpt-5.2-codex` (Engineering).
- **Stability Layer**: Introduced a transparent fallback mechanism. If a bleeding-edge model is unavailable, the router automatically maps it to the best available stable model (e.g., `gpt-4.1`).
- **Observability Suite**: Real-time metrics endpoint (`/debug/metrics`), structured JSON logging, and CLI cost reporting script.
- **Mission Control V2**: Completely redesigned `Guide.html` with a futuristic Cyberpunk HUD, real-time logs, and a Command Deck.

### 🛠️ Improvements
- **Unified Port**: Standardized entire application on port `8082`.
- **Docs**: "Champion" level documentation overhaul. `sudo tee` secrets installation and clear architectural guides.
- **Testing**: Updated test suite (40 unit tests + E2E smoke) to validate new Tier 5 routing logic.

## [2.0.0] - 2025-10-15
- Initial Stable Release.
- Multi-tier routing (Llama 3.1 -> GPT-4).
- Cost Guard implementation.

## [1.0.0] - 2024-01-01
- Prototype version.
