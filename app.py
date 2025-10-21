from fastapi import FastAPI
from typing import List, Dict

try:
    app  # type: ignore
except NameError:
    app = FastAPI(title="ai-router", version="0.1.0")

def _fallback_models() -> List[Dict]:
    return [{"id": x} for x in ["qwen3-8b","qwen3-14b","gpt-5-nano","gpt-5-mini","gpt-5-codex","gpt-5-high"]]

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/v1/models")
def v1_models():
    try:
        import router_graph  # type: ignore
        if hasattr(router_graph, "get_models"):
            data = router_graph.get_models()  # type: ignore
            if isinstance(data, list) and all(isinstance(x, dict) and "id" in x for x in data):
                return {"data": data}
    except Exception:
        pass
    return {"data": _fallback_models()}
