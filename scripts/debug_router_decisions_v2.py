#!/usr/bin/env python3
"""
Query /debug/router_decision for a curated test matrix and print results.

Run with:
  .venv/bin/python3 scripts/debug_router_decisions_v2.py

Reads base URL from AI_ROUTER_BASE (default http://localhost:8082).
"""
import os
import sys
import json
from typing import List, Dict, Any

import requests

BASE = os.getenv("AI_ROUTER_BASE", "http://localhost:8082").rstrip("/")
URL = f"{BASE}/debug/router_decision"


TEST_MATRIX = [
    {
        "id": "S1-CHAT",
        "prompt": "Hi, can you say hello and ask how I'm doing?",
        "expected_task": "chitchat",
        "expected_complexity": "low",
        "expected_tier": "Tier 1 local",
    },
    {
        "id": "S2-FACT",
        "prompt": "What is the freezing point of water in Celsius?",
        "expected_task": "simple_qa",
        "expected_complexity": "low",
        "expected_tier": "Tier 1 local",
    },
    {
        "id": "S3-CODE",
        "prompt": "Write a Python function def add(a, b): that returns the sum and include a docstring.",
        "expected_task": "code_gen",
        "expected_complexity": "medium",
        "expected_tier": "Tier 2 DeepSeek (local)",
    },
    {
        "id": "S4-CRIT-DBG",
        "prompt": "Traceback (most recent call last):\n  File \"server.py\", line 128, in handle\n    lock.acquire()\nRuntimeError: deadlock in production DB",
        "expected_task": "code_crit_debug",
        "expected_complexity": "critical",
        "expected_tier": "Tier 3/4 OpenAI (cloud)",
    },
    {
        "id": "S5-SYS-DESIGN",
        "prompt": "Design a distributed HVAC control system for a 1000-room hotel with zonal control and high availability.",
        "expected_task": "system_design",
        "expected_complexity": "high",
        "expected_tier": "Tier 3/4 OpenAI (cloud)",
    },
    {
        "id": "S6-REASON",
        "prompt": "Compare trade-offs between optimistic and pessimistic concurrency for a shared thermostat state across many devices.",
        "expected_task": "research",
        "expected_complexity": "high",
        "expected_tier": "Tier 3 OpenAI (cloud)",
    },
    {
        "id": "S7-HVAC-INC",
        "prompt": "Intermittent thermostat resets every 4 hours; gateway logs show 'connection reset by peer'. What are likely root causes and next troubleshooting steps?",
        "expected_task": "code_review|data_analysis|system_design",
        "expected_complexity": "medium",
        "expected_tier": "Tier 2 DeepSeek (local) or Tier 3 if cloud escalates",
    },
]


def pretty_row(cols: List[str], widths: List[int]) -> str:
    out = []
    for i, c in enumerate(cols):
        w = widths[i]
        s = c if c is not None else ""
        if len(s) > w:
            s = s[: w - 3] + "..."
        out.append(s.ljust(w))
    return " | ".join(out)


def call_debug(prompt: str) -> Dict[str, Any]:
    try:
        r = requests.post(URL, json={"prompt": prompt}, timeout=10)
    except Exception as e:
        return {"error": str(e)}
    try:
        return r.json()
    except Exception as e:
        return {"error": f"invalid-json: {e}", "text": r.text[:200]}


def run():
    widths = [8, 18, 12, 28, 6]
    header = pretty_row(["id", "task", "complexity", "selected_model_id", "cloud"], widths)
    sep = "-" * len(header)
    print(f"Querying {URL}")
    print(header)
    print(sep)

    for case in TEST_MATRIX:
        cid = case["id"]
        prompt = case["prompt"]
        resp = call_debug(prompt)
        if resp.get("error"):
            print(pretty_row([cid, "ERROR", "-", resp.get("error"), "-"], widths))
            continue

        routing_meta = resp.get("routing_meta") or {}
        task = routing_meta.get("task") or routing_meta.get("TASK") or "-"
        complexity = routing_meta.get("complexity") or routing_meta.get("COMPLEXITY") or "-"
        selected = resp.get("selected_model_id") or resp.get("selected_model") or "-"
        cloud = resp.get("fallback_available") if resp.get("fallback_available") is not None else resp.get("cloud_available")
        cloud_flag = "Y" if cloud else "N"

        print(pretty_row([cid, str(task), str(complexity), str(selected), cloud_flag], widths))


if __name__ == "__main__":
    run()
