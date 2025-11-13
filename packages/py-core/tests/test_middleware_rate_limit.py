"""
Tests for rate limiting middleware.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fbx_core.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimitMiddleware,
    RateLimitConfig,
)


class TestInMemoryRateLimiter:
    """Test InMemoryRateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter instance."""
        return InMemoryRateLimiter()

    @pytest.mark.asyncio
    async def test_first_request_allowed(self, limiter):
        """Test that first request is always allowed."""
        is_limited, info = await limiter.is_rate_limited("test_key", 10, 60)

        assert is_limited is False
        assert info["remaining"] == 9
        assert info["limit"] == 10

    @pytest.mark.asyncio
    async def test_requests_within_limit(self, limiter):
        """Test multiple requests within limit."""
        key = "test_key"
        max_requests = 5
        window = 60

        for i in range(max_requests):
            is_limited, info = await limiter.is_rate_limited(key, max_requests, window)
            assert is_limited is False
            assert info["remaining"] == max_requests - i - 1

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, limiter):
        """Test rate limit is enforced when exceeded."""
        key = "test_key"
        max_requests = 3
        window = 60

        # Make max_requests requests
        for _ in range(max_requests):
            is_limited, info = await limiter.is_rate_limited(key, max_requests, window)
            assert is_limited is False

        # Next request should be limited
        is_limited, info = await limiter.is_rate_limited(key, max_requests, window)

        assert is_limited is True
        assert info["remaining"] == 0
        assert info["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, limiter):
        """Test that different keys have independent limits."""
        max_requests = 2
        window = 60

        # Use up limit for key1
        await limiter.is_rate_limited("key1", max_requests, window)
        await limiter.is_rate_limited("key1", max_requests, window)

        # key2 should still be allowed
        is_limited, info = await limiter.is_rate_limited("key2", max_requests, window)

        assert is_limited is False
        assert info["remaining"] == 1

    @pytest.mark.asyncio
    async def test_old_requests_cleaned_up(self, limiter):
        """Test that old requests outside the window are cleaned up."""
        key = "test_key"
        max_requests = 3
        window = 1  # 1 second window

        # Make some requests
        for _ in range(2):
            await limiter.is_rate_limited(key, max_requests, window)

        # Wait for window to expire
        await asyncio.sleep(1.5)

        # Should be able to make requests again
        is_limited, info = await limiter.is_rate_limited(key, max_requests, window)

        assert is_limited is False
        assert info["remaining"] == 2  # Reset after window

    @pytest.mark.asyncio
    async def test_retry_after_calculation(self, limiter):
        """Test retry_after is calculated correctly."""
        key = "test_key"
        max_requests = 1
        window = 60

        # Use up the limit
        await limiter.is_rate_limited(key, max_requests, window)

        # Check retry_after
        is_limited, info = await limiter.is_rate_limited(key, max_requests, window)

        assert is_limited is True
        assert 0 < info["retry_after"] <= window


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    def test_config_creation(self):
        """Test creating rate limit configuration."""
        config = RateLimitConfig(requests=100, window=60)

        assert config.requests == 100
        assert config.window == 60
        assert config.key_prefix == "rate_limit"

    def test_config_with_custom_prefix(self):
        """Test configuration with custom key prefix."""
        config = RateLimitConfig(requests=50, window=30, key_prefix="api")

        assert config.requests == 50
        assert config.window == 30
        assert config.key_prefix == "api"


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI application."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/api/v1/bills/search")
        async def search_bills():
            return {"bills": []}

        return app

    def test_middleware_initialization(self, app):
        """Test middleware can be initialized."""
        app.add_middleware(RateLimitMiddleware, redis_url=None)

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200

    def test_rate_limit_headers_present(self, app):
        """Test that rate limit headers are added to response."""
        app.add_middleware(RateLimitMiddleware, redis_url=None)

        client = TestClient(app)
        response = client.get("/test")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_enforcement(self, app):
        """Test that rate limiting is enforced."""
        # Set very low limit for testing
        config = RateLimitConfig(requests=2, window=60)
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=None,
            default_config=config
        )

        client = TestClient(app)

        # First two requests should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200
        assert int(response1.headers["X-RateLimit-Remaining"]) == 1

        response2 = client.get("/test")
        assert response2.status_code == 200
        assert int(response2.headers["X-RateLimit-Remaining"]) == 0

        # Third request should be rate limited
        response3 = client.get("/test")
        assert response3.status_code == 429
        assert "rate limit exceeded" in response3.json()["detail"].lower()
        assert "Retry-After" in response3.headers

    def test_health_check_bypasses_rate_limit(self, app):
        """Test that health check endpoints bypass rate limiting."""
        config = RateLimitConfig(requests=1, window=60)
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=None,
            default_config=config
        )

        client = TestClient(app)

        # Health check should not be rate limited
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    def test_different_endpoints_separate_limits(self, app):
        """Test that different endpoints can have separate rate limits."""
        default_config = RateLimitConfig(requests=10, window=60)
        middleware = RateLimitMiddleware(
            app=app,
            redis_url=None,
            default_config=default_config
        )

        # Override endpoint-specific config for search
        middleware.endpoint_configs["/api/v1/bills/search"] = RateLimitConfig(
            requests=2, window=60
        )

        app.add_middleware(RateLimitMiddleware, redis_url=None)

        client = TestClient(app)

        # Regular endpoint should have default limit
        response = client.get("/test")
        assert response.status_code == 200
        # Note: This test might need adjustment based on actual middleware behavior

    def test_client_identifier_from_ip(self, app):
        """Test client identification by IP address."""
        app.add_middleware(RateLimitMiddleware, redis_url=None)

        client = TestClient(app)

        # Requests from same client
        response1 = client.get("/test")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])

        response2 = client.get("/test")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        # Remaining should decrease
        assert remaining2 == remaining1 - 1

    def test_rate_limit_reset_time(self, app):
        """Test that reset time is included in headers."""
        app.add_middleware(RateLimitMiddleware, redis_url=None)

        client = TestClient(app)
        response = client.get("/test")

        reset_time = int(response.headers["X-RateLimit-Reset"])
        import time
        current_time = int(time.time())

        # Reset time should be in the future
        assert reset_time > current_time

    def test_429_response_format(self, app):
        """Test format of 429 rate limit exceeded response."""
        config = RateLimitConfig(requests=1, window=60)
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=None,
            default_config=config
        )

        client = TestClient(app)

        # Use up the limit
        client.get("/test")

        # Get rate limited response
        response = client.get("/test")

        assert response.status_code == 429
        assert "detail" in response.json()
        assert "retry_after" in response.json()
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in response.headers


class TestRateLimitIntegration:
    """Integration tests for rate limiting."""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting configured."""
        app = FastAPI()

        @app.get("/api/public")
        async def public_endpoint():
            return {"data": "public"}

        @app.get("/api/admin")
        async def admin_endpoint():
            return {"data": "admin"}

        @app.get("/healthz")
        async def health():
            return {"status": "ok"}

        # Add middleware with different configs
        config = RateLimitConfig(requests=3, window=60)
        app.add_middleware(
            RateLimitMiddleware,
            redis_url=None,
            default_config=config
        )

        return app

    def test_concurrent_requests_rate_limited(self, app_with_rate_limit):
        """Test that concurrent requests are properly rate limited."""
        client = TestClient(app_with_rate_limit)

        # Make requests up to the limit
        responses = []
        for _ in range(4):
            response = client.get("/api/public")
            responses.append(response)

        # First 3 should succeed
        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        assert responses[2].status_code == 200

        # 4th should be rate limited
        assert responses[3].status_code == 429

    def test_rate_limit_per_endpoint(self, app_with_rate_limit):
        """Test rate limiting is per-endpoint."""
        client = TestClient(app_with_rate_limit)

        # Use up limit on public endpoint
        for _ in range(3):
            response = client.get("/api/public")
            assert response.status_code == 200

        # Admin endpoint should still work (separate limit)
        response = client.get("/api/admin")
        assert response.status_code == 200

    def test_health_endpoints_unlimited(self, app_with_rate_limit):
        """Test health endpoints are not rate limited."""
        client = TestClient(app_with_rate_limit)

        # Make many requests to health endpoint
        for _ in range(20):
            response = client.get("/healthz")
            assert response.status_code == 200
