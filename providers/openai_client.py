import logging
import os
import time

from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

logger = logging.getLogger("ai-router.openai")


def _needs_reasoning(name: str) -> bool:
    """Check if model is a reasoning model (o1, o3, o4 families)."""
    n = (name or "").lower()
    # Reasoning models (o1, o3, o4 families) don't support temperature param
    return n.startswith("o1") or n.startswith("o3") or n.startswith("o4")


# Global cache for auth validation to avoid repeated 401 spam
# Key meanings:
# - validated: True if we've attempted auth check at least once
# - available: True if auth succeeded (200), False if auth failed (401)
# - checked_at: timestamp of last check (for cache TTL)
_OPENAI_AUTH_STATUS = {"validated": False, "available": False, "checked_at": 0}


def is_cloud_enabled() -> bool:
    """
    Check if cloud (OpenAI) calls are enabled based on cached auth status.
    
    Returns:
        True if cloud is available (auth not yet checked or auth succeeded)
        False if auth has failed globally (cached 401)
    
    Use this before making any OpenAI call to short-circuit when cloud is disabled.
    """
    # If we haven't validated yet, assume cloud is available (will validate on first call)
    if not _OPENAI_AUTH_STATUS["validated"]:
        return True
    
    # Check cache TTL (5 minutes)
    now = time.time()
    if (now - _OPENAI_AUTH_STATUS["checked_at"]) >= 300:
        # Cache expired, assume available (will re-validate on next call)
        _OPENAI_AUTH_STATUS["validated"] = False
        return True
    
    return _OPENAI_AUTH_STATUS["available"]

def validate_model_id(model_name: str) -> bool:
    """
    Validate that a model ID exists in the OpenAI account.
    Returns True if valid, False otherwise.
    
    IMPORTANT: If auth fails globally (401), this function will:
    - Log a clear error message once
    - Cache the failure to avoid repeated validation attempts
    - Return False for all subsequent calls until restart
    
    NOTE: Skips validation if no API key is present (returns True to avoid blocking local-only usage).
    """
    
    key = os.getenv("OPENAI_API_KEY_TIER2") or os.getenv("OPENAI_API_KEY")
    if not key:
        logger.debug("OpenAI validation skipped: no API key configured (local-only mode)")
        return True # Cannot validate without key, assume OK (router will fail late if used)

    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    org = os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG")
    proj = os.getenv("OPENAI_PROJECT")
    
    # Check global auth status cache (avoid repeated 401 spam)
    now = time.time()
    if _OPENAI_AUTH_STATUS["validated"] and (now - _OPENAI_AUTH_STATUS["checked_at"]) < 300:
        # Use cached result for 5 minutes
        if not _OPENAI_AUTH_STATUS["available"]:
            logger.debug(f"OpenAI validation skipped for {model_name}: auth globally disabled (cached 401)")
            return False
    
    import httpx
    try:
        headers = {"Authorization": f"Bearer {key[:12]}..."}  # Truncated for logging
        if org:
            headers["OpenAI-Organization"] = org
        if proj:
            headers["OpenAI-Project"] = proj
        
        # Build actual request headers (with full key)
        request_headers = {"Authorization": f"Bearer {key}"}
        if org:
            request_headers["OpenAI-Organization"] = org
        if proj:
            request_headers["OpenAI-Project"] = proj
        
        models_url = f"{base.rstrip('/')}/models"
        
        # First call: check if we can authenticate at all
        if not _OPENAI_AUTH_STATUS["validated"]:
            logger.info(f"OpenAI auth check: GET {models_url} (org={org or 'none'}, project={proj or 'none'})")
        
        # Short timeout for startup check
        resp = httpx.get(models_url, headers=request_headers, timeout=5.0)
        
        if resp.status_code == 401:
            # GLOBAL AUTH FAILURE - disable cloud entirely
            _OPENAI_AUTH_STATUS["validated"] = True
            _OPENAI_AUTH_STATUS["available"] = False
            _OPENAI_AUTH_STATUS["checked_at"] = now
            
            logger.error(
                f"OpenAI auth FAILED (401 Unauthorized): Invalid API key or insufficient permissions. "
                f"Cloud models disabled. Fallback forced to local-only. "
                f"Base URL: {base}, Org: {org or 'none'}, Project: {proj or 'none'}"
            )
            return False
        
        if resp.status_code == 200:
            data = resp.json()
            available = {m["id"] for m in data.get("data", [])}
            
            # Cache successful auth
            if not _OPENAI_AUTH_STATUS["validated"]:
                logger.info(f"OpenAI auth SUCCESS: {len(available)} models available")
                _OPENAI_AUTH_STATUS["validated"] = True
                _OPENAI_AUTH_STATUS["available"] = True
                _OPENAI_AUTH_STATUS["checked_at"] = now
            
            # Check if specific model exists
            is_valid = model_name in available
            if not is_valid:
                logger.warning(
                    f"Model '{model_name}' not found in OpenAI account. "
                    f"Available models: {sorted(list(available)[:10])}..."
                )
            return is_valid
        
        # Other status codes (429, 500, etc.)
        logger.warning(f"OpenAI validation failed for {model_name}: HTTP {resp.status_code}")
        return False
        
    except httpx.TimeoutException:
        logger.warning(f"OpenAI validation timeout for {model_name} (network issue)")
        return False
    except Exception as e:
        logger.warning(f"OpenAI validation error for {model_name}: {type(e).__name__}: {e}")
        return False


def make_openai(model: str, temperature: float = 0.0, params: dict = None):
    key = os.getenv("OPENAI_API_KEY_TIER2") or os.getenv("OPENAI_API_KEY")
    base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
    org = os.getenv("OPENAI_ORGANIZATION") or os.getenv("OPENAI_ORG")
    proj = os.getenv("OPENAI_PROJECT")
    timeout = int(os.getenv("OPENAI_TIMEOUT_SEC", "20"))
    
    params = params or {}

    # NOTE: Model mapping is now handled in router_config.yaml via the 'name' field.
    # The 'model' argument here should already be the real provider ID (e.g., gpt-4o).
    # Do NOT add hardcoded mappings here.

    if not key:
        # generate a Runnable that fails to trigger fallbacks without breaking imports
        def _raise(_):
            raise RuntimeError("OpenAI disabled: missing OPENAI_API_KEY")
        return RunnableLambda(_raise)

    # Models that require the Responses API (e.g., gpt-5-codex, gpt-5.2-codex)
    # NOTE: Legacy check removed. Now we assume standard chat completions unless special tier logic re-added.
    if False:
        import logging
        import time
        import uuid

        import httpx
        
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
                    logger.warning(
                        f"Responses API error (attempt {attempt+1}): "
                        f"{e.response.status_code} - {e.response.text[:200]}"
                    )
                    
                    # Don't retry fatal 4xx errors (except 429)
                    if e.response.status_code in (400, 401, 402, 403, 404):
                         # Raises specific structured error that Router can catch
                         raise ValueError(f"Upstream Error {e.response.status_code}: {e.response.text}")

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
    
    # Inject params (e.g. reasoning_effort, seed, top_p)
    # Move specific known params to top-level if ChatOpenAI supports them (like temperature), 
    # others to model_kwargs.
    model_kwargs = {}
    
    for k, v in params.items():
        if k == "temperature":
             kwargs["temperature"] = v
        else:
             model_kwargs[k] = v

    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs

    # Fallback to env var for temperature if not in params
    if "temperature" not in kwargs and not _needs_reasoning(model):
         kwargs["temperature"] = temperature

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
