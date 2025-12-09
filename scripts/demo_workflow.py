import requests
import json
import sys
import time

BASE_URL = "http://localhost:8082"

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def print_step(phase, description, prompt):
    print(f"\n{color('='*60, '36')}")
    print(f"{color(phase.upper(), '1;33')} : {description}")
    print(f"{color('-'*60, '36')}")
    print(f"Prompt: \"{prompt[:80]}...\"")
    
    start = time.time()
    try:
        # We use the debug endpoint to just see the decision without waiting for generation
        # (Simulating the routing logic)
        resp = requests.post(f"{BASE_URL}/debug/router_decision", json={"prompt": prompt})
        resp.raise_for_status()
        data = resp.json()
        
        meta = data['routing_meta']
        model = data['selected_model_id']
        is_cloud = "gpt" in model or "o3" in model
        
        print(f"Routing Decision:")
        print(f"  Task:       {meta['task']}")
        print(f"  Complexity: {meta['complexity']}")
        print(f"  Model:      {color(model, '32' if not is_cloud else '31')}")
        print(f"  Cloud Used? {is_cloud}")
        
    except Exception as e:
        print(f"Error: {e}")

def run_simulation():
    print(f"{color('WORKFLOW SIMULATION: POOR DEV (Local Draft -> Cloud Polish)', '1;37')}\n")
    
    # PHASE 1: DRAFTING (Structure)
    # Expectation: DeepSeek (Local)
    prompt_draft = (
        "Create a complete e-commerce backend structure using FastAPI. "
        "Include folders for routers, schemas, models, and services. "
        "Write the main.py and database connection logic."
    )
    print_step("Phase 1: Zero-Cost Drafting", "Generate entire project structure", prompt_draft)
    
    # PHASE 2: REFINING (Core Logic)
    # Expectation: Cloud (O3/Codex) due to critical keywords
    prompt_refine = (
        "Refactor this authentication middleware. "
        "It has a security vulnerability allowing token bypass. "
        "Fix the race condition in the session handling."
    )
    print_step("Phase 2: Critical Refinement", "Fix security/race condition in core", prompt_refine)

if __name__ == "__main__":
    run_simulation()
