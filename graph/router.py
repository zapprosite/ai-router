"""
AI Router - Automatic Complexity-Aware Multi-LLM Routing

This module implements a zero-configuration router that automatically
infers task type and complexity from prompts, selecting the optimal
model without requiring manual flags like `critical=true` or `budget=high`.

Architecture:
1. classify_prompt() -> RoutingMeta (task, complexity, confidence)
2. select_model_from_policy() -> model_id based on (task, complexity)
3. LLM Judge (optional) -> refinement for ambiguous cases
4. Model invocation with SLA monitoring and fallbacks
"""

import os, re, math, time, yaml, pathlib, logging
from typing import Any, Dict, List, TypedDict, Optional, Tuple
from dataclasses import dataclass, asdict

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableBranch, RunnableLambda

from providers.openai_client import make_openai
from providers.ollama_client import make_ollama
from graph.cost_guard import PRICING_PER_1M, _get_tier_from_model, est_tokens as cost_est_tokens
import uuid, json, datetime

logger = logging.getLogger("ai-router.graph")

# ---------- Config ----------
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = os.getenv("ROUTER_CONFIG", str(ROOT / "config" / "router_config.yaml"))

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)


def _merge_env_config(reg: Dict[str, Any]):
    """Merge environment variables into the model registry."""
    # Ollama Overrides
    if "deepseek-coder-v2-16b" in reg and os.getenv("OLLAMA_CODER_MODEL"):
        reg["deepseek-coder-v2-16b"]["name"] = os.getenv("OLLAMA_CODER_MODEL")
    
    if "llama-3.1-8b-instruct" in reg and os.getenv("OLLAMA_INSTRUCT_MODEL"):
        reg["llama-3.1-8b-instruct"]["name"] = os.getenv("OLLAMA_INSTRUCT_MODEL")

    # OpenAI Overrides
    mapping = {
        "OPENAI_CODE_MINI": "gpt-5.1-codex-mini",
        "OPENAI_CODE_STANDARD": "gpt-5.1-codex",
        "OPENAI_CODE_REASONING": "o3-mini-high",
        "OPENAI_CODE_ELITE": "o3",
        "OPENAI_TEXT_NANO": "gpt-5-nano",
        "OPENAI_TEXT_STANDARD": "gpt-5-mini"
    }

    for env_var, model_id in mapping.items():
        val = os.getenv(env_var)
        if val and model_id in reg:
            reg[model_id]["name"] = val

REG = {m["id"]: m for m in CONFIG["models"]}
_merge_env_config(REG)

TASK_TYPES = CONFIG.get("task_types", {})
COMPLEXITY_SIGNALS = CONFIG.get("complexity_signals", {})
ROUTING_POLICY = CONFIG.get("routing_policy", {})
CLASSIFIER_CFG = CONFIG.get("classifier", {"llm_assisted": False})
SLA = CONFIG.get("sla", {"enabled": True, "latency_sec": 6})

# Legacy thresholds for backwards compatibility
TH = CONFIG.get("thresholds", {})
BUD = CONFIG.get("budget", {})

# Precompile regex patterns for task detection
TASK_PATTERNS = {}
for task_name, task_cfg in TASK_TYPES.items():
    if "regex" in task_cfg:
        TASK_PATTERNS[task_name] = re.compile(task_cfg["regex"], re.I)

COMPLEXITY_PATTERNS = {}
for level, cfg in COMPLEXITY_SIGNALS.items():
    if "regex" in cfg:
        COMPLEXITY_PATTERNS[level] = re.compile(cfg["regex"], re.I)

# ---------- Data Classes ----------
@dataclass
class RoutingMeta:
    """Structured routing metadata inferred from prompt analysis."""
    task: str = "simple_qa"
    complexity: str = "low"
    confidence: float = 1.0
    requires_search: bool = False
    requires_long_context: bool = False
    classifier_used: str = "heuristic"  # "heuristic" or "llm"

# ---------- State ----------
class RouterState(TypedDict, total=False):
    messages: List[Dict[str, str]]
    latency_ms_max: int
    budget: str  # Optional override (backwards compat)
    prefer_code: bool  # Optional override (backwards compat)
    critical: bool  # Optional override (backwards compat)
    
    # New automatic routing fields
    routing_meta: Dict[str, Any]
    model_id: str
    attempts: List[Dict[str, str]]
    output: str
    usage: Dict[str, Any]

