import sys
import os
import time

# Ensure we can import from project root
sys.path.insert(0, os.getcwd())

# Load environment
from dotenv import load_dotenv
load_dotenv("config/.env.local")

from graph.router import REG
from providers.openai_client import make_openai
from providers.ollama_client import make_ollama

# Prompt to send
PROMPT = "Explain the concept of 'Recursion' in one short sentence."

def run_tour():
    print(f"=== AI ROUTER MODEL TOUR ===")
    print(f"Prompt: {PROMPT}\n")

    for model_id, meta in REG.items():
        print(f"Testing model: {model_id} ... ", end="", flush=True)
        provider = meta.get("provider", "ollama")
        model_real_name = meta.get("name", model_id)
        
        try:
            start_t = time.perf_counter()
            chain = None
            
            if provider == "openai":
                # Check for key availability before trying to save time/errors
                if not os.getenv("OPENAI_API_KEY"):
                     print("SKIPPED (No API Key)")
                     continue
                chain = make_openai(model_real_name)
            else:
                chain = make_ollama(model_real_name)
                
            # Invoke
            # The chain usually expects {"messages": [...]}
            input_payload = {"messages": [{"role": "user", "content": PROMPT}]}
            response = chain.invoke(input_payload)
            
            # The output of the chain is usually a string (content) or an object depending on chain construction.
            # In router.py, to_text is usually the last step.
            
            duration = (time.perf_counter() - start_t) * 1000
            print(f"OK ({duration:.0f}ms)")
            print(f" > Response: {str(response)[:100]}...")
            print("-" * 40)
            
        except Exception as e:
            print(f"FAILED")
            print(f" > Error: {e}")
            print("-" * 40)

if __name__ == "__main__":
    run_tour()
