"""
Test: Model ID Validation

Ensures the router only uses known, valid model IDs and that
'high/mini' effort levels are represented as parameters, not ID suffixes.
"""

import os
import sys

# Ensure test environment
os.environ["AI_ROUTER_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-mock"
os.environ["ENABLE_OPENAI_FALLBACK"] = "1"

sys.path.insert(0, os.getcwd())

from graph.router import REG, classify_prompt, select_model_from_policy

# Known REAL model IDs that can be sent to OpenAI API
KNOWN_OPENAI_IDS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o1",
    "o3",
    "o3-mini",
    # Local models (Ollama) - not sent to OpenAI
    "hermes3:8b",
    "deepseek-coder-v2:16b",
}


class TestModelValidation:
    """Tests that ensure no invented model IDs are used."""

    def test_all_openai_models_use_real_ids(self):
        """Verify that all OpenAI models in config use real provider IDs."""
        for model_id, model_cfg in REG.items():
            if model_cfg.get("provider") == "openai":
                real_name = model_cfg.get("name")
                assert real_name in KNOWN_OPENAI_IDS, (
                    f"Model '{model_id}' uses unknown OpenAI ID '{real_name}'. "
                    f"Known IDs: {KNOWN_OPENAI_IDS}"
                )

    def test_effort_is_param_not_id(self):
        """Verify that 'high/mini' effort is in params, not the model name."""
        for model_id, model_cfg in REG.items():
            if model_cfg.get("provider") == "openai":
                real_name = model_cfg.get("name", "")
                # The real name should NOT contain 'high' or 'codex-mini' as suffix
                assert "codex-mini" not in real_name.lower(), (
                    f"Model '{model_id}' has 'codex-mini' in name '{real_name}'. "
                    "Use params.reasoning_effort instead."
                )
                assert "codex-high" not in real_name.lower(), (
                    f"Model '{model_id}' has 'codex-high' in name '{real_name}'. "
                    "Use params.reasoning_effort instead."
                )

    def test_gpt52_aliases_have_params(self):
        """Verify that GPT-5.2 aliases have reasoning_effort params."""
        gpt52_aliases = ["gpt-5.2-high", "gpt-5.2-codex-mini", "gpt-5.2-codex-high"]
        
        for alias in gpt52_aliases:
            if alias in REG:
                model_cfg = REG[alias]
                params = model_cfg.get("params", {})
                assert "reasoning_effort" in params, (
                    f"Model '{alias}' should have params.reasoning_effort defined."
                )

    def test_routing_returns_known_model(self):
        """Verify routing logic returns models that exist in registry."""
        test_cases = [
            ("Hello, how are you?", "local-chat"),
            ("Write a Python function.", "local-code"),
            ("Prove sqrt(2) is irrational.", "o3"),
        ]
        
        for prompt, expected_prefix in test_cases:
            meta = classify_prompt([{"role": "user", "content": prompt}])
            selected = select_model_from_policy(meta)
            assert selected in REG, f"Selected model '{selected}' not in registry."


class TestCloudGating:
    """Tests for cloud fallback gating."""

    def test_cloud_blocked_when_disabled(self, monkeypatch):
        """Verify cloud models are blocked when ENABLE_OPENAI_FALLBACK=0."""
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "0")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        from graph.router import _is_cloud_available
        assert not _is_cloud_available(), "Cloud should be blocked when disabled."

    def test_cloud_allowed_with_key(self, monkeypatch):
        """Verify cloud is allowed when key exists and fallback enabled."""
        monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        
        from graph.router import _is_cloud_available
        assert _is_cloud_available(), "Cloud should be allowed with valid key."
