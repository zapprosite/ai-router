
def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert j.get("ok") is True


def test_v1_chat_completions_router(client, auth_headers):
    body = {
        "model": "router-auto",
        "messages": [{"role": "user", "content": "Say hi."}],
    }
    r = client.post("/v1/chat/completions", json=body, headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    # router shim should return either a model field or a usage.resolved_model_id
    assert isinstance(j, dict)
    has_model = bool(j.get("model"))
    has_usage = bool(j.get("usage") and j["usage"].get("resolved_model_id"))
    has_choices = bool(j.get("choices"))
    assert has_model or has_usage or has_choices
