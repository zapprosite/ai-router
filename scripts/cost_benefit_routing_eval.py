import json
import requests
import sys
from typing import Dict, Any, List

# Define the Prompt Battery
PROMPTS = [
    # --- LEVEL 1: LOCAL (Should stay on Llama/DeepSeek) ---
    {
        "id": "p1_hello",
        "category": "local_ok",
        "messages": [{"role": "user", "content": "Hello, how are you?"}]
    },
    {
        "id": "p2_sort",
        "category": "deepseek_ok",
        "messages": [{"role": "user", "content": "Write a python function to sort a list of dicts by key"}]
    },
    {
        "id": "p3_api",
        "category": "local_ok",
        "messages": [{"role": "user", "content": "Explain REST vs GraphQL briefly."}]
    },
    {
        "id": "p4_fix_simple",
        "category": "deepseek_ok",
        "messages": [{"role": "user", "content": "Fix this code: def foo(x): return x+1"}]
    },
    {
        "id": "p5_review_med",
        "category": "deepseek_ok",
        "messages": [{"role": "user", "content": "Review this function:\n" + ("def work(): pass\n" * 50) + "\nIs it optimized?"}]
    },

    # --- LEVEL 2: CODE GEN (DeepSeek preferred, escalate only if huge) ---
    {
        "id": "p6_regex",
        "category": "deepseek_ok", 
        "messages": [{"role": "user", "content": "Write a regex to match email addresses that must end in .edu or .gov"}]
    },
    {
        "id": "p7_refactor_med",
        "category": "deepseek_ok",
        "messages": [{"role": "user", "content": "Refactor this code to use list comprehensions:\n" + ("items.append(x)\n" * 20)}]
    },

    # --- LEVEL 3: CLOUD (Codex needed for context/quality) ---
    {
        "id": "p8_full_app",
        "category": "deepseek_ok", # Optimized: DeepSeek 16B is capable of scaffolding standard apps
        "messages": [{"role": "user", "content": "Create a complete FastAPI application structure with SQLAlchemy, Pydantic v2, JWT authentication, and Docker Compose."}]
    },
    {
        "id": "p9_stacktrace",
        "category": "deepseek_ok", # Optimized: DeepSeek 16B can handle standard stack traces
        "messages": [{"role": "user", "content": "Analyze this stack trace:\n" + ("File '/app/main.py', line 10, in <module>\n  foo()\n" * 100) + "RecursionError: maximum recursion depth exceeded"}]
    },

    # --- LEVEL 4: CRITICAL (O3 needed) ---
    {
        "id": "p10_deadlock",
        "category": "o3_needed",
        "messages": [{"role": "user", "content": "My production Postgres database is facing a deadlock situation. Here are the logs... help immediately!"}]
    },
    {
        "id": "p11_arch",
        "category": "o3_needed",
        "messages": [{"role": "user", "content": "Design a distributed system for a Netflix clone handling 10M concurrent users. Discuss sharding, CDN, and caching layers."}]
    }
]

BASE_URL = "http://localhost:8082"

def color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def run_eval():
    print(f"{'ID':<15} {'EXPECTED':<15} {'TASK':<15} {'COMPLEXITY':<12} {'MODEL':<25} {'CLOUD?':<8} {'MATCH?':<8}")
    print("-" * 110)

    score = 0
    total = 0

    for p in PROMPTS:
        pid = p["id"]
        cat = p["category"]
        
        try:
            # 1. Debug Decision
            # Extract content from messages (helper expects list, but API expects prompt str)
            prompt_text = p["messages"][0]["content"]
            resp = requests.post(f"{BASE_URL}/debug/router_decision", json={"prompt": prompt_text})
            resp.raise_for_status()
            data = resp.json()
            
            meta = data["routing_meta"]
            model = data["selected_model_id"]
            fallback = data["fallback_available"]
            
            # Determine if cloud
            is_cloud = "gpt" in model or "o3" in model or "o4" in model
            
            # Evaluate
            match = False
            if cat in ["local_ok", "deepseek_ok"] and not is_cloud:
                match = True
            elif cat in ["codex_needed", "o3_needed"] and is_cloud:
                match = True
            
            # Specific model checks
            if cat == "o3_needed" and "o3" not in model and "o4" not in model:
                match = False # Downgraded critical
            
            if match:
                score += 1
            
            match_str = "YES" if match else "NO"
            match_col = "32" if match else "31" # Green/Red
            
            print(f"{pid:<15} {cat:<15} {meta['task']:<15} {meta['complexity']:<12} {model:<25} {str(is_cloud):<8} {color(match_str, match_col)}")

        except Exception as e:
            print(f"{pid:<15} ERROR: {e}")
        
        total += 1

    print("-" * 110)
    print(f"Final Score: {score}/{total} ({(score/total)*100:.1f}%)")

if __name__ == "__main__":
    run_eval()
