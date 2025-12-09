#!/usr/bin/env python3
"""
Lightweight helper to query the router debug endpoint for routing decisions.

Run as:
  python3 scripts/debug_router_decisions.py

This posts each prompt to POST /debug/router_decision and prints a compact table:
  prompt_id | predicted_task | predicted_complexity | selected_model | attempts

The script is read-only and safe to run against a local router.
"""
import os
import sys
import json
import textwrap
from typing import List, Dict, Any

import requests

BASE = os.getenv("AI_ROUTER_BASE", "http://localhost:8082")
URL = BASE.rstrip("/") + "/debug/router_decision"


PROMPTS = [
    # id, prompt
    ("P1-CHAT", "Hi there! Can you give me a quick hello and ask how I am doing?"),
    ("P2-FACT", "What is the boiling point of water at sea level in Celsius?"),
    ("P3-CODE", "Write a Python function def sum(a, b): that returns the sum with a docstring."),
    ("P4-DBG-CRIT", "Traceback (most recent call last):\n  File \"app.py\", line 42, in <module>\n    lock.acquire()\nRuntimeError: deadlock detected while acquiring lock"),
    ("P5-SYS-DESIGN", "Design a distributed HVAC control system for a 1000-room hotel with zone-level control and high availability."),
    ("P6-DATA", "Given a dataset of hourly temperature readings for a year, how would you detect anomalous HVAC behavior? Outline steps and key metrics."),
    ("P7-BORDERLINE", "Compare two strategies for scaling the HVAC analytics pipeline: batch nightly processing vs streaming with micro-batches. Pros and cons?"),
    ("P8-HVAC-SPEC", "We have intermittent thermostat resets in Building A every 4 hours; logs show 'connection reset by peer' on the gateway. What are the likely root causes and next steps?")
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


def summarize_attempts(resp: Dict[str, Any]) -> str:
    # The debug endpoint may not include attempts; fallback to empty
    attempts = resp.get("usage", {}).get("attempts") or resp.get("attempts") or []
    if not attempts:
        return "-"
    parts = []
    for a in attempts:
        m = a.get("model") or a.get("model_id") or str(a)
        st = a.get("status") or a.get("result") or "ok"
        parts.append(f"{m}:{st}")
    return ",".join(parts)


def run():
    widths = [8, 16, 12, 22, 20]
    header = pretty_row(["prompt_id", "task", "complexity", "selected_model", "attempts"], widths)
    sep = "-" * len(header)
    print(header)
    print(sep)

    for pid, prompt in PROMPTS:
        payload = {"prompt": prompt}
        try:
            r = requests.post(URL, json=payload, timeout=10)
        except Exception as e:
            print(pretty_row([pid, "ERR", "-", "-", str(e)], widths))
            continue

        try:
            data = r.json()
        except Exception:
            print(pretty_row([pid, "ERR_JSON", "-", str(r.status_code), r.text[:40]], widths))
            continue

        routing_meta = data.get("routing_meta") or {}
        # routing_meta may be a dict-like object or dataclass converted to dict
        task = routing_meta.get("task") or routing_meta.get("TASK") or "-"
        complexity = routing_meta.get("complexity") or routing_meta.get("COMPLEXITY") or "-"
        selected = data.get("selected_model_id") or data.get("selected_model") or "-"
        attempts = summarize_attempts(data)

        print(pretty_row([pid, task, complexity, selected, attempts], widths))


if __name__ == "__main__":
    print(f"Querying router debug endpoint: {URL}")
    run()
