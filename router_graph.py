# router_graph utilitário mínimo e idempotente
from typing import List, Dict

def get_models() -> List[Dict]:
    # Ajuste livre futuramente: detectar ollama/cloud em runtime
    return [
        {"id": "qwen3-8b"},
        {"id": "qwen3-14b"},
        {"id": "gpt-5-nano"},
        {"id": "gpt-5-mini"},
        {"id": "gpt-5-codex"},
        {"id": "gpt-5-high"},
    ]