# ---------- Utilities ----------
def join_messages(msgs: List[Dict[str, str]]) -> str:
    """Concatenate messages into a single string for analysis."""
    return "\n".join([f'{m.get("role", "user")}: {m.get("content", "")}' for m in msgs])

def est_tokens(txt: str) -> int:
    """Estimate token count (rough heuristic: ~4 chars per token)."""
    return max(1, math.ceil(len(txt) / 4))

def _has_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_TIER2"))

def _is_cloud_available() -> bool:
    """
    Check if cloud models are available.
    Automatic detection: True if keys exist, unless explicitly disabled via env.
    """
    # 1. Check if explicitly disabled (optional override)
    if str(os.getenv("ENABLE_OPENAI_FALLBACK", "")).strip() == "0":
        return False
    # 2. Check if keys exist
    return _has_openai()

# Legacy alias for compatibility
_fallback_enabled = _is_cloud_available

# ---------- AUTOMATIC CLASSIFICATION ----------
def classify_prompt(messages: List[Dict[str, str]]) -> RoutingMeta:
    """
    Automatically classify a prompt into task type and complexity.
    
    This is the core of the zero-config routing: no manual flags needed.
    Uses a combination of:
    1. Keyword matching
    2. Regex pattern detection
    3. Token count analysis
    4. Structural analysis (numbered lists, code blocks, etc.)
    """
    txt = join_messages(messages).lower()
    txt_original = join_messages(messages)
    token_count = est_tokens(txt_original)
    
    # Initialize with defaults
    detected_task = "simple_qa"
    detected_complexity = "low"
    confidence = 0.5
    
    # --- Task Detection (in priority order) ---
    task_scores: Dict[str, float] = {}
    
    for task_name, task_cfg in TASK_TYPES.items():
        score = 0.0
        
        # Keyword matching
        keywords = task_cfg.get("keywords", [])
        for kw in keywords:
            if kw.lower() in txt:
                score += 0.3
        
        # Regex matching (higher weight)
        if task_name in TASK_PATTERNS:
            if TASK_PATTERNS[task_name].search(txt_original):
                score += 0.8
        
        if score > 0:
            task_scores[task_name] = score
    
    # Pick highest scoring task
    if task_scores:
        detected_task = max(task_scores, key=task_scores.get)
        confidence = min(1.0, task_scores[detected_task])
    
    # --- Complexity Detection ---
    # Start with task default complexity
    task_default = TASK_TYPES.get(detected_task, {}).get("complexity_default", "low")
    detected_complexity = task_default
    
    # Critical tasks should ALWAYS be at least their default complexity
    # Do not downgrade system_design, code_crit_debug, or reasoning based on token count
    critical_tasks = ["code_crit_debug", "system_design", "reasoning", "research"]
    
    if detected_task in critical_tasks:
        # These tasks should be at least 'high' complexity by default
        if task_default in ["high", "critical"]:
            detected_complexity = task_default
    else:
        # Adjust based on token count for non-critical tasks
        if token_count < 50:
            detected_complexity = "low"
        elif token_count < 500:
            if detected_complexity == "low":
                detected_complexity = "medium" if detected_task in ["code_gen", "code_review"] else "low"
        elif token_count < 2000:
            detected_complexity = max(detected_complexity, "medium", key=lambda x: ["low", "medium", "high", "critical"].index(x))
        else:
            detected_complexity = max(detected_complexity, "high", key=lambda x: ["low", "medium", "high", "critical"].index(x))

    
    # 2. Complexity pattern matching
    for level, pattern in COMPLEXITY_PATTERNS.items():
        if pattern.search(txt_original):
            if level in ["high", "critical"]:
                detected_complexity = level
                break
    
    # 3. Critical indicators (force escalation)
    critical_signals = COMPLEXITY_SIGNALS.get("critical", {}).get("indicators", [])
    for signal in critical_signals:
        if signal.lower() in txt:
            detected_complexity = "critical"
            confidence = max(confidence, 0.9)
            break
    
    # 4. Stack traces / error messages
    if "traceback" in txt or "exception" in txt or "error:" in txt:
        if detected_task in ["code_gen", "code_review", "simple_qa"]:
            detected_task = "code_crit_debug" if detected_complexity in ["high", "critical"] else "code_review"
            detected_complexity = max(detected_complexity, "medium", key=lambda x: ["low", "medium", "high", "critical"].index(x))
    
    # Determine if long context is needed
    requires_long_context = token_count > 4000
    
    return RoutingMeta(
        task=detected_task,
        complexity=detected_complexity,
        confidence=confidence,
        requires_search=False,  # Could be extended for RAG
        requires_long_context=requires_long_context,
        classifier_used="heuristic"
    )

