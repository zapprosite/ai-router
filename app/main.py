import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# ---------- Structured Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("ai-router")

# ---------- Prometheus & Rate Limiting ----------
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


from graph.router import REG, build_compiled_router, debug_router_decision

# ---------- Startup Validation (Fail Fast) ----------
REQUIRED_MODELS = ["local-chat", "local-code", "gpt-4.1-nano", "gpt-4o-mini", "gpt-4.1", "o3", "gpt-5.2-high", "gpt-5.2-codex-mini", "gpt-5.2-codex-high"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup/shutdown."""
    # Startup: Validate Models
    # We only validate "REQUIRED" models if we are not in a pure test env with mocks,
    # or we try to be smart about it.
    
    # Check if we are in test mode (skip real validation to avoid blocking build)
    is_test = os.getenv("AI_ROUTER_ENV") == "test"
    
    if not is_test:
        from providers.ollama_client import validate_model_id as validate_ollama
        from providers.openai_client import validate_model_id as validate_openai
        
    if not is_test:
        from providers.ollama_client import validate_model_id as validate_ollama
        from providers.openai_client import validate_model_id as validate_openai
        
        # Iterate over registered models in REG (which is dict of id -> meta)
        for model in REG.values():
            mid = model["id"]
            mname = model["name"]
            provider = model.get("provider", "ollama")
            
            # Skip validation if provider keys missing (cloud gating)
            # But if keys exist, we MUST validate.
            
            valid = False
            if provider == "ollama":
                valid = validate_ollama(mname)
            elif provider == "openai":
                valid = validate_openai(mname)
            
            if not valid:
                logger.warning(f"Startup Warning: Model '{mid}' (name={mname}) not found in {provider}. Calls may fail.")
                # We don't crash hard for everything, but maybe for critical local ones?
                if mid in ["local-chat", "local-code"]:
                     # For local, if missing, it's a setup issue.
                     # But we allow proceed to avoid breaking "cloud-only" setups or vice versa.
                     pass

    logger.info(f"Config validated. {len(REG)} models registered.")
    yield
    # Shutdown (cleanup if needed)
    logger.info("Shutting down AI Router.")

app = FastAPI(title="AI Router (LangGraph/LangChain 1.0)", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Init Metrics
Instrumentator().instrument(app).expose(app)

# Global Exception Handler for clean 500s
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
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
    if request.url.path.startswith(("/guide", "/public", "/healthz", "/docs", "/openapi.json", "/dashboard.html")) or request.url.path == "/":
        return await call_next(request)
    
    # Check for API Key
    expected_key = os.getenv("AI_ROUTER_API_KEY")
    if expected_key:
        # 1. Try X-API-Key
        client_key = request.headers.get("X-API-Key")
        
        # 2. Try Authorization header
        if not client_key:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                if auth_header.startswith("Bearer "):
                    client_key = auth_header[7:]  # Strip "Bearer "
                else:
                    client_key = auth_header  # Use raw token
        
        # Log auth attempt (masked)
        has_auth = bool(client_key)
        logger.info(f"Auth request: path={request.url.path} auth_provided={has_auth}")

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

import hashlib
import pathlib

import yaml
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# montar /public para servir o painel
try:
    app.mount("/public", StaticFiles(directory="public"), name="public")
except Exception as e:
    logger.warning(f"Failed to mount /public: {e}")

# --- /guide (abre o painel) ---
@app.get("/guide")
def guide():
    fp = pathlib.Path(__file__).resolve().parents[1] / "public" / "Guide.html"
    if fp.exists(): return FileResponse(str(fp))
    return {"error":"Guide.html não encontrado. Gere em /public/Guide.html"}

# --- /dashboard.html (abre o dashboard) ---
@app.get("/dashboard.html")
def dashboard():
    fp = pathlib.Path(__file__).resolve().parents[1] / "public" / "dashboard.html"
    if fp.exists(): return FileResponse(str(fp), media_type="text/html")
    return {"error":"dashboard.html não encontrado. Gere em /public/dashboard.html"}

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
            import importlib
            import pathlib
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
    # Ensure logical router models are present for OpenAI-compat clients
    virtual_models = ["router-auto", "router-local", "router-code"]
    existing_ids = {d.get("id") for d in data}
    
    for vm in virtual_models:
        if vm not in existing_ids:
            data.append({
                "id": vm,
                "object": "model",
                "owned_by": "ai-router",
                "created": int(time.time()),
            })
    return {"object": "list", "data": data}

# --- Ações: smoke e teste de modelo ---
from pydantic import BaseModel


class TestReq(BaseModel):
    model: str
    prompt: str | None = None

@app.post("/actions/smoke")
async def actions_smoke():
    # roda 2 smokes rápidos através do grafo (roteador real)
    st1 = {
        "messages":[{"role":"user","content":"Explique HVAC em 1 frase."}],
        "budget":"balanced","prefer_code":False
    }
    st2 = {
        "messages":[{"role":"user","content":"Escreva uma função Python soma(n1,n2) com docstring."}],
        "budget":"low","prefer_code":True
    }
    out1 = await router_app.ainvoke(st1)
    out2 = await router_app.ainvoke(st2)
    return {"ok":True,"smoke":[out1,out2]}

@app.post("/actions/test")
async def actions_test(body: TestReq):
    # invoca modelo específico direto (sem roteador)
    from graph.router import resolve_model_alias
    from providers.ollama_client import make_ollama
    from providers.openai_client import make_openai

    name = body.model
    prompt = body.prompt or ("Explique HVAC em 1 frase." if "codex" not in name and "coder" not in name else "Escreva uma função Python soma(n1,n2) com docstring.")
    
    # Resolver alias (ex: gpt-5.2-high -> gpt-4o + params)
    real_id, params, provider = resolve_model_alias(name)

    if provider == "ollama":
        chain = make_ollama(real_id, 0.1)
    else:
        # Passar params resolvidos (reasoning_effort, etc)
        chain = make_openai(real_id, 0.0, params=params)

    try:
        out = await chain.ainvoke({"messages":[{"role":"user","content":prompt}]})
        return {"ok":True,"model":name,"resolved":real_id,"preview":str(out)[:500]}
    except Exception as e:
        return {"ok":False,"model":name,"error":str(e)}


@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/health")
async def health_check():
    """
    Detailed health check including GPU Queue stats.
    Compatible with Coolify health checks.
    """
    from services.gpu_queue import get_queue
    q = await get_queue()
    metrics = await q.get_metrics()
    
    return {
        "status": "ok",
        "service": "ai-router",
        "gpu_queue": metrics
    }


async def _run_router_completion(messages: List[Dict], prefer_code: bool = False, **kwargs) -> Dict:
    """
    Shared utility to invoke the router graph.
    Returns the raw output dictionary from router_app.ainvoke().
    """
    try:
        out = await router_app.ainvoke({
            "messages": messages,
            "budget": "balanced",
            "prefer_code": prefer_code,
        })
        
        # Check for explicitly returned error objects (e.g. from upstream)
        if isinstance(out, dict) and out.get("type") == "upstream_error":
            # Parse status code from error string "Upstream Error 402: ..."
            # Default to 500 if parsing fails
            status = 500
            detail = out.get("error", "Unknown upstream error")
            
            import re
            match = re.search(r"Upstream Error (\d+):", detail)
            if match:
                status = int(match.group(1))
            
            raise HTTPException(status_code=status, detail=detail)
            
        return out
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
@limiter.limit("50/minute")
async def _chat_completions(request: Request, body: _ChatReq):
    # Minimal heuristic to hint code preference
    txt = "\n".join([m.content for m in body.messages if m.role in ("user","system")])
    prefer_code = ("```" in txt) or ("def " in txt) or ("class " in txt) or ("traceback" in txt)
    
    out = await _run_router_completion(
        messages=[m.model_dump() for m in body.messages],
        prefer_code=bool(prefer_code)
    )

    content = (
        out.get("output")
        or out.get("content")
        or out.get("text")
        or (out.get("message") or {}).get("content")
        or ""
    )
    usage_data = out.get("usage") or {}
    model_used = usage_data.get("resolved_model_id") or "router-auto"
    escalated = usage_data.get("escalated", False)
    escalation_reason = usage_data.get("escalation_reason") or ""
    attempts = usage_data.get("attempts", [])
    initial_model = attempts[0].get("model") if attempts else model_used
    
    created = int(time.time())
    response_body = {
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
        "usage": usage_data,
    }
    
    # Return with observability headers
    return Response(
        content=json.dumps(response_body),
        media_type="application/json",
        headers={
            "X-AI-Router-Initial-Model": initial_model,
            "X-AI-Router-Final-Model": model_used,
            "X-AI-Router-Escalated": str(escalated).lower(),
            "X-AI-Router-Escalation-Reason": escalation_reason,
        }
    )

# --- OpenAI Responses API: /v1/responses ---
# Flexible schema to accept both simple strings and complex Codex CLI format
from fastapi.responses import StreamingResponse


class _ResponseReq(BaseModel):
    model: str
    input: Any  # Accept string, list of messages, or Codex-style input items
    stream: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 0.2
    max_output_tokens: Optional[int] = None

def _normalize_content(content: Any) -> str:
    """
    Normalize content field which can be:
    - A simple string
    - An array of content items like [{"type": "input_text", "text": "..."}, ...]
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Concatenate text from all input_text items
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "input_text":
                texts.append(item.get("text", ""))
        return "\n".join(texts)
    return str(content)

def _normalize_input_to_messages(input_data: Any) -> List[Dict[str, str]]:
    """
    Normalize input field which can be:
    - A simple string -> [{"role": "user", "content": input}]
    - A list of message dicts with role/content
    - Codex-style: [{"type": "message", "role": "user", "content": [...]}, ...]
    """
    if isinstance(input_data, str):
        return [{"role": "user", "content": input_data}]
    
    if isinstance(input_data, list):
        messages = []
        for item in input_data:
            if not isinstance(item, dict):
                continue
            
            # Handle Codex-style {type: "message", role: "...", content: [...]}
            if item.get("type") == "message":
                role = item.get("role", "user")
                content = _normalize_content(item.get("content", ""))
                if content:
                    messages.append({"role": role, "content": content})
            # Handle simple {role: "...", content: "..."}
            elif "role" in item and "content" in item:
                role = item.get("role", "user")
                content = _normalize_content(item.get("content", ""))
                if content:
                    messages.append({"role": role, "content": content})
        
        if not messages:
            raise HTTPException(status_code=400, detail="Invalid input format: no valid messages found")
        return messages
    
    raise HTTPException(status_code=400, detail="Invalid input format: expected string or array")

def _sse_event(event: str, data: dict) -> str:
    """Format an SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

@app.post("/v1/responses")
async def _responses_api(body: _ResponseReq, request: Request):
    # Check if streaming is requested
    accept_header = request.headers.get("accept", "")
    stream_requested = body.stream == True or "text/event-stream" in accept_header
    
    # 1. Normalize input -> messages
    messages = _normalize_input_to_messages(body.input)
    txt = "\n".join([m["content"] for m in messages if m["role"] in ("user", "system")])

    # 2. Heuristic for code
    prefer_code = ("```" in txt) or ("def " in txt) or ("class " in txt) or ("traceback" in txt)

    # 3. Invoke Router
    out = await _run_router_completion(
        messages=messages,
        prefer_code=bool(prefer_code)
    )

    # 4. Extract content
    content = (
        out.get("output")
        or out.get("content")
        or out.get("text")
        or (out.get("message") or {}).get("content")
        or ""
    )
    model_used = (out.get("usage") or {}).get("resolved_model_id") or "router-auto"
    created = int(time.time())
    response_id = f"resp-{created}"

    # 5. Build usage with required fields for Codex
    raw_usage = out.get("usage", {})
    usage_obj = {
        "input_tokens": raw_usage.get("prompt_tokens_est", raw_usage.get("input_tokens", 0)),
        "output_tokens": raw_usage.get("completion_tokens_est", raw_usage.get("output_tokens", 0)),
        "total_tokens": raw_usage.get("total_tokens_est", raw_usage.get("total_tokens", 0)),
    }
    # Include extra fields if available
    usage_obj.update({k: v for k, v in raw_usage.items() if k not in usage_obj})

    # 6. Build output item
    output_item = {
        "id": "item_0",
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": content}]
    }

    # 7. Build response object
    response_obj = {
        "id": response_id,
        "object": "response",
        "created": created,
        "status": "completed",
        "model": model_used,
        "output": [output_item],
        "usage": usage_obj
    }

    # 8. Handle streaming or non-streaming response
    if stream_requested:
        def generate_sse():
            seq = 0
            try:
                # Event 1: response.created
                yield _sse_event("response.created", {
                    "type": "response.created",
                    "sequence_number": seq,
                    "response": {
                        "id": response_id,
                        "object": "response",
                        "created": created,
                        "status": "in_progress",
                        "model": model_used,
                        "output": []
                    }
                })
                seq += 1
                
                # Event 2: response.output_item.added (REQUIRED before delta)
                yield _sse_event("response.output_item.added", {
                    "type": "response.output_item.added",
                    "sequence_number": seq,
                    "output_index": 0,
                    "item": {
                        "id": "item_0",
                        "type": "message",
                        "role": "assistant",
                        "status": "in_progress",
                        "content": []
                    }
                })
                seq += 1
                
                # Event 3: response.content_part.added
                yield _sse_event("response.content_part.added", {
                    "type": "response.content_part.added",
                    "sequence_number": seq,
                    "item_id": "item_0",
                    "output_index": 0,
                    "content_index": 0,
                    "part": {"type": "output_text", "text": ""}
                })
                seq += 1
                
                # Event 4: response.output_text.delta (full text as single delta)
                yield _sse_event("response.output_text.delta", {
                    "type": "response.output_text.delta",
                    "sequence_number": seq,
                    "item_id": "item_0",
                    "output_index": 0,
                    "content_index": 0,
                    "delta": content
                })
                seq += 1
                
                # Event 5: response.output_text.done
                yield _sse_event("response.output_text.done", {
                    "type": "response.output_text.done",
                    "sequence_number": seq,
                    "item_id": "item_0",
                    "output_index": 0,
                    "content_index": 0,
                    "text": content
                })
                seq += 1
                
                # Event 6: response.output_item.done
                yield _sse_event("response.output_item.done", {
                    "type": "response.output_item.done",
                    "sequence_number": seq,
                    "output_index": 0,
                    "item": output_item
                })
                seq += 1
                
                # Event 7: response.completed
                yield _sse_event("response.completed", {
                    "type": "response.completed",
                    "sequence_number": seq,
                    "response": response_obj
                })
            except Exception as e:
                # Event: error
                yield _sse_event("error", {
                    "type": "error",
                    "error": {"message": str(e), "type": "internal_error"}
                })
        
        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-AI-Router-Initial-Model": out.get("usage", {}).get("attempts", [{}])[0].get("model", model_used),
                "X-AI-Router-Final-Model": model_used,
                "X-AI-Router-Escalated": str(out.get("usage", {}).get("escalated", False)).lower(),
                "X-AI-Router-Escalation-Reason": out.get("usage", {}).get("escalation_reason") or "",
            }
        )
    else:
        return response_obj

@app.post("/route")
@limiter.limit("100/minute")
async def route(request: Request, req: RouteRequest) -> Dict[str, Any]:
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
        out = await router_app.ainvoke(state)
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
