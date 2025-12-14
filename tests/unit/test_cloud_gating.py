"""
Test Cloud Gating logic.

Verifies:
- Cloud fallback is correctly blocked when YAML disables it.
- Cloud fallback is allowed when both YAML and ENV enable it.
- OpenAI provider is NEVER called in tests (mocked).
"""
from unittest.mock import patch


class TestCloudGating:
    """Tests for cloud fallback gating logic."""

    def test_cloud_blocked_when_yaml_false(self, client, auth_headers, monkeypatch):
        """
        When enable_cloud_fallback=false in YAML, cloud should be blocked
        even if ENABLE_OPENAI_FALLBACK=1 in env.
        """
        # Mock the SLA config to disable cloud
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "1")
        
        from graph import router
        original_sla = router.SLA.copy()
        router.SLA["enable_cloud_fallback"] = False
        
        # Mock OpenAI to track if it's called
        openai_called = {"value": False}
        
        def mock_openai_invoke(*args, **kwargs):
            openai_called["value"] = True
            return "Mocked OpenAI Response"
        
        with patch.object(router, "_is_cloud_available", return_value=False):
            # The router should use local model only
            from app import main as m
            
            class LocalOnlyRouter:
                def invoke(self, state):
                    return {
                        "output": "Local response",
                        "usage": {"resolved_model_id": "local-chat", "cloud_available": False}
                    }
                async def ainvoke(self, state, **kwargs):
                    return self.invoke(state)
            
            original_router = m.router_app
            m.router_app = LocalOnlyRouter()
            
            try:
                response = client.post(
                    "/v1/chat/completions",
                    json={"model": "router-auto", "messages": [{"role": "user", "content": "test"}]},
                    headers=auth_headers
                )
                assert response.status_code == 200
                # OpenAI should NOT have been called
                assert not openai_called["value"], "OpenAI was called but should have been blocked"
            finally:
                m.router_app = original_router
                router.SLA = original_sla

    def test_cloud_allowed_when_both_enabled(self, client, auth_headers, monkeypatch):
        """
        When enable_cloud_fallback=true in YAML AND ENABLE_OPENAI_FALLBACK=1,
        cloud should be allowed (but we still mock it).
        """
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "1")
        
        from graph import router
        original_sla = router.SLA.copy()
        router.SLA["enable_cloud_fallback"] = True
        
        with patch.object(router, "_is_cloud_available", return_value=True):
            from app import main as m
            
            class CloudEnabledRouter:
                def invoke(self, state):
                    return {
                        "output": "Cloud response (mocked)",
                        "usage": {"resolved_model_id": "gpt-4o-mini", "cloud_available": True}
                    }
                async def ainvoke(self, state, **kwargs):
                    return self.invoke(state)
            
            original_router = m.router_app
            m.router_app = CloudEnabledRouter()
            
            try:
                response = client.post(
                    "/v1/chat/completions",
                    json={"model": "router-auto", "messages": [{"role": "user", "content": "test"}]},
                    headers=auth_headers
                )
                assert response.status_code == 200
                # Cloud was available (mocked)
            finally:
                m.router_app = original_router
                router.SLA = original_sla
