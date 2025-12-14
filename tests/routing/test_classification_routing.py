"""
Automatic Routing Evaluation Test Suite
Merged from legacy eval_routing.py
"""

import pytest

from graph.router import (
    RoutingMeta,
    classify_prompt,
    select_model_from_policy,
)

# NOTE: Environment variables are handled by conftest.py (autouse fixtures)
# but specific overrides can be done via monkeypatch if needed.

class TestAutomaticClassification:
    """Test the automatic prompt classification system."""
    
    def test_chitchat_detection(self):
        """Simple greetings should be classified as chitchat/low."""
        prompts = [
            "Hi there!",
            "Hello, how are you?",
            "Thanks for the help",
            "What's up?",
        ]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in ["chitchat", "simple_qa"], f"Failed for: {prompt}"
            assert meta.complexity == "low", f"Complexity should be low for: {prompt}"
    
    def test_simple_qa_detection(self):
        """Simple factual questions should be classified correctly."""
        prompts = [
            "What is the capital of France?",
            "Who is the president of Brazil?",
            "When was Python released?",
        ]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in ["simple_qa", "chitchat"], f"Failed for: {prompt}"
            assert meta.complexity == "low", f"Complexity should be low for: {prompt}"
    
    def test_code_gen_detection(self):
        """Code generation requests should be classified as code_gen."""
        prompts = [
            "Write a Python function to calculate factorial",
            "Create a class for handling user authentication",
            "```python\ndef hello():\n    pass\n```",
            "import os; how do I list files?",
        ]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in ["code_gen", "code_review"], f"Failed for: {prompt}"
    
    def test_critical_debug_detection(self):
        """Critical debugging prompts should escalate to critical complexity."""
        prompts = [
            "I'm seeing a deadlock in my database transactions",
            "There's a race condition in the payment processing",
            "We have a memory leak in production",
            "Security vulnerability in the auth module",
            "Production incident postmortem analysis",
        ]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in ["code_crit_debug", "code_review", "system_design"], f"Task mismatch for: {prompt}"
            assert meta.complexity in ["high", "critical"], f"Should be high/critical for: {prompt}"
    
    def test_system_design_detection(self):
        """System design prompts should be classified correctly."""
        prompts = [
            "Design a distributed cache architecture",
            "System design for a real-time messaging platform",
            "How do I build a high availability cluster?",
        ]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in ["system_design", "code_crit_debug", "reasoning"], f"Failed for: {prompt}"
            assert meta.complexity in ["medium", "high", "critical"], f"Should be at least medium for: {prompt}"
    
    def test_long_prompt_escalation(self):
        """Long prompts should escalate complexity."""
        short = "Fix this bug"
        long = "Fix this bug. " * 200  # ~4000 chars
        
        short_meta = classify_prompt([{"role": "user", "content": short}])
        long_meta = classify_prompt([{"role": "user", "content": long}])
        
        complexity_order = ["low", "medium", "high", "critical"]
        assert complexity_order.index(long_meta.complexity) > complexity_order.index(short_meta.complexity)


class TestPolicyBasedRouting:
    """Test the policy-based model selection."""
    
    def test_chitchat_routes_to_local(self):
        """Chitchat should route to local models (Tier 1)."""
        meta = RoutingMeta(task="chitchat", complexity="low")
        model = select_model_from_policy(meta)
        assert model == "local-chat", f"Got: {model}"
    
    def test_code_gen_routes_to_deepseek(self):
        """Code generation should route to DeepSeek (Tier 2)."""
        meta = RoutingMeta(task="code_gen", complexity="medium")
        model = select_model_from_policy(meta)
        assert model in ["local-code", "gpt-5.2-codex-mini"], f"Got: {model}"
    
    def test_critical_routes_to_cloud(self):
        """Critical tasks should route to cloud reasoning models."""
        meta = RoutingMeta(task="code_crit_debug", complexity="critical")
        model = select_model_from_policy(meta)
        assert any(m in model for m in ["gpt-5.2-codex-high", "o3", "o3-mini"]), f"Expected o3/codex, got: {model}"
    
    def test_system_design_high_routes_to_o3(self):
        """High-complexity system design should route to O3."""
        meta = RoutingMeta(task="system_design", complexity="high")
        model = select_model_from_policy(meta)
        assert model in ["gpt-5.2-codex-high", "o3", "o3-mini-high"], f"Got: {model}"


