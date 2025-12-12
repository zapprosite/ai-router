"""
Automatic Routing Evaluation Test Suite

Tests the zero-configuration, complexity-aware routing system.
No manual flags required - routing is inferred from prompts.
"""
import sys
import os
import pytest

sys.path.insert(0, os.getcwd())

# Mock environment for testing
# NOTE: We DO NOT set "ENABLE_OPENAI_FALLBACK=1" here.
# The system should automatically enable cloud because the API key is present.
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key"

from graph.router import (
    classify_prompt,
    select_model_from_policy,
    RoutingMeta,
    REG,
    ROUTING_POLICY,
)


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
        assert model in ["local-code", "gpt-5.1-codex-mini"], f"Got: {model}"
    
    def test_critical_routes_to_cloud(self):
        """Critical tasks should route to cloud reasoning models."""
        meta = RoutingMeta(task="code_crit_debug", complexity="critical")
        model = select_model_from_policy(meta)
        # Now routes to gpt-5.1-codex-high
        assert any(m in model for m in ["gpt-5.1-codex-high", "o3", "o3-mini"]), f"Expected o3, got: {model}"
    
    def test_system_design_high_routes_to_o3(self):
        """High-complexity system design should route to O3."""
        meta = RoutingMeta(task="system_design", complexity="high")
        model = select_model_from_policy(meta)
        assert model in ["gpt-5.1-codex-high", "o3", "o3-mini-high"], f"Got: {model}"


class TestEndToEndRouting:
    """Test complete routing from prompt to model selection."""
    
    def test_e2e_simple_greeting(self):
        """'Hi' should route to local fast model."""
        meta = classify_prompt([{"role": "user", "content": "Hi"}])
        model = select_model_from_policy(meta)
        assert model == "local-chat"
    
    def test_e2e_code_request(self):
        """Code requests should route to code-capable models."""
        meta = classify_prompt([{"role": "user", "content": "Write a Python function for quicksort"}])
        model = select_model_from_policy(meta)
        assert model in ["local-code", "gpt-5.1-codex-mini", "gpt-5.1-codex"]
    
    def test_e2e_deadlock_analysis(self):
        """Deadlock analysis should route to premium cloud."""
        meta = classify_prompt([{"role": "user", "content": "Analyze this deadlock stack trace in our production database"}])
        model = select_model_from_policy(meta)
        assert any(m in model for m in ["gpt-5.1-codex-high", "o3", "o3-mini"]), f"Got: {model}"
        assert meta.complexity in ['high', 'critical']
    
    def test_e2e_system_design(self):
        """System design should route to reasoning models."""
        meta = classify_prompt([{"role": "user", "content": "Design a distributed HVAC control system with failover"}])
        model = select_model_from_policy(meta)
        assert any(m in model for m in ["gpt-5.1-codex-high", "o3", "o3-mini"]), f"Got: {model}"
        assert meta.complexity in ['high', 'critical']


class TestRoutingMetadata:
    """Test that routing metadata is properly structured."""
    
    def test_routing_meta_has_required_fields(self):
        """RoutingMeta should have all required fields."""
        meta = classify_prompt([{"role": "user", "content": "Test prompt"}])
        
        assert hasattr(meta, "task")
        assert hasattr(meta, "complexity")
        assert hasattr(meta, "confidence")
        assert hasattr(meta, "classifier_used")
        assert hasattr(meta, "requires_long_context")
    
    def test_confidence_is_valid(self):
        """Confidence should be between 0 and 1."""
        meta = classify_prompt([{"role": "user", "content": "Test prompt"}])
        assert 0.0 <= meta.confidence <= 1.0
    
    def test_task_is_known(self):
        """Task should be a known task type."""
        from graph.router import TASK_TYPES
        
        prompts = ["Hi", "Write code", "Analyze this deadlock"]
        for prompt in prompts:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            assert meta.task in TASK_TYPES or meta.task == "simple_qa", f"Unknown task: {meta.task}"


def run_eval():
    """Legacy entry point for pytest discovery."""
    print("=== Automatic Routing Evaluation ===\n")
    
    test_cases = [
        # (prompt, expected_tier_or_model)
        ("Hi", "local-chat"),
        ("What is the capital of France?", "local-chat"),
        ("Write a Python function to sort a list", "local-code"),
        ("Analyze this deadlock in production", "o3"),
        ("Design a distributed system architecture", "o3"),
        ("Traceback (most recent call last):", "local-code"),
        ("Security vulnerability in authentication", "o3"),
        ("Race condition in payment processing", "o3"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for prompt, expected in test_cases:
        meta = classify_prompt([{"role": "user", "content": prompt}])
        model = select_model_from_policy(meta)
        
        # Check if we got the expected model or a reasonable alternative
        is_pass = (model == expected) or (
            expected in ["o3", "gpt-5.1-codex"] and model in ["o3", "o3-mini-high", "gpt-5.1-codex"]
        ) or (
            expected == "local-code" and model in ["local-code", "gpt-5.1-codex-mini"]
        )
        
        status = "✅" if is_pass else "❌"
        if is_pass:
            passed += 1
        else:
            print(f"{status} Prompt: '{prompt[:40]}...' -> Got: {model} (Expected: {expected})")
            print(f"   Meta: task={meta.task}, complexity={meta.complexity}")
    
    score = (passed / total) * 100
    print(f"\nFinal Score: {passed}/{total} ({score:.1f}%)")
    
    if score < 80:
        print("FAILED: Score below 80%")
        return False
    else:
        print("PASSED: Automatic Routing Logic is Sound.")
        return True


if __name__ == "__main__":
    success = run_eval()
    sys.exit(0 if success else 1)
