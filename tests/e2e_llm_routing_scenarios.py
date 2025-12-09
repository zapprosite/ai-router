import os
import requests


BASE = os.getenv("AI_ROUTER_BASE", "http://localhost:8082").rstrip("/")


def test_healthz():
	r = requests.get(f"{BASE}/healthz", timeout=5)
	assert r.status_code == 200
	j = r.json()
	assert isinstance(j, dict)
	assert j.get("ok") is True


def test_v1_chat_completions_router():
	body = {
		"model": "router-auto",
		"messages": [{"role": "user", "content": "Say hi."}],
	}
	r = requests.post(f"{BASE}/v1/chat/completions", json=body, timeout=15)
	assert r.status_code == 200
	j = r.json()
	# router shim should return either a model field or a usage.resolved_model_id
	assert isinstance(j, dict)
	has_model = bool(j.get("model"))
	has_usage = bool(j.get("usage") and j["usage"].get("resolved_model_id"))
	has_choices = bool(j.get("choices"))
	assert has_model or has_usage or has_choices
