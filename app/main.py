from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
import os, time

from graph.router import build_compiled_router

app = FastAPI(title="AI Router (LangGraph/LangChain 1.0)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class Message(BaseModel):
    role: Literal["system","user","assistant","tool"] = "user"
    content: str = Field(..., min_length=1)

class RouteRequest(BaseModel):
    messages: List[Message]
    latency_ms_max: Optional[int] = 0
    budget: Optional[Literal["low","balanced","high"]] = "balanced"
    prefer_code: Optional[bool] = False

router_app = build_compiled_router()

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pathlib, hashlib, yaml

# montar /public para servir o painel
try:
    app.mount("/public", StaticFiles(directory="public"), name="public")
except Exception:
    pass

# --- /guide (abre o painel) ---
@app.get("/guide")
def guide():
    fp = pathlib.Path(__file__).resolve().parents[1] / "public" / "Guide.html"
    if fp.exists(): return FileResponse(str(fp))
    return {"error":"Guide.html não encontrado. Gere em /public/Guide.html"}

# --- /debug/where: módulos, registry, env ---
@app.get("/debug/where")
def debug_where():
    def sha16(path: str)->str:
        try:
            return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]
        except Exception:
            return "NA"
    mods={}
    for mname in ("app.main","graph.router","providers.ollama_client","providers.openai_client"):
        try:
            import importlib, pathlib
            m = importlib.import_module(mname)
            f = pathlib.Path(getattr(m,"__file__","")).resolve()
            mods[mname] = {"file": str(f), "sha16": sha16(str(f))}
        except Exception as e:
            mods[mname] = {"error": str(e)}
    # registry pelo YAML
    from graph.router import CONFIG_PATH
    cfgp = pathlib.Path(CONFIG_PATH).resolve()
    reg = []
    try:
        cfg = yaml.safe_load(cfgp.read_text())
        for m in cfg.get("models",[]):
            reg.append(m)
    except Exception as e:
        reg = [{"error": str(e)}]
    return {
        "ok": True,
        "config_path": str(cfgp),
        "models": reg,
        "modules": mods,
        "env_models": {
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL"),
            "OPENAI_ORGANIZATION": os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG"),
            "OPENAI_PROJECT": os.getenv("OPENAI_PROJECT"),
            "OPENAI_API_KEY_SET": bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_TIER2")),
        },
    }

# --- /v1/models (compat OpenAI) ---
@app.get("/v1/models")
def list_models_openai():
    from graph.router import CONFIG_PATH
    cfg = yaml.safe_load(open(CONFIG_PATH,"r"))
    data=[]
    import time
    for m in cfg.get("models",[]):
        data.append({
            "id": m.get("id") or m.get("name"),
            "object":"model",
            "owned_by": m.get("provider","unknown"),
            "created": int(time.time())
        })
    # Ensure logical router model is present for OpenAI-compat clients
    if not any((d.get("id") == "router-auto") for d in data):
        data.append({
            "id": "router-auto",
            "object": "model",
            "owned_by": "router",
            "created": int(time.time()),
        })
    return {"object":"list","data":data}

# --- Ações: smoke e teste de modelo ---
from pydantic import BaseModel
class TestReq(BaseModel):
    model: str
    prompt: str | None = None

@app.post("/actions/smoke")
def actions_smoke():
    # roda 2 smokes rápidos através do grafo (roteador real)
    st1 = {
        "messages":[{"role":"user","content":"Explique HVAC em 1 frase."}],
        "budget":"balanced","prefer_code":False
    }
    st2 = {
        "messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],
        "budget":"low","prefer_code":True
    }
    out1 = router_app.invoke(st1)
    out2 = router_app.invoke(st2)
    return {"ok":True,"smoke":[out1,out2]}

@app.post("/actions/test")
def actions_test(body: TestReq):
    # invoca modelo específico direto (sem roteador)
    from providers.ollama_client import make_ollama
    from providers.openai_client import make_openai
    name = body.model
    prompt = body.prompt or ("Explique HVAC em 1 frase." if "codex" not in name and "coder" not in name else "Escreva uma função Python soma(n1,n2) com docstring.")
    # heurística rápida: se contém ":" é nome de modelo Ollama; se começa com gpt-5* é OpenAI
    if ":" in name:
        chain = make_ollama(name, 0.1)
    else:
        chain = make_openai(name, 0.0)
    try:
        out = chain.invoke({"messages":[{"role":"user","content":prompt}]})
        return {"ok":True,"model":name,"preview":str(out)[:500]}
    except Exception as e:
        return {"ok":False,"model":name,"error":str(e)}


@app.get("/healthz")
def healthz(): return {"ok": True}

# --- OpenAI shim: /v1/chat/completions ---
class _ChatMsg(BaseModel):
    role: Literal["system","user","assistant","tool"]
    content: str

class _ChatReq(BaseModel):
    model: str
    messages: List[_ChatMsg]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = None

@app.post("/v1/chat/completions")
def _chat_completions(body: _ChatReq):
    # Minimal heuristic to hint code preference
    txt = "\n".join([m.content for m in body.messages if m.role in ("user","system")])
    prefer_code = ("```" in txt) or ("def " in txt) or ("class " in txt) or ("traceback" in txt)
    try:
        out = router_app.invoke({
            "messages": [m.model_dump() for m in body.messages],
            "budget": "balanced",
            "prefer_code": bool(prefer_code),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    content = (
        out.get("output")
        or out.get("content")
        or out.get("text")
        or (out.get("message") or {}).get("content")
        or ""
    )
    model_used = (out.get("usage") or {}).get("resolved_model_id") or "router-auto"
    created = int(time.time())
    return {
        "id": f"chatcmpl-{created}",
        "object": "chat.completion",
        "created": created,
        "model": model_used,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": out.get("usage", {}),
    }

@app.post("/route")
def route(req: RouteRequest) -> Dict[str, Any]:
    t0 = time.perf_counter()
    state = {
        "messages": [m.model_dump() for m in req.messages],
        "latency_ms_max": req.latency_ms_max or 0,
        "budget": req.budget or "balanced",
        "prefer_code": bool(req.prefer_code),
    }
    try:
        out = router_app.invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    out["usage"]["latency_ms_router"] = int((time.perf_counter() - t0) * 1000)
    print({"evt":"route_done","model":out["usage"]["resolved_model_id"],"lat_ms":out["usage"]["latency_ms_router"]})
    return out


# --- HEAD compat ---
@app.head("/healthz")
def _healthz_head():
    return Response(status_code=200)

@app.head("/guide")
def _guide_head():
    return Response(status_code=200)


# --- raiz: redireciona para o painel ---
@app.get("/")
def _root():
    return RedirectResponse(url="/guide", status_code=302)

@app.head("/")
def _root_head():
    return Response(status_code=302, headers={"Location": "/guide"})
