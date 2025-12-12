import json
import os
from fastapi.testclient import TestClient

# Set test API key
os.environ["AI_ROUTER_API_KEY"] = "test_secret_key_12345"


def test_chat_completions_openai_shim(monkeypatch):
    # Import app and override router_app with a dummy invoker
    from app import main as m

    class DummyRouter:
        def invoke(self, state):
            assert "messages" in state
            return {
                "output": "OK RESULT",
                "usage": {"resolved_model_id": "dummy-model"},
            }

    m.router_app = DummyRouter()
    client = TestClient(m.app)

    payload = {
        "model": "router-auto",
        "messages": [{"role": "user", "content": "test"}],
    }
    resp = client.post("/v1/chat/completions", json=payload, headers={"X-API-Key": "test_secret_key_12345"})
    assert resp.status_code == 200
    data = resp.json()

    # OpenAI format basics
    assert data.get("object") == "chat.completion"
    assert data.get("model") == "dummy-model"
    assert isinstance(data.get("choices"), list) and len(data["choices"]) >= 1
    msg = data["choices"][0]["message"]
    assert msg["role"] == "assistant"
    assert msg["content"] == "OK RESULT"
    assert data.get("usage", {}).get("resolved_model_id") == "dummy-model"


def test_models_includes_router_auto():
    from app import main as m
    client = TestClient(m.app)
    resp = client.get("/v1/models", headers={"X-API-Key": "test_secret_key_12345"})
    assert resp.status_code == 200
    data = resp.json()
    ids = [d.get("id") for d in data.get("data", [])]
    assert "router-auto" in ids

