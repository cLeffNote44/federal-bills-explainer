"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from typing import Generator


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up test environment variables.
    Runs once per test session.
    """
    # Save original environment
    original_env = os.environ.copy()

    # Set test environment variables
    test_env = {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test_fbx",
        "CONGRESS_API_KEY": "test-api-key-" + "x" * 32,
        "JWT_SECRET_KEY": "test-jwt-secret-" + "x" * 32,
        "ADMIN_TOKEN": "test-admin-token-" + "x" * 32,
        "REDIS_URL": "redis://localhost:6379/1",  # Use DB 1 for tests
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "WARNING",  # Reduce noise in tests
        "DRY_RUN": "true",
        "EMBEDDINGS_ENABLED": "false",
        "EXPLANATIONS_ENABLED": "false",
        "CORS_ORIGINS": "http://localhost:3000",
        "MAX_REQUEST_SIZE": "1048576",  # 1MB
        "SESSION_TIMEOUT": "3600",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Fixture that provides a clean environment for testing.
    Use this when you need to test with specific environment variables.
    """
    # Clear all environment variables for this test
    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    yield monkeypatch


@pytest.fixture
def mock_redis():
    """
    Mock Redis client for testing.
    """
    from unittest.mock import AsyncMock

    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=0)
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.close = AsyncMock()

    return redis_mock


@pytest.fixture
async def test_cache_service(mock_redis):
    """
    Provide a test cache service with mocked Redis.
    """
    from fbx_core.cache import CacheService

    cache = CacheService(redis_url="redis://localhost:6379/1")
    cache.redis = mock_redis
    cache.enabled = True

    yield cache

    await cache.close()


@pytest.fixture
def sample_bill_data():
    """
    Sample bill data for testing.
    """
    return {
        "congress": 118,
        "bill_type": "hr",
        "number": 1234,
        "title": "Test Bill Title",
        "summary": "This is a test bill summary.",
        "status": "introduced",
        "introduced_date": "2025-01-01",
        "sponsor": "Rep. Test Sponsor",
        "cosponsors_count": 5,
    }


@pytest.fixture
def sample_jwt_token():
    """
    Generate a sample JWT token for testing.
    """
    import os
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-long"

    from fbx_core.auth import create_access_token

    return create_access_token(
        data={"sub": "testuser@example.com", "scopes": ["read", "write"]}
    )


@pytest.fixture
def sample_admin_token():
    """
    Generate a sample admin token for testing.
    """
    return "test-admin-token-" + "x" * 32


@pytest.fixture
def test_app():
    """
    Create a test FastAPI application.
    """
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    @app.post("/test")
    async def test_post_endpoint(data: dict):
        return {"received": data}

    return app


@pytest.fixture
def test_client(test_app):
    """
    Create a test client for the FastAPI application.
    """
    from fastapi.testclient import TestClient

    return TestClient(test_app)


# Markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )


# Custom assertions
def assert_valid_jwt_token(token: str):
    """Assert that a string is a valid JWT token format."""
    parts = token.split(".")
    assert len(parts) == 3, "JWT token should have 3 parts"
    assert all(len(part) > 0 for part in parts), "JWT parts should not be empty"


def assert_rate_limit_headers(headers: dict):
    """Assert that rate limit headers are present and valid."""
    required_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ]

    for header in required_headers:
        assert header in headers, f"Missing header: {header}"
        assert int(headers[header]) >= 0, f"Invalid value for {header}"


def assert_security_headers(headers: dict):
    """Assert that security headers are present."""
    required_headers = [
        "Content-Security-Policy",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
    ]

    for header in required_headers:
        assert header in headers, f"Missing security header: {header}"


# Helper functions
def create_mock_request(
    method: str = "GET",
    path: str = "/test",
    headers: dict = None,
    body: bytes = b""
):
    """Create a mock request object for testing."""
    from unittest.mock import Mock
    from starlette.datastructures import Headers

    request = Mock()
    request.method = method
    request.url.path = path
    request.headers = Headers(headers or {})
    request.body = Mock(return_value=body)

    return request


# Async test utilities
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures (for integration tests)
@pytest.fixture
async def test_db_session():
    """
    Create a test database session.
    Note: Requires database to be running.
    """
    # This would typically use SQLAlchemy's test utilities
    # For now, it's a placeholder
    yield None


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_cache():
    """Clean up cache after each test."""
    yield
    # Cleanup code here if needed
    pass
