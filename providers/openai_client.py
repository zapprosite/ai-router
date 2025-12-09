import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda


def _needs_reasoning(name: str) -> bool:
    n = (name or "").lower()
    # Reasoning models (o1, o3, o4 families) don't support temperature param
    return n.startswith("o1") or n.startswith("o3") or n.startswith("o4")


def _is_responses_only(name: str) -> bool:
    # Disabled: Responses API requires special access. Use standard chat completions.
    # n = (name or "").lower()
    # return n in ("gpt-5-codex", "gpt-5.1-codex", "gpt-5.1-codex-mini")
    return False


def make_openai(model: str, temperature: float = 0.0):
    key = os.getenv("OPENAI_API_KEY_TIER2") or os.getenv("OPENAI_API_KEY")
    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    org = os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG")
    proj = os.getenv("OPENAI_PROJECT")
    timeout = int(os.getenv("OPENAI_TIMEOUT_SEC", "20"))

    # Stability Layer: Map future GPT-5.1 models to stable GPT-4.1 equivalents
    # This ensures "2025" models work reliably with current infrastructure
    if model == "gpt-5.1-high":
        model = "gpt-4.1" # Best available high-end writing model
    elif model == "gpt-5.1-codex-mini":
        model = "gpt-4.1-mini" # Fast code model mapping
    elif model == "gpt-5.1-codex-high":
        model = "gpt-4.1" # High-end code model mapping

    if not key:
        # generate a Runnable that fails to trigger fallbacks without breaking imports
        def _raise(_):
            raise RuntimeError("OpenAI disabled: missing OPENAI_API_KEY")
        return RunnableLambda(_raise)

    # Models that require the Responses API (e.g., gpt-5-codex, gpt-5.1-codex)
    if _is_responses_only(model):
        import uuid
        import httpx
        import logging
        import time
        
        logger = logging.getLogger("ai-router.openai")
        
        def _call_responses_api(payload):
            msgs = payload["messages"]
            text = "\n".join(m.get("content", "") for m in msgs if m.get("role") in ("system", "user"))
            
            # Build headers explicitly with Bearer token
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "X-Client-Request-Id": str(uuid.uuid4()),
            }
            if org:
                headers["OpenAI-Organization"] = org
            if proj:
                headers["OpenAI-Project"] = proj
            
            url = f"{base.rstrip('/')}/responses"
            body = {"model": model, "input": text}
            
            # Retry with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(url, json=body, headers=headers)
                        
                        # Log request ID for debugging
                        req_id = resp.headers.get("x-request-id", "N/A")
                        logger.debug(f"OpenAI request-id: {req_id}")
                        
                        resp.raise_for_status()
                        data = resp.json()
                        
                        # Extract output text
                        for out in data.get("output", []):
                            if out.get("type") == "message":
                                for part in out.get("content", []):
                                    if part.get("type") == "output_text":
                                        return part.get("text", "")
                        return str(data)
                        
                except httpx.HTTPStatusError as e:
                    logger.warning(f"Responses API error (attempt {attempt+1}): {e.response.status_code} - {e.response.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
                except httpx.RequestError as e:
                    logger.error(f"Connection error (attempt {attempt+1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        raise
            
            return ""
        
        return RunnableLambda(_call_responses_api)


    headers = {}
    if proj:
        headers["OpenAI-Project"] = proj

    kwargs = dict(
        model=model,
        api_key=key,
        organization=org,
        base_url=base,
        timeout=timeout,
        default_headers=headers or None,
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )

    # Only include reasoning_effort for gpt-5 ("high") and only if env is valid
    if _needs_reasoning(model):
        eff = (os.getenv("OPENAI_REASONING_EFFORT", "") or "").strip().lower()
        if eff in ("low", "medium", "high"):
            kwargs["reasoning_effort"] = eff
    else:
        # standard chat models: use temperature
        kwargs["temperature"] = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))

    llm = ChatOpenAI(**kwargs)
    
    # Cost Guard Integration
    from graph.cost_guard import check_cost_limit
    def _guard(x):
        if not check_cost_limit(model, x["messages"]):
            raise ValueError(f"Cost Guard: Request blocked for model {model} due to budget limits.")
        return x
    
    guard = RunnableLambda(_guard)

    to_msgs = RunnableLambda(lambda x: x["messages"])
    to_text = RunnableLambda(lambda m: getattr(m, "content", str(m)))
    return guard | to_msgs | llm | to_text
