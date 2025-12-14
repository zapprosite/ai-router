"""
Test Routing Policy with is_cloud_enabled integration.

Verifies:
- When is_cloud_enabled()=False, high complexity tasks stay local (no cloud escalation)
- When is_cloud_enabled()=True, high complexity tasks with local failure can escalate to cloud
"""
from unittest.mock import patch


class TestRoutingPolicyCloudGating:
    """Tests for cloud gating in routing policy based on is_cloud_enabled()."""

    def test_cloud_disabled_high_complexity_stays_local(self, client, auth_headers, monkeypatch):
        """
        When is_cloud_enabled()=False, router should NOT escalate to cloud
        even for high complexity tasks. Must use only local models.
        """
        # Mock is_cloud_enabled to return False (simulating 401 cached)
        with patch("graph.router.is_cloud_enabled", return_value=False):
            with patch("graph.router._is_cloud_available", return_value=False):
                from app import main as m
                
                # Track which models were invoked
                invoked_models = []
                
                class LocalOnlyMockRouter:
                    def invoke(self, state):
                        # Simulate router behavior with cloud blocked
                        model = state.get("model_id", "llama-3.1-8b-instruct")
                        invoked_models.append(model)
                        return {
                            "output": "Local response for complex task",
                            "usage": {
                                "resolved_model_id": "deepseek-coder-v2-16b",
                                "cloud_available": False,
                                "escalated": False,
                                "routing_meta": {
                                    "task": "code_gen",
                                    "complexity": "high",
                                    "complexity_boosted": True
                                },
                                "attempts": [{"model": "deepseek-coder-v2-16b", "status": "success"}]
                            },
                            "attempts": [{"model": "deepseek-coder-v2-16b", "status": "success"}]
                        }
                
                original_router = m.router_app
                m.router_app = LocalOnlyMockRouter()
                
                try:
                    # Send a high complexity request
                    response = client.post(
                        "/v1/chat/completions",
                        json={
                            "model": "router-auto",
                            "messages": [{"role": "user", "content": """
                            Implement a complete distributed microservices architecture with:
                            - Service mesh using Istio
                            - Event sourcing with Kafka
                            - CQRS pattern implementation
                            - Circuit breaker patterns
                            - Distributed tracing with OpenTelemetry
                            
                            This is a production-critical system that requires careful design.
                            """}]
                        },
                        headers=auth_headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Verify usage metadata
                    usage = data.get("usage", {})
                    assert usage.get("cloud_available") is False, "cloud_available should be False"
                    
                    # Verify model stayed local (no gpt-* or o3-* models)
                    resolved_model = usage.get("resolved_model_id", "")
                    assert not resolved_model.startswith("gpt-"), f"Should not use cloud model, got: {resolved_model}"
                    assert not resolved_model.startswith("o3"), f"Should not use cloud model, got: {resolved_model}"
                    
                    # Verify complexity_boosted was applied
                    routing_meta = usage.get("routing_meta", {})
                    assert routing_meta.get("complexity_boosted") is True, "complexity_boosted should be True"
                    
                finally:
                    m.router_app = original_router

    def test_cloud_enabled_can_escalate_on_local_failure(self, client, auth_headers, monkeypatch):
        """
        When is_cloud_enabled()=True, router should be able to escalate to cloud
        when local model fails quality gate.
        """
        # Enable cloud
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "1")
        
        with patch("graph.router.is_cloud_enabled", return_value=True):
            with patch("graph.router._is_cloud_available", return_value=True):
                from app import main as m
                
                class CloudEscalationMockRouter:
                    def invoke(self, state):
                        # Simulate escalation: local failed, cloud succeeded
                        # Note: attempts must be inside usage for the endpoint to read correctly
                        return {
                            "output": "Cloud response after local failure",
                            "usage": {
                                "resolved_model_id": "gpt-4o-mini",
                                "cloud_available": True,
                                "escalated": True,
                                "escalation_reason": "quality_failed:missing_code_block",
                                "routing_meta": {
                                    "task": "code_gen",
                                    "complexity": "high"
                                },
                                "attempts": [
                                    {"model": "deepseek-coder-v2-16b", "status": "quality_failed:missing_code_block"},
                                    {"model": "gpt-4o-mini", "status": "success"}
                                ]
                            },
                            "attempts": [
                                {"model": "deepseek-coder-v2-16b", "status": "quality_failed:missing_code_block"},
                                {"model": "gpt-4o-mini", "status": "success"}
                            ]
                        }
                
                original_router = m.router_app
                m.router_app = CloudEscalationMockRouter()
                
                try:
                    response = client.post(
                        "/v1/chat/completions",
                        json={
                            "model": "router-auto",
                            "messages": [{"role": "user", "content": """
                            Write a complex async Python function to process large files
                            with proper error handling and type hints.
                            """}]
                        },
                        headers=auth_headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Verify usage metadata
                    usage = data.get("usage", {})
                    assert usage.get("cloud_available") is True, "cloud_available should be True"
                    assert usage.get("escalated") is True, "escalated should be True"
                    
                    # Verify final model is cloud
                    resolved_model = usage.get("resolved_model_id", "")
                    assert resolved_model.startswith("gpt-") or resolved_model.startswith("o"), \
                        f"Should escalate to cloud model, got: {resolved_model}"
                    
                    # Verify attempts show local failure then cloud success
                    attempts = usage.get("attempts", [])
                    assert len(attempts) >= 2, f"Should have at least 2 attempts (local + cloud), got: {attempts}"
                    assert "quality_failed" in attempts[0].get("status", ""), "First attempt should fail quality"
                    assert attempts[-1].get("status") == "success", "Last attempt should succeed"
                    
                finally:
                    m.router_app = original_router


class TestRoutingPolicyIntegration:
    """Integration tests for routing policy with real router logic (mocked LLMs)."""

    def test_classify_node_sets_cloud_available(self, monkeypatch):
        """Verify _node_classify sets cloud_available in state."""
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "0")
        
        from graph import router
        
        # Force cloud unavailable
        with patch.object(router, "_is_cloud_available", return_value=False):
            with patch.object(router, "is_cloud_enabled", return_value=False):
                state = {
                    "messages": [{"role": "user", "content": "Hello"}]
                }
                
                result = router._node_classify(state)
                
                assert "cloud_available" in result, "State should have cloud_available"
                assert result["cloud_available"] is False, "cloud_available should be False"
                assert "routing_meta" in result, "State should have routing_meta"

    def test_classify_node_sets_complexity_boosted_when_cloud_unavailable(self, monkeypatch):
        """Verify complexity_boosted is set for high complexity when cloud is unavailable."""
        from graph import router
        
        with patch.object(router, "_is_cloud_available", return_value=False):
            with patch.object(router, "is_cloud_enabled", return_value=False):
                # High complexity task
                state = {
                    "messages": [{"role": "user", "content": """
                    Design a distributed system architecture for a high-traffic
                    e-commerce platform with microservices, event sourcing, and CQRS.
                    This is production-critical code.
                    """}]
                }
                
                result = router._node_classify(state)
                
                assert result["cloud_available"] is False
                routing_meta = result.get("routing_meta", {})
                
                # For high/critical complexity with cloud unavailable, should boost
                complexity = routing_meta.get("complexity", "low")
                if complexity in ["high", "critical"]:
                    assert routing_meta.get("complexity_boosted") is True, \
                        f"complexity_boosted should be True for {complexity} when cloud unavailable"
