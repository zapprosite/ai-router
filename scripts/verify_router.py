import requests
import sys
import json
import time

BASE_URL = "http://localhost:8082"

def test_route(name, messages, expected_model_partial, detailed_check=None):
    print(f"--- Scenario: {name} ---")
    url = f"{BASE_URL}/route"
    payload = {
        "messages": messages,
        "budget": "balanced",
        "prefer_code": False
    }
    
    # Adjust for code scenario
    if "Code" in name:
        payload["prefer_code"] = True
    
    try:
        start = time.time()
        res = requests.post(url, json=payload, timeout=30)
        dur = time.time() - start
        
        if res.status_code != 200:
            print(f"FAILED: Status {res.status_code}")
            return False
            
        data = res.json()
        model = data.get("usage", {}).get("resolved_model_id", "unknown")
        output = data.get("output", "")[:100].replace("\n", " ")
        
        print(f"Routed to: {model}")
        print(f"Latency: {dur:.2f}s")
        print(f"Output Preview: {output}...")
        
        if expected_model_partial in model:
            print("✅ ROUTING CORRECT")
            return True
        else:
            print(f"❌ ROUTING FAILED (Expected subset '{expected_model_partial}', got '{model}')")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def main():
    print(f"Targeting: {BASE_URL}")
    
    # Scenario A: Simple -> Llama
    s1 = test_route(
        "A (Simple)", 
        [{"role": "user", "content": "What is the capital of France?"}],
        "llama-3.1"
    )
    
    # Scenario B: Code -> DeepSeek
    s2 = test_route(
        "B (Medium Code)",
        [{"role": "user", "content": "Write a Python Fibonacci function."}],
        "deepseek"
    )
    
    # Scenario C: Complex -> OpenAI (Simulated by 'refactor' keyword and high complexity)
    # We force complexity via keyword match in our loose heuristic
    s3 = test_route(
        "C (Complex/Fallback)",
        [{"role": "user", "content": "Analyze this traceback and refactor the entire system architecture for optimization. Traceback: ..." + ("data " * 100)}],
        "gpt-5" # Expecting gpt-5-codex or gpt-5 based on config
    )
    
    if s1 and s2:
        print("\nSUMMARY: Basic Routing Matches Expectations.")
        # Note: S3 might fail if no OpenAI key, that's acceptable for logic verification if local env lacks keys.
        if s3:
            print("SUMMARY: Complex/Fallback verify PASSED.")
        else:
            print("SUMMARY: Complex/Fallback verify FAILED (or no cloud keys).")
    else:
        print("\nSUMMARY: CRITICAL ROUTING FAILURES.")
        sys.exit(1)

if __name__ == "__main__":
    main()
