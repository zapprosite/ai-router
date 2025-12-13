import logging
import math
import os

logger = logging.getLogger("ai-router.cost")

# Approximate pricing (Input/Output blended or worst case for estimation)
# Prices are per 1M tokens (approximate as of Late 2024/2025)
PRICING_PER_1M = {
    "mini": 0.50,       # gpt-4o-mini / gpt-5-mini
    "standard": 5.00,   # gpt-4o / gpt-5-codex
    "reasoning": 10.00, # o3-mini-high (reasoning tokens add up)
    "elite": 30.00,     # o3 / gpt-5
    "local": 0.00       # Llama / DeepSeek (Free)
}

def _get_tier_from_model(model_name: str) -> str:
    """Reverse lookup tier from model name using Env vars."""
    if model_name == os.getenv("OPENAI_CODE_ELITE"): 
        return "elite"
    if model_name == os.getenv("OPENAI_CODE_REASONING"):
        return "reasoning"
    if model_name == os.getenv("OPENAI_CODE_STANDARD"):
        return "standard"
    if model_name == os.getenv("OPENAI_CODE_MINI"):
        return "mini"
    
    if model_name == os.getenv("OPENAI_TEXT_STANDARD"):
        return "standard"
    if model_name == os.getenv("OPENAI_TEXT_NANO"):
        return "mini"
    
    if "llama" in model_name.lower():
        return "local"
    if "deepseek" in model_name.lower():
        return "local"
    
    return "standard" # Default fallback

def est_tokens(text: str) -> int:
    """Rough estimation of tokens (char/4)."""
    return math.ceil(len(text) / 4)

def check_cost_limit(model_name: str, messages: list) -> bool:
    """
    Check if the request exceeds the cost limit for its tier.
    Returns True if allowed, False if blocked.
    """
    if str(os.getenv("ENABLE_COST_PROTECTION", "0")) != "1":
        return True

    tier = _get_tier_from_model(model_name)
    
    # Calculate prompt tokens
    full_text = "".join([str(m.get("content", "")) for m in messages])
    prompt_tokens = est_tokens(full_text)
    
    # Estimate completion tokens (heuristic based on tier)
    # Reasoning models generate LOTS of tokens.
    completion_multiplier = 2.0 if tier in ["reasoning", "elite"] else 0.5
    est_total_tokens = prompt_tokens + (prompt_tokens * completion_multiplier)
    
    # Calculate Cost
    price = PRICING_PER_1M.get(tier, 5.00)
    est_cost = (est_total_tokens / 1_000_000) * price
    
    # Get Limit
    env_var = f"MAX_COST_PER_QUERY_{tier.upper()}_USD"
    limit = float(os.getenv(env_var, "10.0"))
    
    if est_cost > limit:
        logger.warning(
            f"⛔ Cost Guard BLOCKED: {model_name} ({tier}). "
            f"Est. Tokens={est_total_tokens}, Cost=${est_cost:.4f} > Limit=${limit:.4f}"
        )
        return False
        
    return True
