import os
import requests
from tests.utils import wait_until_healthy

BASE_URL = os.getenv("ROUTER_BASE_URL", "http://localhost:8082")

def test_healthz_ok():
    wait_until_healthy(BASE_URL, timeout=60)
    r = requests.get(f"{BASE_URL}/healthz", timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert j.get("ok") is True

def test_models_shape():
    wait_until_healthy(BASE_URL, timeout=60)
    r = requests.get(f"{BASE_URL}/v1/models", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "data" in j and isinstance(j["data"], list)
    # aceita lista vazia, mas valida formato quando houver modelos
    for m in j["data"]:
        assert isinstance(m, dict)
        assert "id" in m
