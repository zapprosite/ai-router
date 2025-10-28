#!/usr/bin/env python3
import os, json, sys
from typing import List
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from providers.ollama_client import make_ollama
from providers.openai_client import make_openai

def try_invoke(name:str, chain, prompt:str)->dict:
    try:
        out = chain.invoke({"messages":[{"role":"user","content":prompt}]})
        return {"model": name, "ok": True, "preview": str(out)[:200]}
    except Exception as e:
        return {"model": name, "ok": False, "error": str(e)}

tests: List[dict] = []

# Locais (Ollama)
tests.append(try_invoke("llama3.1:8b-instruct-q5_K_M", make_ollama("llama3.1:8b-instruct-q5_K_M", 0.15), "Explique HVAC em 1 frase."))
tests.append(try_invoke("deepseek-coder-v2:16b", make_ollama("deepseek-coder-v2:16b", 0.1), "Escreva uma função Python soma(n1,n2) com docstring."))

# OpenAI (Tier-2): nano/mini/codex/high
for m in ["gpt-5-nano", "gpt-5-mini", "gpt-5-codex", "gpt-5"]:
    chain = make_openai(m, 0.0)
    prompt = "Explique HVAC em 1 frase." if m != "gpt-5-codex" else "Escreva uma função Python soma(n1,n2) com docstring."
    tests.append(try_invoke(m, chain, prompt))

print(json.dumps(tests, indent=2, ensure_ascii=False))
