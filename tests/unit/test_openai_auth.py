"""
Test OpenAI Authentication and Validation Logic
"""
from unittest.mock import Mock, patch

import httpx
import pytest


@pytest.fixture
def mock_env_with_key(monkeypatch):
    """Set up environment with valid OpenAI key"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


@pytest.fixture
def mock_env_no_key(monkeypatch):
    """Set up environment without OpenAI key (local-only mode)"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_TIER2", raising=False)


@pytest.fixture(autouse=True)
def reset_auth_cache():
    """Reset global auth cache before each test"""
    from providers.openai_client import _OPENAI_AUTH_STATUS
    _OPENAI_AUTH_STATUS["validated"] = False
    _OPENAI_AUTH_STATUS["available"] = False
    _OPENAI_AUTH_STATUS["checked_at"] = 0
    yield


class TestOpenAIAuthentication:
    """Test OpenAI authentication and validation logic"""

    def test_no_api_key_returns_true(self, mock_env_no_key):
        """When no API key is configured, validation should return True (local-only mode)"""
        from providers.openai_client import validate_model_id
        
        result = validate_model_id("gpt-4o")
        assert result is True

    def test_valid_auth_success(self, mock_env_with_key):
        """When auth is valid (200), should cache success and validate model"""
        from providers.openai_client import _OPENAI_AUTH_STATUS, validate_model_id
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4o"},
                {"id": "gpt-4o-mini"},
                {"id": "o3"},
            ]
        }
        
        with patch("httpx.get", return_value=mock_response):
            result = validate_model_id("gpt-4o")
        
        assert result is True
        assert _OPENAI_AUTH_STATUS["validated"] is True
        assert _OPENAI_AUTH_STATUS["available"] is True

    def test_valid_auth_model_not_found(self, mock_env_with_key):
        """When auth is valid but model doesn't exist, should return False"""
        from providers.openai_client import validate_model_id
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4o"},
                {"id": "gpt-4o-mini"},
            ]
        }
        
        with patch("httpx.get", return_value=mock_response):
            result = validate_model_id("nonexistent-model")
        
        assert result is False

    def test_401_unauthorized_disables_cloud(self, mock_env_with_key):
        """When auth fails (401), should cache failure and disable cloud validation"""
        from providers.openai_client import _OPENAI_AUTH_STATUS, validate_model_id
        
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch("httpx.get", return_value=mock_response):
            result = validate_model_id("gpt-4o")
        
        assert result is False
        assert _OPENAI_AUTH_STATUS["validated"] is True
        assert _OPENAI_AUTH_STATUS["available"] is False

    def test_401_cached_prevents_spam(self, mock_env_with_key):
        """After 401, subsequent validations should use cache (no repeated API calls)"""
        from providers.openai_client import validate_model_id
        
        # First call: 401
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        
        with patch("httpx.get", return_value=mock_response_401) as mock_get:
            result1 = validate_model_id("gpt-4o")
            assert result1 is False
            assert mock_get.call_count == 1
        
        # Second call: should use cache, no API call
        with patch("httpx.get", return_value=mock_response_401) as mock_get:
            result2 = validate_model_id("gpt-4o-mini")
            assert result2 is False
            assert mock_get.call_count == 0  # No API call made

    def test_timeout_returns_false(self, mock_env_with_key):
        """When request times out, should return False without crashing"""
        from providers.openai_client import validate_model_id
        
        with patch("httpx.get", side_effect=httpx.TimeoutException("Timeout")):
            result = validate_model_id("gpt-4o")
        
        assert result is False

    def test_network_error_returns_false(self, mock_env_with_key):
        """When network error occurs, should return False without crashing"""
        from providers.openai_client import validate_model_id
        
        with patch("httpx.get", side_effect=httpx.RequestError("Network error")):
            result = validate_model_id("gpt-4o")
        
        assert result is False

    def test_429_rate_limit_returns_false(self, mock_env_with_key):
        """When rate limited (429), should return False"""
        from providers.openai_client import validate_model_id
        
        mock_response = Mock()
        mock_response.status_code = 429
        
        with patch("httpx.get", return_value=mock_response):
            result = validate_model_id("gpt-4o")
        
        assert result is False

    def test_auth_with_org_and_project(self, mock_env_with_key, monkeypatch):
        """When org/project are set, should include them in headers"""
        monkeypatch.setenv("OPENAI_ORGANIZATION", "org-test")
        monkeypatch.setenv("OPENAI_PROJECT", "proj-test")
        
        from providers.openai_client import validate_model_id
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o"}]}
        
        with patch("httpx.get", return_value=mock_response) as mock_get:
            validate_model_id("gpt-4o")
            
            # Verify headers include org and project
            call_kwargs = mock_get.call_args[1]
            headers = call_kwargs["headers"]
            assert "OpenAI-Organization" in headers
            assert headers["OpenAI-Organization"] == "org-test"
            assert "OpenAI-Project" in headers
            assert headers["OpenAI-Project"] == "proj-test"


class TestIsCloudEnabled:
    """Test is_cloud_enabled() helper function"""

    def test_returns_true_when_not_validated(self):
        """Before any validation, should return True (optimistic)"""
        from providers.openai_client import _OPENAI_AUTH_STATUS, is_cloud_enabled
        
        _OPENAI_AUTH_STATUS["validated"] = False
        _OPENAI_AUTH_STATUS["available"] = False
        
        assert is_cloud_enabled() is True

    def test_returns_true_when_auth_succeeded(self):
        """After successful auth, should return True"""
        import time
        
        from providers.openai_client import _OPENAI_AUTH_STATUS, is_cloud_enabled
        
        _OPENAI_AUTH_STATUS["validated"] = True
        _OPENAI_AUTH_STATUS["available"] = True
        _OPENAI_AUTH_STATUS["checked_at"] = time.time()
        
        assert is_cloud_enabled() is True

    def test_returns_false_when_auth_failed(self):
        """After 401, should return False"""
        import time
        
        from providers.openai_client import _OPENAI_AUTH_STATUS, is_cloud_enabled
        
        _OPENAI_AUTH_STATUS["validated"] = True
        _OPENAI_AUTH_STATUS["available"] = False
        _OPENAI_AUTH_STATUS["checked_at"] = time.time()
        
        assert is_cloud_enabled() is False

    def test_cache_expires_after_5_minutes(self):
        """After 5 minutes, cache should expire and return True"""
        import time
        
        from providers.openai_client import _OPENAI_AUTH_STATUS, is_cloud_enabled
        
        # Set cache to 6 minutes ago (expired)
        _OPENAI_AUTH_STATUS["validated"] = True
        _OPENAI_AUTH_STATUS["available"] = False
        _OPENAI_AUTH_STATUS["checked_at"] = time.time() - 360  # 6 minutes ago
        
        # Should return True because cache expired
        assert is_cloud_enabled() is True
        # Should also reset validated flag
        assert _OPENAI_AUTH_STATUS["validated"] is False