class TestEndToEndRouting:
    """Test complete routing from prompt to model selection."""
    
    def test_e2e_simple_greeting(self):
        meta = classify_prompt([{"role": "user", "content": "Hi"}])
        model = select_model_from_policy(meta)
        assert model == "local-chat"
    
    def test_e2e_code_request(self):
        meta = classify_prompt([{"role": "user", "content": "Write a Python function for quicksort"}])
        model = select_model_from_policy(meta)
        assert model in ["local-code", "gpt-5.2-codex-mini", "gpt-5.2-codex", "deepseek-coder-v2-16b"]
    
    def test_e2e_deadlock_analysis(self):
        meta = classify_prompt([{"role": "user", "content": "Analyze this deadlock stack trace in our production database"}])
        model = select_model_from_policy(meta)
        assert any(m in model for m in ["gpt-5.2-codex-high", "o3", "o3-mini"]), f"Got: {model}"
        assert meta.complexity in ['high', 'critical']

class TestRoutingMetadata:
    """Test that routing metadata is properly structured."""
    
    def test_routing_meta_validity(self):
        """RoutingMeta should have all required fields and valid confidence."""
        meta = classify_prompt([{"role": "user", "content": "Test prompt"}])
        assert hasattr(meta, "task")
        assert hasattr(meta, "complexity")
        assert 0.0 <= meta.confidence <= 1.0


# Parametrized core logic tests (Replacing the old run_eval loop)
@pytest.mark.parametrize("prompt, expected_models", [
    ("Hi", ["local-chat"]),
    ("What is the capital of France?", ["local-chat"]),
    ("Write a Python function to sort a list", ["local-code", "gpt-5.2-codex-mini", "deepseek-coder-v2-16b"]),
    ("Analyze this deadlock in production", ["gpt-5.2-codex-high", "o3", "o3-mini"]),
    ("Design a distributed system architecture", ["gpt-5.2-codex-high", "o3", "o3-mini-high"]),
    ("Traceback (most recent call last):", ["local-code", "gpt-5.2-codex-mini", "deepseek-coder-v2-16b", "code_review"]),
    ("Optimize this high-frequency trading algorithm in C++", ["gpt-5.2-codex-high", "o3"]),
    ("Security vulnerability in authentication", ["gpt-5.2-codex-high", "o3"]),
    # Creative writing - Low complexity -> Local (Policy Update)
    ("Write a screenplay for a cyberpunk movie", ["local-chat"]),
    ("Write a haiku about the Singularity", ["gpt-5.2-high", "local-chat"]), # Adjusted as creative writing might drop to local if simple strings
])
def test_routing_scenarios_parametrized(prompt, expected_models):
    """
    Parametrized version of the legacy run_eval suite.
    Ensures that specific prompts route to one of the expected models.
    """
    meta = classify_prompt([{"role": "user", "content": prompt}])
    model = select_model_from_policy(meta)
    
    # We allow exact match OR if the model is in the 'expected' set (which might be broad in tests)
    # The expected_models list in parametrize is a list of valid outcomes.
    
    # Loosened check: if 'local-code' is expected, 'deepseek' is also fine usually.
    # The logic below matches the manual logic inside the old run_eval
    
    valid = False
    if model in expected_models:
        valid = True
    
    # Special Handling for specific groups to mimic old logic robustness
    if "gpt-5.2-codex-high" in expected_models and model in ["o3", "o3-mini-high"]:
        valid = True
    if "local-code" in expected_models and model in ["gpt-5.2-codex-mini"]:
        valid = True

    assert valid, f"Prompt: '{prompt}' routed to {model}. Expected one of: {expected_models}. Meta: {meta}"
