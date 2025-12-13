
from graph.router import RoutingMeta, select_model_from_policy


class TestQualityJudge:
    def test_high_quality_forces_cloud(self):
        """
        Scenario: User asks for 'Perfect Code' (Quality 9/10).
        Expectation: Even simple tasks should upgrade to 'critical' tier models (Cloud).
        """
        meta = RoutingMeta(
            task="code_gen",
            complexity="low",
            quality_score=9 # High Quality Force
        )
        
        # In config, code_gen.critical -> ["gpt-5.2-codex-high", "o3"]
        model = select_model_from_policy(meta)
        
        # Should NOT use local-code
        assert "local-code" not in model
        assert "gpt-5.2-codex-high" in model or "o3" in model or "gpt-4" in model

    def test_low_quality_stays_local(self):
        """
        Scenario: User asks for 'Draft/Quick' (Quality 3/10).
        Expectation: Standard tasks stay on Local GPU.
        """
        meta = RoutingMeta(
            task="code_gen",
            complexity="medium", # Usually might escalate
            quality_score=3 # Low Quality Force
        )
        
        # In config, code_gen.medium -> ["local-code", "gpt-4.1-mini"]
        # But we want to ensure it DOESN'T jump to High/Critical
        model = select_model_from_policy(meta)
        
        # Should favor local or mini
        assert "gpt-5.2-codex-high" not in model
        assert "o3" not in model

    def test_machine_learning_domain_routing(self):
        """
        Scenario: Task is 'machine_learning'.
        Expectation: Even medium complexity ML tasks go to Cloud (Tier 5).
        """
        meta = RoutingMeta(
            task="machine_learning",
            complexity="medium",
            quality_score=5
        )
        
        # In config, machine_learning.medium -> ["gpt-5.2-codex-high"]
        model = select_model_from_policy(meta)
        
        assert "gpt-5.2" in model
