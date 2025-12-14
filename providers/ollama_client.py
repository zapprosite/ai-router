import os

from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama


def validate_model_id(model_name: str) -> bool:
    """
    Validate that a model exists in local Ollama.
    """
    try:
        # Fast CLI check
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Output format: NAME     ID      SIZE   MODIFIED
            # Check if model_name is a substring of any line (simple check)
            # Better: parse lines
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if not parts:
                    continue
                name = parts[0]
                if name == model_name or name.startswith(model_name + ":"):
                     return True
        return False
    except Exception:
        return False

def make_ollama(model: str, temperature: float = 0.1):
    base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_URL") or "http://localhost:11434"
    
    # Determine configuration tier (Coder vs Instruct)
    is_coder = model == os.getenv("OLLAMA_CODER_MODEL")
    prefix = "OLLAMA_CODER" if is_coder else "OLLAMA_INSTRUCT"
    
    # Load Tier-specific parameters
    num_ctx = int(os.getenv(f"{prefix}_NUM_CTX", os.getenv("OLLAMA_NUM_CTX", "4096")))
    num_predict = int(os.getenv(f"{prefix}_NUM_PREDICT", os.getenv("OLLAMA_NUM_PREDICT", "-1")))
    
    env_temp = os.getenv(f"{prefix}_TEMPERATURE")
    if env_temp:
        temperature = float(env_temp)
        
    top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
    seed = int(os.getenv("OLLAMA_SEED", "42"))
    keep_alive = os.getenv(f"{prefix}_KEEP_ALIVE") or os.getenv("OLLAMA_KEEP_ALIVE", None)

    llm = ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        num_ctx=num_ctx,
        num_predict=num_predict,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
        seed=seed,
        keep_alive=keep_alive
    )

    to_msgs = RunnableLambda(lambda x: x["messages"])
    to_text = RunnableLambda(lambda m: getattr(m, "content", str(m)))
    return to_msgs | llm | to_text
