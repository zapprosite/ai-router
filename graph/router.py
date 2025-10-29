import os, re, math, time, yaml, pathlib
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableBranch, RunnableLambda

from providers.openai_client import make_openai
from providers.ollama_client import make_ollama

# ---------- Config ----------
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = os.getenv("ROUTER_CONFIG", str(ROOT / "config" / "router_config.yaml"))
CONFIG = yaml.safe_load(open(CONFIG_PATH, "r"))

REG = {m["id"]: m for m in CONFIG["models"]}
TH  = CONFIG["thresholds"]
BUD = CONFIG["budget"]
SLA = CONFIG.get("sla", {"enabled": True, "latency_sec": 6})

CODE_HINT_RE    = re.compile(TH["code_hint_regex"], re.I)
CODE_COMPLEX_RE = re.compile(TH["code_complex_regex"], re.I)

def _has_openai()->bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_TIER2"))

def _fallback_enabled()->bool:
    # Fallback only when explicitly enabled AND key exists
    if str(os.getenv("ENABLE_OPENAI_FALLBACK", "0")).strip() != "1":
        return False
    return _has_openai()

# ---------- State ----------
class RouterState(TypedDict, total=False):
    messages: List[Dict[str, str]]
    latency_ms_max: int
    budget: str
    prefer_code: bool
    model_id: str
    output: str
    usage: Dict[str, Any]

# ---------- Utils ----------
def join_messages(msgs: List[Dict[str,str]]) -> str:
    return "\n".join([f'{m.get("role","user")}: {m.get("content","")}' for m in msgs])

def est_tokens(txt: str) -> int:
    return max(1, math.ceil(len(txt) / 4))

def is_long_input(messages: List[Dict[str,str]]) -> bool:
    return est_tokens(join_messages(messages)) > int(TH["long_tokens"])

def is_code_simple(messages: List[Dict[str,str]]) -> bool:
    txt = join_messages(messages)
    return bool(CODE_HINT_RE.search(txt)) and est_tokens(txt) <= int(TH["code_simple_max_tokens"])

def is_code_complex(messages: List[Dict[str,str]]) -> bool:
    txt = join_messages(messages)
    return bool(CODE_COMPLEX_RE.search(txt)) or (bool(CODE_HINT_RE.search(txt)) and est_tokens(txt) > int(TH["code_simple_max_tokens"]))

def pick_model_id(state: RouterState) -> str:
    msgs = state["messages"]
    budget = (state.get("budget") or "balanced").lower()
    prefer_code = bool(state.get("prefer_code", False))
    prefer_cheap = bool(BUD.get(budget, {}).get("prefer_cheap", True))
    # openai_on no longer drives routing choice; local-first always
    if is_long_input(msgs):
        # Inputs muito longos: mantenha local-first (DeepSeek 16B)
        return "deepseek-coder-v2-16b"

    if prefer_code or is_code_complex(msgs):
        return "deepseek-coder-v2-16b"

    if is_code_simple(msgs):
        return "llama-3.1-8b-instruct"

    if est_tokens(join_messages(msgs)) <= 300:
        return "llama-3.1-8b-instruct"

    return "llama-3.1-8b-instruct"

# ---------- Chains ----------
def _build_chain(model_id: str):
    meta = REG[model_id]
    if meta["provider"] == "ollama":
        return make_ollama(meta["name"], temperature=float(os.getenv("OLLAMA_TEMPERATURE","0.1")))
    else:
        return make_openai(meta["name"], temperature=float(os.getenv("OPENAI_TEMPERATURE","0.0")))

CHAIN_Q8   = _build_chain("llama-3.1-8b-instruct")
CHAIN_Q14  = _build_chain("deepseek-coder-v2-16b")
CHAIN_NANO = _build_chain("gpt-5-nano")
CHAIN_MINI = _build_chain("gpt-5-mini")
CHAIN_CODEX= _build_chain("gpt-5-codex")
CHAIN_HIGH = _build_chain("gpt-5-high")

Q14_F  = CHAIN_Q14.with_fallbacks([CHAIN_CODEX])          # deepseek -> codex
Q8_F   = CHAIN_Q8.with_fallbacks([Q14_F])                 # llama8 -> deepseek -> codex
NANO_F = CHAIN_NANO.with_fallbacks([CHAIN_MINI])          # nano -> mini

BRANCH = RunnableBranch(
    (lambda x: x["model_id"] == "llama-3.1-8b-instruct", Q8_F),
    (lambda x: x["model_id"] == "deepseek-coder-v2-16b", Q14_F),
    (lambda x: x["model_id"] == "gpt-5-nano", NANO_F),
    (lambda x: x["model_id"] == "gpt-5-mini", CHAIN_MINI),
    (lambda x: x["model_id"] == "gpt-5-codex", CHAIN_CODEX),
    (lambda x: x["model_id"] == "gpt-5-high", CHAIN_HIGH),
    CHAIN_MINI,
)

def _sla_wrap(runnable):
    if not SLA.get("enabled", True):
        return runnable
    threshold = float(SLA.get("latency_sec", 6))
    if _fallback_enabled():
        cloud_pref = {
            "llama-3.1-8b-instruct": (CHAIN_MINI,),
            "deepseek-coder-v2-16b": (CHAIN_CODEX, CHAIN_MINI),
        }
    else:
        cloud_pref = {}
    def _call(x: Dict[str,Any]):
        start = time.perf_counter()
        try:
            out = BRANCH.invoke(x)
            took = time.perf_counter() - start
            prefs = cloud_pref.get(x["model_id"], tuple())
            if prefs and took > threshold:
                for c in prefs:
                    try:
                        return c.invoke({"messages": x["messages"]})
                    except Exception:
                        continue
            return out
        except Exception:
            prefs = cloud_pref.get(x["model_id"], tuple())
            for c in prefs:
                try:
                    return c.invoke({"messages": x["messages"]})
                except Exception:
                    continue
            raise
    return RunnableLambda(_call)

class RouterState(TypedDict, total=False):
    messages: List[Dict[str, str]]
    latency_ms_max: int
    budget: str
    prefer_code: bool
    model_id: str
    output: str
    usage: Dict[str, Any]

def _node_route(state: RouterState) -> RouterState:
    return {"model_id": pick_model_id(state)}

def _node_invoke(state: RouterState) -> RouterState:
    wrapped = _sla_wrap(BRANCH)
    out = wrapped.invoke({"messages": state["messages"], "model_id": state["model_id"]})
    prompt = join_messages(state["messages"])
    usage = {
        "prompt_tokens_est": est_tokens(prompt),
        "completion_tokens_est": est_tokens(out),
        "total_tokens_est": est_tokens(prompt) + est_tokens(out),
        "resolved_model_id": state["model_id"],
        "config_path": CONFIG_PATH,
    }
    return {"output": out, "usage": usage}

def build_compiled_router():
    g = StateGraph(RouterState)
    g.add_node("route", _node_route)
    g.add_node("invoke", _node_invoke)
    g.set_entry_point("route")
    g.add_edge("route", "invoke")
    g.add_edge("invoke", END)
    return g.compile()