def classify_prompt_with_llm(messages: List[Dict[str, str]], heuristic_meta: RoutingMeta) -> RoutingMeta:
    """
    Use an LLM to refine classification when heuristics are uncertain.
    
    Only called when:
    1. LLM-assisted classification is enabled
    2. Heuristic confidence is below threshold
    3. OpenAI fallback is available
    """
    if not CLASSIFIER_CFG.get("llm_assisted", False):
        return heuristic_meta
    
    threshold = CLASSIFIER_CFG.get("heuristic_confidence_threshold", 0.7)
    if heuristic_meta.confidence >= threshold:
        return heuristic_meta
    
    if not _fallback_enabled():
        return heuristic_meta
    
    try:
        prompt_text = join_messages(messages)[:2000]
        template = CLASSIFIER_CFG.get("prompt_template", "Classify: {prompt}")
        classifier_prompt = template.format(prompt=prompt_text)
        
        # Use the configured classifier model
        model_id = CLASSIFIER_CFG.get("llm_model", "gpt-5-nano")
        chain = _build_chain(model_id) if model_id in REG else _build_chain("gpt-5-nano")
        
        result = chain.invoke({"messages": [{"role": "user", "content": classifier_prompt}]})
        result_str = str(result).upper()
        
        # Parse response
        task_match = re.search(r"TASK:\s*(\w+)", result_str)
        complexity_match = re.search(r"COMPLEXITY:\s*(\w+)", result_str)
        
        if task_match and complexity_match:
            task = task_match.group(1).lower()
            complexity = complexity_match.group(1).lower()
            
            # Validate against known values
            if task in TASK_TYPES:
                heuristic_meta.task = task
            if complexity in ["low", "medium", "high", "critical"]:
                heuristic_meta.complexity = complexity
            
            heuristic_meta.classifier_used = "llm"
            heuristic_meta.confidence = 0.9
        
    except Exception as e:
        logger.warning(f"LLM classifier failed: {e}. Using heuristic result.")
    
    return heuristic_meta

# ---------- MODEL SELECTION ----------
def select_model_from_policy(routing_meta: RoutingMeta, budget_override: str = None) -> str:
    """
    Select the optimal model based on routing policy and availability.
    
    Uses the routing_policy config to map (task, complexity) -> model list,
    then picks the first available model from the list.
    """
    task = routing_meta.task
    complexity = routing_meta.complexity
    
    # Get policy for this task
    task_policy = ROUTING_POLICY.get(task, ROUTING_POLICY.get("simple_qa", {}))
    
    # Get model list for this complexity
    model_list = task_policy.get(complexity, task_policy.get("low", ["llama-3.1-8b-instruct"]))
    
    # Filter by availability
    available_models = []
    for model_id in model_list:
        if model_id not in REG:
            continue
        
        meta = REG[model_id]
        provider = meta.get("provider", "ollama")
        
        # Check if cloud is available
        if provider == "openai" and not _fallback_enabled():
            continue
        
        available_models.append(model_id)
    
    # Fallback chain
    if not available_models:
        # Try local models first
        if "deepseek-coder-v2-16b" in REG:
            return "deepseek-coder-v2-16b"
        return "llama-3.1-8b-instruct"
    
    return available_models[0]

# Legacy function for backwards compatibility
def pick_model_id(state: RouterState) -> str:
    """
    Legacy model selection function. Now delegates to the new policy-based system.
    Kept for API compatibility.
    """
    msgs = state["messages"]
    
    # Check for legacy overrides
    if state.get("critical", False) and _fallback_enabled():
        return "o3" if state.get("budget") == "high" else "gpt-5.1-codex"
    
    # Use new automatic classification
    routing_meta = classify_prompt(msgs)
    
    # Refine with LLM if needed
    routing_meta = classify_prompt_with_llm(msgs, routing_meta)
    
    return select_model_from_policy(routing_meta, state.get("budget"))

