"""
Advanced Routing Integration Tests
Enforces "Poor Dev" optimization strategy (DeepSeek First) and critical escalations.
"""
import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.getcwd())

# Mock environment
os.environ["OPENAI_API_KEY"] = "sk-test-mock"
# Ensure simple routing without LLM classifier unless necessary
os.environ["ENABLE_OPENAI_FALLBACK"] = "1"

from graph.router import classify_prompt, select_model_from_policy, RoutingMeta, REG

class TestPoorDevStrategy:
    """
    Strict regression tests for the 'Poor Dev' cost optimization strategy.
    Rule: Maximize Local/DeepSeek usage. Only Critical/Reasoning goes to Cloud.
    """

    def test_deepseek_handles_high_complexity_code(self):
        """
        High complexity code gen (scaffolding, big refactors) MUST stay on DeepSeek.
        Reason: DeepSeek V2 16B has 128k context and good reasoning, ample for drafting.
        """
        # Complex scaffolding request with sufficient length to trigger High complexity and Regex for confidence
        prompt = "Create a full e-commerce backend with FastAPI. Structure the project files." + "\n# filler comment\n" * 500 + "```python\ndef main(): pass\n```"
        meta = classify_prompt([{"role": "user", "content": prompt}])
        
        # Should be High complexity Code Gen
        assert meta.task == "code_gen"
        assert meta.complexity == "high"
        
        # Selection MUST be DeepSeek
        model = select_model_from_policy(meta)
        assert model == "local-code", f"Escalated unnecessarily to {model}"

    def test_deepseek_handles_medium_stacktraces(self):
        """
        Medium/High stack traces should stay local.
        Only 'Critical' production incidents go to Cloud.
        """
        # Standard dev stack trace
        trace = "Traceback (most recent call last):\n  File 'main.py', line 10, in <module>\n    x = 1/0\nZeroDivisionError: division by zero"
        prompt = f"Help me fix this error:\n{trace}"
        
        meta = classify_prompt([{"role": "user", "content": prompt}])
        
        # Might be high or medium depending on length, but policy says DeepSeek for both
        assert meta.task in ["code_crit_debug", "code_review"]
        
        model = select_model_from_policy(meta)
        assert model == "local-code", f"Standard traceback escalated to {model}"

    def test_escalation_for_production_critical(self):
        """
        Security/Production/Deadlock keywords MUST trigger O3.
        """
        prompt = "URGENT: Production database deadlock detected. Transactions are freezing. Analyze this pg_stat_activity output..."
        
        meta = classify_prompt([{"role": "user", "content": prompt}])
        assert meta.complexity == "critical"
        
        model = select_model_from_policy(meta)
        # Should trigger critical path -> gpt-5.1-codex-high or o3
        assert "gpt-5.1-codex-high" in model or "o3" in model

    def test_escalation_for_complex_reasoning(self):
        """
        Pure reasoning/math/architecture proofs go to O3/O4.
        """
        prompt = "Prove that P != NP using a constructive counter-example or derive the time complexity of this distributed consensus algorithm."
        
        meta = classify_prompt([{"role": "user", "content": prompt}])
        assert meta.task == "reasoning"
        assert meta.complexity in ["high", "critical"]
        
        model = select_model_from_policy(meta)
        # Should escalate to o3 or gpt-5.1-high
        assert any(m in model for m in ["gpt-5.1-high", "o3", "o3-mini"])

class TestRegexBoosting:
    """
    Verify that strong regex signals prevent unnecessary LLM classifier calls.
    (This saves $ and latency).
    """

    def test_regex_high_confidence(self):
        # Prompt with code blocks
        prompt = "```python\ndef foo(): pass\n```"
        meta = classify_prompt([{"role": "user", "content": prompt}])
        
        # Confidence should be high enough to skip LLM refinement (>0.7)
        assert meta.confidence >= 0.8
        assert meta.classifier_used == "heuristic"

    def test_ambiguous_prompt_low_confidence(self):
        # Vague prompt
        prompt = "The system is weird."
        meta = classify_prompt([{"role": "user", "content": prompt}])
        
        # Confidence should be low
        assert meta.confidence < 0.6
