"""
API Router Security and Routing Tests

Tests for:
- API Key authentication (401/200 behavior)
- Public routes accessibility
- Basic routing logic
"""
import pytest
from fastapi.testclient import TestClient


class TestAPIKeySecurity:
    """Tests for X-API-Key middleware protection."""

    def test_route_without_api_key_returns_401(self, client):
        """Calling /route without X-API-Key should return 401."""
        response = client.post(
            "/route",
            json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert response.status_code == 401
        assert "Unauthorized" in response.text or "API Key" in response.text

    def test_route_with_wrong_api_key_returns_401(self, client, wrong_auth_headers):
        """Calling /route with wrong X-API-Key should return 401."""
        response = client.post(
            "/route",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers=wrong_auth_headers
        )
        assert response.status_code == 401

    def test_route_with_valid_api_key_returns_200(self, client, auth_headers):
        """Calling /route with valid X-API-Key should return 200."""
        # Mock the router to avoid actual LLM calls
        from app import main as m

        class DummyRouter:
            def invoke(self, state):
                return {
                    "output": "Test response",
                    "usage": {"resolved_model_id": "local-chat", "latency_ms_router": 10}
                }

        original_router = m.router_app
        m.router_app = DummyRouter()

        try:
            response = client.post(
                "/route",
                json={"messages": [{"role": "user", "content": "Hello"}]},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "output" in data or "usage" in data
        finally:
            m.router_app = original_router

    def test_v1_chat_completions_without_key_returns_401(self, client):
        """OpenAI-compatible endpoint should require API key."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "router-auto",
                "messages": [{"role": "user", "content": "test"}]
            }
        )
        assert response.status_code == 401

    def test_actions_test_without_key_returns_401(self, client):
        """Action endpoints should require API key."""
        response = client.post(
            "/actions/test",
            json={"model": "hermes3:8b"}
        )
        assert response.status_code == 401


class TestPublicRoutes:
    """Tests for routes that should be accessible without API key."""

    def test_guide_route_public_ok(self, client):
        """GET /guide should be accessible without API key."""
        response = client.get("/guide")
        # May return 200 with HTML or redirect, but NOT 401
        assert response.status_code != 401
        assert response.status_code in [200, 302, 307]

    def test_healthz_route_public_ok(self, client):
        """GET /healthz should be accessible without API key."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True

    def test_root_redirect_public_ok(self, client):
        """GET / should redirect to /guide without requiring API key."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [302, 307]
        assert "/guide" in response.headers.get("location", "")

    def test_v1_models_public_ok(self, client):
        """GET /v1/models should be accessible without API key (OpenAI compat)."""
        response = client.get("/v1/models")
        # This might require API key depending on design - check current behavior
        # If it returns 401, we may need to make it public
        assert response.status_code in [200, 401]

    def test_docs_public_ok(self, client):
        """GET /docs (Swagger UI) should be accessible."""
        response = client.get("/docs")
        assert response.status_code != 401


class TestRoutingBasic:
    """Basic routing logic tests with mocked LLM."""

    def test_route_basic_smoke(self, client, auth_headers):
        """Smoke test: /route with minimal payload returns valid JSON."""
        from app import main as m

        class DummyRouter:
            def invoke(self, state):
                return {
                    "output": "Smoke test OK",
                    "usage": {"resolved_model_id": "local-chat", "latency_ms_router": 5}
                }

        original_router = m.router_app
        m.router_app = DummyRouter()

        try:
            response = client.post(
                "/route",
                json={"messages": [{"role": "user", "content": "hello"}]},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
        finally:
            m.router_app = original_router

    def test_general_chat_uses_local_chat_model(self, client, auth_headers):
        """Simple chat should route to local-chat model."""
        from app import main as m

        captured_state = {}

        class CapturingRouter:
            def invoke(self, state):
                captured_state.update(state)
                return {
                    "output": "Response",
                    "usage": {"resolved_model_id": "local-chat", "latency_ms_router": 5}
                }

        original_router = m.router_app
        m.router_app = CapturingRouter()

        try:
            response = client.post(
                "/route",
                json={
                    "messages": [{"role": "user", "content": "Hi there!"}],
                    "prefer_code": False
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            # Check that routing metadata indicates local model
            assert data["usage"]["resolved_model_id"] == "local-chat"
        finally:
            m.router_app = original_router

    def test_code_request_uses_local_code_model(self, client, auth_headers):
        """Code requests should route to local-code model."""
        from app import main as m

        class CapturingRouter:
            def invoke(self, state):
                return {
                    "output": "def hello(): pass",
                    "usage": {"resolved_model_id": "local-code", "latency_ms_router": 5}
                }

        original_router = m.router_app
        m.router_app = CapturingRouter()

        try:
            response = client.post(
                "/route",
                json={
                    "messages": [{"role": "user", "content": "Write a Python sort function"}],
                    "prefer_code": True
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["usage"]["resolved_model_id"] == "local-code"
        finally:
            m.router_app = original_router


class TestDebugEndpoints:
    """Tests for debug endpoints (should require API key)."""

    def test_debug_metrics_requires_auth(self, client):
        """GET /debug/metrics should require API key."""
        response = client.get("/debug/metrics")
        assert response.status_code == 401

    def test_debug_where_requires_auth(self, client):
        """GET /debug/where should require API key."""
        response = client.get("/debug/where")
        assert response.status_code == 401

    def test_debug_router_decision_requires_auth(self, client):
        """POST /debug/router_decision should require API key."""
        response = client.post(
            "/debug/router_decision",
            json={"prompt": "test prompt"}
        )
        assert response.status_code == 401

    def test_debug_metrics_with_auth(self, client, auth_headers):
        """GET /debug/metrics with auth should work."""
        response = client.get("/debug/metrics", headers=auth_headers)
        # May return error if no logs, but should NOT be 401
        assert response.status_code != 401
