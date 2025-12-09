#!/usr/bin/env python3
"""
Run a set of developer-day scenarios against the local router.

Usage:
  . .venv/bin/activate
  python3 scripts/dev_day_scenarios.py

This is a read-only client script: it only calls the router's OpenAI-compatible
shim at /v1/chat/completions (model: router-auto) and prints the resolved model.
"""
import os
import sys
import time
from typing import List, Dict, Any

import requests

BASE = os.getenv("AI_ROUTER_BASE", "http://localhost:8082").rstrip("/")
ENDPOINT = f"{BASE}/v1/chat/completions"
TIMEOUT = float(os.getenv("AI_ROUTER_TIMEOUT", "15"))


SCENARIOS: List[Dict[str, Any]] = [
    {"id": "C1", "short": "função simples", "prompt": "Escreva uma função Python chamada add(a, b) que retorna a soma com docstring e um exemplo de uso.", "expect": "DeepSeek (local)"},
    {"id": "C2", "short": "refatorar ifs", "prompt": "Refatore a função abaixo para reduzir ifs aninhados e melhorar legibilidade:\n```py\ndef process(x):\n    if x is not None:\n        if x > 0:\n            return 'pos'\n        else:\n            return 'non-pos'\n    return None\n```", "expect": "DeepSeek (local)"},
    {"id": "C3", "short": "scaffold FastAPI", "prompt": "Gere scaffold de uma API FastAPI com rotas CRUD para modelo User (id,email,name), validação Pydantic e exemplos de testes pytest.", "expect": "DeepSeek (local)"},
    {"id": "C4", "short": "stack trace simples", "prompt": "Analise este traceback e sugira correção:\nTraceback (most recent call last):\n  File \"app.py\", line 10, in <module>\n    print(data['key'])\nKeyError: 'key'\n", "expect": "DeepSeek (local)"},
    {"id": "C5", "short": "deadlock billing", "prompt": "Temos deadlock no serviço de billing envolvendo transações PostgreSQL e locks explícitos; trace e proponha correção e mitigação para produção.", "expect": "Codex / o3 (cloud)"},
    {"id": "C6", "short": "arquitetura HVAC", "prompt": "Desenhe arquitetura de um serviço de controle HVAC multi-tenant para 1000+ clientes com tolerância a falhas e particionamento de carga.", "expect": "o3 (cloud)"},
    {"id": "C7", "short": "middleware auth", "prompt": "Revise este middleware de autenticação assíncrona e aponte possíveis race conditions ou problemas de segurança.\n(Imagine código com cache local e refresh de token simultâneo.)", "expect": "o3 (cloud)"},
    {"id": "C8", "short": "testes integração", "prompt": "Escreva testes de integração assíncronos para rota POST /items que usa dependências externas (banco e fila). Use pytest-asyncio e fixtures.", "expect": "DeepSeek (local)"},
]


def pretty_row(cols: List[str], widths: List[int]) -> str:
    out = []
    for i, c in enumerate(cols):
        s = str(c or "")
        w = widths[i]
        if len(s) > w:
            s = s[: w - 3] + "..."
        out.append(s.ljust(w))
    return " | ".join(out)


def call_router(prompt: str) -> Dict[str, Any]:
    body = {
        "model": "router-auto",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        r = requests.post(ENDPOINT, json=body, timeout=TIMEOUT)
    except Exception as e:
        return {"error": str(e)}
    try:
        return r.json()
    except Exception as e:
        return {"error": f"invalid-json: {e}", "text": r.text[:200]}


def run():
    widths = [4, 26, 28, 28, 24]
    print(pretty_row(["id", "descrição curta", "modelo_escolhido", "esperado", "comentário"], widths))
    print("-" * 120)

    for s in SCENARIOS:
        cid = s["id"]
        prompt = s["prompt"]
        expect = s["expect"]
        # call
        resp = call_router(prompt)
        if resp.get("error"):
            selected = f"ERROR: {resp.get('error')}\n"
            comment = "erro na chamada"
        else:
            # router shim returns 'model' and usage.resolved_model_id
            usage = resp.get("usage") or {}
            selected = usage.get("resolved_model_id") or resp.get("model") or "-"
            # comment heuristics
            if isinstance(selected, str) and any(m in selected for m in ["o3", "codex", "gpt-5.1"]):
                comment = "Cloud (escalado)"
            else:
                comment = "Local (suficiente)"

        print(pretty_row([cid, s["short"], selected, expect, comment], widths))
        time.sleep(0.2)


if __name__ == "__main__":
    run()
