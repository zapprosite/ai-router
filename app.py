from fastapi import FastAPI
from typing import List, Dict

# Reuso se "app" já existir no módulo (idempotente)
try:
    app  # type: ignore # noqa
except NameError:
    app = FastAPI(title="ai-router", version="0.1.0")

def _fallback_models() -> List[Dict]:
    # Local-first + cloud conforme AGENTS.md
    static = [
        {"id": "qwen3-8b"}, {"id": "qwen3-14b"},
        {"id": "gpt-5-nano"}, {"id": "gpt-5-mini"},
        {"id": "gpt-5-codex"}, {"id": "gpt-5-high"},
    ]
    return static

def _dynamic_models() -> List[Dict]:
    # Tenta obter do router_graph se existir
    try:
        import router_graph  # type: ignore
        # Preferência por funções ou constantes conhecidas
        if hasattr(router_graph, "get_models"):
            data = router_graph.get_models()  # type: ignore
            if isinstance(data, list) and all(isinstance(x, dict) and "id" in x for x in data):
                return data
        if hasattr(router_graph, "MODEL_REGISTRY"):
            reg = getattr(router_graph, "MODEL_REGISTRY")
            if isinstance(reg, (list, tuple)):
                return [{"id": str(m)} for m in reg]
            if isinstance(reg, dict):
                return [{"id": str(k)} for k in reg.keys()]
    except Exception:
        pass
    return []

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/v1/models")
def v1_models():
    dyn = _dynamic_models()
    data = dyn if dyn else _fallback_models()
    return {"data": data}
