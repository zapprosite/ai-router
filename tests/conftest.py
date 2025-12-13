"""
Pytest fixtures for AI Router tests.
Provides TestClient with mocked API Key for security testing.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fixed test API key
TEST_API_KEY = "test_secret_key_12345"


@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    """Set environment variables for testing."""
    os.environ["AI_ROUTER_API_KEY"] = TEST_API_KEY
    os.environ["OPENAI_API_KEY"] = "sk-test-mock"
    os.environ["ENABLE_OPENAI_FALLBACK"] = "1"
    yield
    # Cleanup not strictly necessary for tests


@pytest.fixture
def client():
    """Create a TestClient with the app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def wrong_auth_headers():
    """Headers with invalid API key."""
    return {"X-API-Key": "wrong_key_12345"}
