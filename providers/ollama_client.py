import os
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda

def make_ollama(model: str, temperature: float = 0.0):
    base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_URL") or "http://localhost:11434"
    llm = ChatOllama(model=model, base_url=base_url, temperature=temperature)

    to_msgs = RunnableLambda(lambda x: x["messages"])
    to_text = RunnableLambda(lambda m: getattr(m, "content", str(m)))
    return to_msgs | llm | to_text