# ---------- Chains ----------
def _build_chain(model_id: str):
    """Build a LangChain runnable for the specified model."""
    if model_id not in REG:
        logger.warning(f"Model {model_id} not in registry. Falling back to llama.")
        model_id = "llama-3.1-8b-instruct"
    
    meta = REG[model_id]
    if meta["provider"] == "ollama":
        return make_ollama(meta["name"], temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")))
    else:
        return make_openai(meta["name"], temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")))

# Pre-build chains for common models
CHAINS = {}
for model_id in REG:
    try:
        CHAINS[model_id] = _build_chain(model_id)
    except Exception as e:
        logger.warning(f"Failed to build chain for {model_id}: {e}")

def _get_chain(model_id: str):
    """Get or build a chain for the model."""
    if model_id in CHAINS:
        return CHAINS[model_id]
    return _build_chain(model_id)

# Build fallback chains
def _build_fallback_chain(primary: str, fallbacks: List[str]):
    """Build a chain with automatic fallbacks."""
    primary_chain = _get_chain(primary)
    fallback_chains = [_get_chain(fb) for fb in fallbacks if fb in REG]
    if fallback_chains:
        return primary_chain.with_fallbacks(fallback_chains)
    return primary_chain

# Dynamic branch based on model_id
def _model_branch(x: Dict[str, Any]) -> Any:
    """Route to the appropriate chain based on model_id."""
    model_id = x.get("model_id", "llama-3.1-8b-instruct")
    chain = _get_chain(model_id)
    
    # Add fallbacks for local models
    if model_id == "llama-3.1-8b-instruct" and _fallback_enabled():
        chain = chain.with_fallbacks([_get_chain("gpt-5-mini")])
    elif model_id == "deepseek-coder-v2-16b" and _fallback_enabled():
        chain = chain.with_fallbacks([_get_chain("gpt-5.1-codex")])
    
    return chain.invoke({"messages": x["messages"]})

BRANCH = RunnableLambda(_model_branch)

# ---------- SLA Monitoring ----------
def _sla_wrap(runnable):
    """Wrap a runnable with SLA monitoring and fallback."""
    if not SLA.get("enabled", True):
        return runnable
    
    # Prefer Env var (ms -> sec)
    if os.getenv("LOCAL_MAX_LATENCY_MS"):
        threshold = float(os.getenv("LOCAL_MAX_LATENCY_MS")) / 1000.0
    else:
        threshold = float(SLA.get("latency_sec", 6))
    
    def _call(x: Dict[str, Any]):
        start = time.perf_counter()
        model_id = x.get("model_id", "llama-3.1-8b-instruct")
        
        try:
            out = runnable.invoke(x)
            took = time.perf_counter() - start
            
            if took > threshold and _fallback_enabled():
                logger.warning(f"SLA exceeded ({took:.2f}s > {threshold}s) for {model_id}")
                # Could trigger cloud fallback here
            
            return out
            
        except Exception as e:
            logger.error(f"Primary chain {model_id} failed: {e}")
            
            # Attempt cloud fallback
            if _fallback_enabled():
                fallback_models = ["gpt-5-mini", "gpt-5.1-codex"]
                for fb_model in fallback_models:
                    try:
                        fb_chain = _get_chain(fb_model)
                        return fb_chain.invoke({"messages": x["messages"]})
                    except Exception as fb_err:
                        logger.error(f"Fallback {fb_model} failed: {fb_err}")
                        continue
            raise
    
    return RunnableLambda(_call)

# ---------- Graph Nodes ----------
def _node_classify(state: RouterState) -> RouterState:
    """Classify the prompt and determine routing metadata."""
    msgs = state["messages"]
    
    # Automatic classification
    routing_meta = classify_prompt(msgs)
    
    # Refine with LLM if enabled and uncertain
    routing_meta = classify_prompt_with_llm(msgs, routing_meta)
    
    # Apply legacy overrides if present
    if state.get("critical", False):
        routing_meta.complexity = "critical"
    
    if state.get("prefer_code", False) and routing_meta.task in ["simple_qa", "chitchat"]:
        routing_meta.task = "code_gen"
    
    return {"routing_meta": asdict(routing_meta)}

def _node_route(state: RouterState) -> RouterState:
    """Select the model based on routing metadata."""
    routing_meta_dict = state.get("routing_meta", {})
    routing_meta = RoutingMeta(**routing_meta_dict) if routing_meta_dict else classify_prompt(state["messages"])
    
    model_id = select_model_from_policy(routing_meta, state.get("budget"))
    
    return {"model_id": model_id, "attempts": [{"model": model_id, "status": "pending"}]}

def _node_invoke(state: RouterState) -> RouterState:
    """Invoke the selected model and return the response."""
    wrapped = _sla_wrap(BRANCH)
    model_id = state.get("model_id", "llama-3.1-8b-instruct")
    
    try:
        out = wrapped.invoke({"messages": state["messages"], "model_id": model_id})
        attempt_status = "success"
    except Exception as e:
        logger.error(f"Invocation failed: {e}")
        out = f"Error: {e}"
        attempt_status = "failed"
    
    # Build usage/telemetry
    prompt = join_messages(state["messages"])
    latency_start = state.get("_latency_start", time.perf_counter())
    
    routing_meta = state.get("routing_meta", {})
    
    # Update attempts
    attempts = state.get("attempts", [])
    if attempts:
        attempts[-1]["status"] = attempt_status
    
    usage = {
        "prompt_tokens_est": est_tokens(prompt),
        "completion_tokens_est": est_tokens(str(out)),
        "total_tokens_est": est_tokens(prompt) + est_tokens(str(out)),
        "resolved_model_id": model_id,
        "config_path": CONFIG_PATH,
        "latency_ms_router": int((time.perf_counter() - latency_start) * 1000),
        "routing_meta": routing_meta,
        "attempts": attempts,
        "classifier_used": routing_meta.get("classifier_used", "heuristic"),
        "cloud_available": _is_cloud_available(),
    }
    
    # ---------- METRICS & LOGGING ----------
    try:
        tier = _get_tier_from_model(model_id)
        price_per_1m = PRICING_PER_1M.get(tier, 5.0)
        total_tokens = usage["total_tokens_est"]
        cost_usd = (total_tokens / 1_000_000) * price_per_1m
        
        metric_event = {
            "ts": datetime.datetime.now().isoformat(),
            "prompt_id": str(uuid.uuid4()),
            "task": routing_meta.get("task", "unknown"),
            "complexity": routing_meta.get("complexity", "unknown"),
            "model_id": model_id,
            "tier": tier,
            "tokens_total": total_tokens,
            "latency_ms": usage["latency_ms_router"],
            "cost_est_usd": round(cost_usd, 6),
            "status": attempt_status
        }
        
        # Log to file
        with open("logs/metrics.jsonl", "a") as f:
            f.write(json.dumps(metric_event) + "\n")
            
        # Log to stderr (for journalctl)
        logger.info(f"METRIC: {json.dumps(metric_event)}")
        
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")
    
    return {"output": out, "usage": usage}

# ---------- Graph Builder ----------
def build_compiled_router():
    """
    Build the compiled LangGraph router.
    
    Graph flow:
    1. classify -> Automatic task/complexity detection
    2. route -> Policy-based model selection
    3. invoke -> Model invocation with SLA monitoring
    """
    g = StateGraph(RouterState)
    
    g.add_node("classify", _node_classify)
    g.add_node("route", _node_route)
    g.add_node("invoke", _node_invoke)
    
    # Linear flow: classify -> route -> invoke -> END
    g.set_entry_point("classify")
    g.add_edge("classify", "route")
    g.add_edge("route", "invoke")
    g.add_edge("invoke", END)
    
    return g.compile()

# ---------- Debug Endpoint Helper ----------
def debug_router_decision(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Debug helper: show what routing decision would be made for a prompt.
    Used by GET /debug/router_decision endpoint.
    """
    routing_meta = classify_prompt(messages)
    routing_meta = classify_prompt_with_llm(messages, routing_meta)
    
    model_id = select_model_from_policy(routing_meta)
    
    return {
        "routing_meta": asdict(routing_meta),
        "selected_model_id": model_id,
        "fallback_available": _fallback_enabled(),
        "available_models": list(REG.keys()),
    }
