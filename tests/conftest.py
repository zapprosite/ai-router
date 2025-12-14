import os

import pytest
from fastapi.testclient import TestClient

# Fixed test API key for consistent auth testing
TEST_API_KEY = "test_secret_key_12345"


@pytest.fixture(scope="session", autouse=True)
def setup_global_env():
    """
    Set baseline environment variables for the entire test session.
    Used to prevent accidental production connectivity.
    """
    # Enforce testing mode
    os.environ["AI_ROUTER_ENV"] = "test"
    # Basic auth key
    os.environ["AI_ROUTER_API_KEY"] = TEST_API_KEY


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    """
    Ensure every test runs with a clean/known environment.
    Automatically used for all tests.
    
    IMPORTANT: Resets OpenAI auth cache to prevent test pollution from
    cached 401 responses that would disable cloud validation for all 
    subsequent tests.
    """
    # Reset OpenAI auth cache BEFORE each test
    try:
        from providers.openai_client import _OPENAI_AUTH_STATUS
        _OPENAI_AUTH_STATUS["validated"] = False
        _OPENAI_AUTH_STATUS["available"] = False
        _OPENAI_AUTH_STATUS["checked_at"] = 0
    except ImportError:
        pass  # Module not yet loaded
    
    monkeypatch.setenv("AI_ROUTER_API_KEY", TEST_API_KEY)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-mock-key")
    monkeypatch.setenv("ENABLE_OPENAI_FALLBACK", "1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    yield  # Run test
    
    # Cleanup: Reset cache again after test
    try:
        from providers.openai_client import _OPENAI_AUTH_STATUS
        _OPENAI_AUTH_STATUS["validated"] = False
        _OPENAI_AUTH_STATUS["available"] = False
        _OPENAI_AUTH_STATUS["checked_at"] = 0
    except ImportError:
        pass


@pytest.fixture
def client():
    """
    Create a TestClient with the FastAPI app.
    Lazy import ensures app is initialized with test env vars.
    Uses context manager pattern for proper cleanup.
    """
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    """Return headers with a valid API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def wrong_auth_headers():
    """Return headers with an invalid API key."""
    return {"X-API-Key": "invalid-key-attempt"}
