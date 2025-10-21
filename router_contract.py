from __future__ import annotations
from typing import Dict, Any
import math, os, re

# Thresholds per AGENTS.md
DOCS_SMALL = int(os.getenv("ROUTER_DOCS_SMALL", "600"))
DOCS_MED   = int(os.getenv("ROUTER_DOCS_MED",   "3000"))
CODE_SMALL = int(os.getenv("ROUTER_CODE_SMALL", "400"))
CODE_MED   = int(os.getenv("ROUTER_CODE_MED",   "2000"))

# Default model ids per AGENTS.md
LOCAL_DOCS = os.getenv("LOCAL_CHAT_MODEL", "qwen3:8b")
LOCAL_CODE = os.getenv("LOCAL_CODE_MODEL", "qwen3:14b")
CLOUD_DOCS = os.getenv("CLOUD_DOCS_MODEL", "gpt-5-mini")
CLOUD_CODE = os.getenv("CLOUD_CODE_MODEL", "gpt-5-codex")
CLOUD_HIGH = os.getenv("CLOUD_HIGH_MODEL", "gpt-5-high")

CODE_HINTS = re.compile(r"```|class\s+\w+:|def\s+\w+\(|function\s+\w+\(|#include\s|SELECT\s|INSERT\s|<\w+>|curl\s-|\bpytest\b|\basync\s+def\b|\bconst\b|\bvar\b|\blet\b", re.I)
DOCS_HINTS = re.compile(r"\b(resumo|explicar|documentar|política|processo|brief|proposta|análise)\b", re.I)
RISKY      = re.compile(r"\b(rm\s+-rf|DROP\s+TABLE|/etc/passwd|/var/run/docker\.sock|sudo\s|127\.0\.0\.1|localhost|file:\/\/)\b", re.I)

def approx_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return math.ceil(len(text)/4)

def classify_task(text: str) -> Dict[str, Any]:
    is_code = bool(CODE_HINTS.search(text))
    is_docs = bool(DOCS_HINTS.search(text))
    task_type = "code" if is_code and not is_docs else "docs"
    tk = approx_tokens(text)
    lines = text.count("\n") + 1
    code_blocks = text.count("```")
    asks = len(re.findall(r"\b(e|and|;)\b", text))
    complexity = "high" if code_blocks >= 2 or lines > 150 or tk > 2500 or asks > 6 else ("medium" if lines > 40 or tk > 800 else "low")
    return {"task_type": task_type, "complexity": complexity, "needs_tools": False}

def select_model(task_type: str, tokens: int, complexity: str) -> str:
    if task_type == "code":
        if tokens <= CODE_SMALL and complexity != "high":
            return LOCAL_CODE
        elif tokens <= CODE_MED:
            return CLOUD_CODE
        else:
            return CLOUD_HIGH
    else:
        if tokens <= DOCS_SMALL and complexity != "high":
            return LOCAL_DOCS
        elif tokens <= DOCS_MED:
            return CLOUD_DOCS
        else:
            return CLOUD_HIGH

def provider_of(model_id: str) -> str:
    return "local" if ":" in model_id and model_id.split(":",1)[0] in ("qwen3","qwen","llama","phi","mistral") else "cloud"

def route_headers(text: str) -> Dict[str, Any]:
    cls = classify_task(text)
    tk = approx_tokens(text)
    model = select_model(cls["task_type"], tk, cls["complexity"])
    route = provider_of(model)
    # Promote if risky or ambiguous
    if RISKY.search(text) or text.count("\n") > 120:
        if route == "local":
            model = CLOUD_CODE if cls["task_type"] == "code" else CLOUD_DOCS
            route = "cloud"
        elif model in (CLOUD_CODE, CLOUD_DOCS):
            model = CLOUD_HIGH
    return {
        "route": route,
        "model": model,
        "task": cls["task_type"],
        "complexity": cls["complexity"],
        "approx_tokens": tk,
    }

def format_header(h: Dict[str, Any]) -> str:
    return f"[route:{h['route']}] [model:{h['model']}] [task:{h['task']}] [complexity:{h['complexity']}]"

