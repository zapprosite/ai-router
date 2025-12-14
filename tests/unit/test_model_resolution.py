"""
Unit Tests for Model Resolution & Params
Verifies the Router correctly resolves aliases to real IDs and injects parameters.
"""
from unittest.mock import patch

from graph.router import REG, _build_chain


def test_resolve_gpt_high_alias():
    """Verify gpt-5.2-high resolves to gpt-4o + reasoning_effort: high"""
    # Force cloud available to enable validation path (which we mock)
    with patch("graph.router._is_cloud_available", return_value=True):
        # Mock validation to return True
        with patch("graph.router.validate_openai_id", return_value=True) as mock_val:
            # Mock make_openai to inspect arguments
            with patch("graph.router.make_openai") as mock_make:
                # Force rebuild since _build_chain caches? 
                # No, _build_chain builds a NEW chain. _get_chain caches.
                # We call _build_chain directly.
                
                _build_chain("gpt-5.2-high")
                
                # Check validation called with REAL ID
                mock_val.assert_called_with("gpt-4o")
                
                # Check make_openai called with REAL ID and PARAMS
                mock_make.assert_called_once()
                args, kwargs = mock_make.call_args
                assert args[0] == "gpt-4o"
                assert kwargs["params"] == {"reasoning_effort": "high"}

def test_resolve_codex_mini_alias():
    """Verify gpt-5.2-codex-mini resolves to gpt-4o-mini + reasoning_effort: low"""
    with patch("graph.router._is_cloud_available", return_value=True):
        with patch("graph.router.validate_openai_id", return_value=True) as mock_val:
            with patch("graph.router.make_openai") as mock_make:
                _build_chain("gpt-5.2-codex-mini")
                
                mock_val.assert_called_with("gpt-4o-mini")
                mock_make.assert_called_once()
                args, kwargs = mock_make.call_args
                assert args[0] == "gpt-4o-mini"
                assert kwargs["params"] == {"reasoning_effort": "low"}

def test_validation_failure_fallback():
    """Verify fallback to local-code if validation fails"""
    with patch("graph.router._is_cloud_available", return_value=True):
        # Validation FAILS
        with patch("graph.router.validate_openai_id", return_value=False) as mock_val:
            # We also need to spy on _build_chain recursion, or check the result.
            # _build_chain("local-code") returns an Ollama chain.
            
            # We'll just check that it calls _build_chain logic recursively or returns ollama
            # For simplicity, let's mock _build_chain("local-code") separate call?
            # Actually easier to check consistent return type if we mock make_ollama
            
            with patch("graph.router.make_ollama") as mock_ollama:
                _build_chain("gpt-5.2-high")
                
                # Should have tried to validate gpt-4o
                mock_val.assert_called_with("gpt-4o")
                
                # Should have CALLED make_ollama (fallback)
                # Ensure local-code maps to deepseek-coder-v2:16b (from config)
                expected_local_name = REG["local-code"]["name"]
                mock_ollama.assert_called()
                args, _ = mock_ollama.call_args
                assert args[0] == expected_local_name
