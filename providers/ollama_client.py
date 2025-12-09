import os
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda

def make_ollama(model: str, temperature: float = 0.0):
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
