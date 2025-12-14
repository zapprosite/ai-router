#!/usr/bin/env python3
"""
Test each model in the AI Router and display responses in terminal.

Usage:
    python scripts/test_models.py
    python scripts/test_models.py --model local-chat
    python scripts/test_models.py --prompt "Explain Python decorators"
"""

import argparse
import os
import sys
import time

import requests

# Default router URL
ROUTER_URL = "http://localhost:8082"

# API Key (from env or default)
API_KEY = os.getenv("AI_ROUTER_API_KEY", "sk-router-change-me")

# Test prompt
DEFAULT_PROMPT = "Olá! Responda em uma frase curta: qual é seu nome e modelo?"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def get_headers() -> dict:
    """Return headers with API key authentication."""
    return {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }


def get_available_models(base_url: str) -> list:
    """Fetch available models from the router."""
    try:
        resp = requests.get(f"{base_url}/v1/models", headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        else:
            print(f"{Colors.RED}Failed to fetch models: {resp.status_code}{Colors.ENDC}")
            return []
    except Exception as e:
        print(f"{Colors.RED}Error fetching models: {e}{Colors.ENDC}")
        return []


def test_model(base_url: str, model_id: str, prompt: str, timeout: int = 30) -> dict:
    """
    Send a chat completion request to a specific model.
    Returns dict with response, latency, and status.
    """
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    start_time = time.time()
    
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=timeout,
            headers=get_headers()
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            return {
                "status": "success",
                "content": content,
                "latency_ms": latency_ms,
                "usage": usage,
                "resolved_model": data.get("model", model_id)
            }
        else:
            return {
                "status": "error",
                "content": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "latency_ms": latency_ms
            }
    except requests.Timeout:
        return {
            "status": "timeout",
            "content": f"Request timed out after {timeout}s",
            "latency_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "status": "error",
            "content": str(e),
            "latency_ms": int((time.time() - start_time) * 1000)
        }


def print_result(model_id: str, result: dict):
    """Pretty print the result for a model."""
    status = result["status"]
    latency = result.get("latency_ms", 0)
    
    # Status color
    if status == "success":
        status_color = Colors.GREEN
        status_icon = "✅"
    elif status == "timeout":
        status_color = Colors.YELLOW
        status_icon = "⏱️"
    else:
        status_color = Colors.RED
        status_icon = "❌"
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}📦 Model: {Colors.YELLOW}{model_id}{Colors.ENDC}")
    print(f"{status_icon} Status: {status_color}{status}{Colors.ENDC} | ⏱️ Latency: {latency}ms")
    
    if result.get("resolved_model"):
        print(f"🔄 Resolved to: {Colors.BLUE}{result['resolved_model']}{Colors.ENDC}")
    
    if result.get("usage"):
        usage = result["usage"]
        print(f"📊 Tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}")
    
    print(f"\n{Colors.BOLD}💬 Response:{Colors.ENDC}")
    print(f"{Colors.GREEN}{result.get('content', 'No content')}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Test AI Router models")
    parser.add_argument("--url", default=ROUTER_URL, help="Router base URL")
    parser.add_argument("--model", "-m", help="Test specific model only")
    parser.add_argument("--prompt", "-p", default=DEFAULT_PROMPT, help="Custom prompt")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--local-only", "-l", action="store_true", help="Test only local models")
    args = parser.parse_args()
    
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 60)
    print("🚀 AI Router - Model Test Suite")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print(f"🌐 Router URL: {args.url}")
    print(f"💬 Prompt: {args.prompt[:50]}...")
    
    # Get available models
    models = get_available_models(args.url)
    
    if not models:
        print(f"{Colors.RED}No models available. Is the router running?{Colors.ENDC}")
        sys.exit(1)
    
    # Filter models
    if args.model:
        if args.model in models:
            models = [args.model]
        else:
            print(f"{Colors.RED}Model '{args.model}' not found.{Colors.ENDC}")
            print(f"Available: {', '.join(models)}")
            sys.exit(1)
    
    if args.local_only:
        # Filter to local models only (not gpt/o3 prefixed)
        models = [m for m in models if not m.startswith(("gpt-", "o3", "o1"))]
    
    print(f"\n📋 Testing {len(models)} models...")
    
    results = {}
    for model_id in models:
        print(f"\n{Colors.YELLOW}Testing {model_id}...{Colors.ENDC}", end="", flush=True)
        result = test_model(args.url, model_id, args.prompt, args.timeout)
        results[model_id] = result
        print_result(model_id, result)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    
    success = sum(1 for r in results.values() if r["status"] == "success")
    failed = sum(1 for r in results.values() if r["status"] == "error")
    timeout = sum(1 for r in results.values() if r["status"] == "timeout")
    
    print(f"{Colors.GREEN}✅ Success: {success}{Colors.ENDC}")
    print(f"{Colors.RED}❌ Failed: {failed}{Colors.ENDC}")
    print(f"{Colors.YELLOW}⏱️ Timeout: {timeout}{Colors.ENDC}")
    
    if success > 0:
        avg_latency = sum(r["latency_ms"] for r in results.values() if r["status"] == "success") / success
        print(f"⏱️ Avg Latency (success): {avg_latency:.0f}ms")
    
    # Exit code
    sys.exit(0 if failed == 0 and timeout == 0 else 1)


if __name__ == "__main__":
    main()
