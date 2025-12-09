import requests
import time
import sys

BASE_URL = "http://localhost:8082"

SCENARIOS = [
    # Local expected
    {"id": "C1", "prompt": "Hi"},
    {"id": "C4", "prompt": "Write a python sort"}, 
    # Cloud expected
    {"id": "C5", "prompt": "Refactor this huge java monolith to microservices... (security critical)"},
    {"id": "C6", "prompt": "Analyze this deadlock trace..."},
    {"id": "C7", "prompt": "Design a global payment system architecture."}
]

def run():
    print("Running Dev Day Scenarios (Simulation)...")
    for s in SCENARIOS:
        try:
            # Using debug endpoint to visualize routing decision + validation
            # Ideally we would call /v1/chat/completions but that costs money/hits cloud
            # We will assume the router's decision is what's important, check if cloud is theoretically available
            resp = requests.post(f"{BASE_URL}/debug/router_decision", json={"prompt": s["prompt"]})
            resp.raise_for_status()
            data = resp.json()
            
            model = data["selected_model_id"]
            if s["id"] in ["C5", "C6", "C7"]:
                 print(f"{s['id']} -> {model} (Cloud? {'gpt' in model or 'o3' in model})")
            else:
                 print(f"{s['id']} -> {model} (Local)")
                 
        except Exception as e:
             print(f"{s['id']} ERROR: {e}")

if __name__ == "__main__":
    run()
