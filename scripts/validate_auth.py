
import os
from pathlib import Path

import yaml
from openai import OpenAI

# Load project config to get real mappings
ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "config" / "router_config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

def check_openai_auth():
    print("=== OpenAI Auth Validator ===")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_TIER2")
    
    if not api_key:
        print("[FAIL] No OPENAI_API_KEY or OPENAI_API_KEY_TIER2 found in env.")
        print("Please check your .env file.")
        return False
        
    print(f"[INFO] API Key found (starts with {api_key[:8]}...)")
    
    client = OpenAI(api_key=api_key)
    
    # Models to test
    # We test the *real* names that the router resolves to
    models_to_test = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    
    # Also check if user has defined older models
    custom_models = [
        os.getenv("OPENAI_CODE_MINI"),
        os.getenv("OPENAI_CODE_STANDARD")
    ]
    
    print("\n--- Testing Model Access ---")
    for model in models_to_test + [m for m in custom_models if m]:
        # Resolve internal alias to real name if needed
        real_name = model
        # Simple lookup in config for aliases
        for m_cfg in CONFIG["models"]:
            if m_cfg["id"] == model:
                real_name = m_cfg["name"]
                break
        
        print(f"Testing access to '{model}' (Mapped to: '{real_name}')...", end=" ")
        try:
            client.chat.completions.create(
                model=real_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            print("✅ OK")
        except Exception as e:
            if "bf2042" in str(e): # Access denied / 401
                print("❌ 401 UNAUTHORIZED / ACCESS DENIED")
            else:
                 # Clean up error message
                err = str(e).split('\n')[0]
                print(f"❌ ERROR: {err}")

if __name__ == "__main__":
    check_openai_auth()
