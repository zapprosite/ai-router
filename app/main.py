from fastapi import FastAPI, Response, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from contextlib import asynccontextmanager
import os, time, json, logging

# ---------- Structured Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("ai-router")

from graph.router import build_compiled_router, CONFIG, REG, debug_router_decision

# ---------- Startup Validation (Fail Fast) ----------
REQUIRED_MODELS = ["local-chat", "local-code", "gpt-4.1-nano", "gpt-4o-mini", "gpt-4.1", "o3", "gpt-5.1-high", "gpt-5.1-codex-mini", "gpt-5.1-codex-high"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup/shutdown."""
    # Startup
    missing = [m for m in REQUIRED_MODELS if m not in REG]
    if missing:
        logger.critical(f"FATAL: Missing required models in config: {missing}")
        raise RuntimeError(f"Config validation failed. Missing models: {missing}")
    logger.info(f"Config validated. {len(REG)} models registered.")
    yield
    # Shutdown (cleanup if needed)
    logger.info("Shutting down AI Router.")

app = FastAPI(title="AI Router (LangGraph/LangChain 1.0)", version="1.0.0", lifespan=lifespan)

# Global Exception Handler for clean 500s
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    return Response(
        content=json.dumps({
            "error": "Internal Server Error",
            "detail": str(exc),
            "type": type(exc).__name__
        }),
        status_code=500,
        media_type="application/json"
    )

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Allow public access to dashboard, static files, and health checks
    if request.url.path.startswith(("/guide", "/public", "/healthz", "/docs", "/openapi.json")) or request.url.path == "/":
        return await call_next(request)
    
    # Check for API Key
    expected_key = os.getenv("AI_ROUTER_API_KEY")
    if expected_key:
        client_key = request.headers.get("X-API-Key")
        if not client_key or client_key != expected_key:
            return Response(content="Unauthorized: Invalid or missing API Key", status_code=401)
            
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class Message(BaseModel):
    role: Literal["system","user","assistant","tool"] = "user"
    content: str = Field(..., min_length=1, max_length=200000)

class RouteRequest(BaseModel):
    messages: List[Message]
    latency_ms_max: Optional[int] = 0
    budget: Optional[Literal["low","balanced","high"]] = "balanced"
    prefer_code: Optional[bool] = False
    critical: Optional[bool] = False  # NEW: Explicit flag for critical routing

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

# --- /debug/router_decision: introspect routing decision ---
class DebugRouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Sample prompt to analyze")

@app.post("/debug/router_decision")
def debug_route_decision(req: DebugRouteRequest):
    """
    Debug endpoint: Show what routing decision would be made for a prompt.
    
    Returns:
    - routing_meta: {task, complexity, confidence, classifier_used}
    - selected_model_id: The model that would be selected
    - fallback_available: Whether cloud fallback is enabled
    """
    messages = [{"role": "user", "content": req.prompt}]
    return debug_router_decision(messages)

# --- /debug/metrics: Cost & Usage Stats ---
@app.get("/debug/metrics")
def get_metrics():
    """
    Returns aggregated metrics from the current session (or persisted logs).
    - Total Requests
    - Total Cost (Est)
    - Average Latency
    - Model Distribution
    """
    log_file = "logs/metrics.jsonl"
    if not os.path.exists(log_file):
        return {"error": "No metrics logs found yet."}
    
    stats = {
        "total_requests": 0,
        "total_cost_usd": 0.0,
        "total_tokens": 0,
        "latencies": [],
        "models": {},
        "tiers": {}
    }
    
    try:
        # Read last 1000 lines efficiently (or just all for now, assuming rotation)
        with open(log_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    stats["total_requests"] += 1
                    stats["total_cost_usd"] += data.get("cost_est_usd", 0)
                    stats["total_tokens"] += data.get("tokens_total", 0)
                    stats["latencies"].append(data.get("latency_ms", 0))
                    
                    mid = data.get("model_id", "unknown")
                    stats["models"][mid] = stats["models"].get(mid, 0) + 1
                    
                    tier = data.get("tier", "unknown")
                    stats["tiers"][tier] = stats["tiers"].get(tier, 0) + 1
                except:
                    continue
                    
        # Averages
        avg_lat = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
        stats["avg_latency_ms"] = int(avg_lat)
        del stats["latencies"] # Keep payload clean
        
        stats["total_cost_usd"] = round(stats["total_cost_usd"], 6)
        
        return stats
    except Exception as e:
        return {"error": str(e)}

# --- /v1/models (compat OpenAI) ---
@app.get("/v1/models")
def list_models_openai():
    from graph.router import CONFIG_PATH
    data = []
    import time
    try:
        cfg = yaml.safe_load(open(CONFIG_PATH, "r"))
        for m in (cfg.get("models", []) if isinstance(cfg, dict) else []):
            data.append({
                "id": m.get("id") or m.get("name"),
                "object": "model",
                "owned_by": m.get("provider", "unknown"),
                "created": int(time.time()),
            })
    except Exception:
        # tolerate missing/invalid config on cold start; still expose router-auto
        pass
    # Ensure logical router model is present for OpenAI-compat clients
    if not any((d.get("id") == "router-auto") for d in data):
        data.append({
            "id": "router-auto",
            "object": "model",
            "owned_by": "router",
            "created": int(time.time()),
        })
    return {"object": "list", "data": data}

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
        "critical": bool(req.critical),
        "_latency_start": t0,
    }
    try:
        out = router_app.invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    out["usage"]["latency_ms_router"] = int((time.perf_counter() - t0) * 1000)
    logger.info(json.dumps({"evt":"route_done","model":out["usage"]["resolved_model_id"],"lat_ms":out["usage"]["latency_ms_router"],"critical":state["critical"]}))
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
