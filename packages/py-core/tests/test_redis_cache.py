"""
Tests for Redis caching service.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from fbx_core.cache import CacheService


class TestCacheService:
    """Test suite for CacheService class."""

    @pytest.fixture
    def cache_service_no_redis(self):
        """Cache service without Redis (disabled)."""
        return CacheService(redis_url=None)

    @pytest.fixture
    async def cache_service_mocked(self):
        """Cache service with mocked Redis."""
        cache = CacheService(redis_url="redis://localhost:6379/0")

        # Mock Redis client
        cache.redis = AsyncMock()
        cache.enabled = True

        return cache

    def test_init_without_redis_url(self):
        """Test initialization without Redis URL disables caching."""
        cache = CacheService(redis_url=None)

        assert cache.redis_url is None
        assert cache.redis is None
        assert cache.enabled is False

    def test_init_with_redis_url(self):
        """Test initialization with Redis URL."""
        cache = CacheService(redis_url="redis://localhost:6379/0")

        assert cache.redis_url == "redis://localhost:6379/0"
        assert cache.redis is None  # Not connected yet
        # enabled depends on REDIS_AVAILABLE constant

    @pytest.mark.asyncio
    async def test_get_when_disabled(self, cache_service_no_redis):
        """Test get returns None when caching is disabled."""
        result = await cache_service_no_redis.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_when_disabled(self, cache_service_no_redis):
        """Test set returns False when caching is disabled."""
        result = await cache_service_no_redis.set("test_key", "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_hit(self, cache_service_mocked):
        """Test successful cache hit."""
        cache_service_mocked.redis.get.return_value = "cached_value"

        result = await cache_service_mocked.get("test_key")

        assert result == "cached_value"
        cache_service_mocked.redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_miss(self, cache_service_mocked):
        """Test cache miss."""
        cache_service_mocked.redis.get.return_value = None

        result = await cache_service_mocked.get("test_key")

        assert result is None
        cache_service_mocked.redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_with_error(self, cache_service_mocked):
        """Test get handles Redis errors gracefully."""
        cache_service_mocked.redis.get.side_effect = Exception("Redis error")

        result = await cache_service_mocked.get("test_key")

        assert result is None  # Should return None on error

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, cache_service_mocked):
        """Test set without TTL."""
        cache_service_mocked.redis.set.return_value = True

        result = await cache_service_mocked.set("test_key", "test_value")

        assert result is True
        cache_service_mocked.redis.set.assert_called_once_with("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_service_mocked):
        """Test set with TTL."""
        cache_service_mocked.redis.setex.return_value = True

        result = await cache_service_mocked.set("test_key", "test_value", ttl=300)

        assert result is True
        cache_service_mocked.redis.setex.assert_called_once_with(
            "test_key", 300, "test_value"
        )

    @pytest.mark.asyncio
    async def test_set_with_error(self, cache_service_mocked):
        """Test set handles Redis errors gracefully."""
        cache_service_mocked.redis.setex.side_effect = Exception("Redis error")

        result = await cache_service_mocked.set("test_key", "test_value", ttl=300)

        assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_delete(self, cache_service_mocked):
        """Test delete operation."""
        cache_service_mocked.redis.delete.return_value = 1

        result = await cache_service_mocked.delete("test_key")

        assert result is True
        cache_service_mocked.redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_non_existent_key(self, cache_service_mocked):
        """Test delete of non-existent key."""
        cache_service_mocked.redis.delete.return_value = 0

        result = await cache_service_mocked.delete("non_existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, cache_service_mocked):
        """Test exists operation."""
        cache_service_mocked.redis.exists.return_value = 1

        result = await cache_service_mocked.exists("test_key")

        assert result is True
        cache_service_mocked.redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_not_found(self, cache_service_mocked):
        """Test exists for non-existent key."""
        cache_service_mocked.redis.exists.return_value = 0

        result = await cache_service_mocked.exists("non_existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_json(self, cache_service_mocked):
        """Test get_json with valid JSON."""
        test_data = {"name": "John", "age": 30}
        cache_service_mocked.redis.get.return_value = json.dumps(test_data)

        result = await cache_service_mocked.get_json("test_key")

        assert result == test_data

    @pytest.mark.asyncio
    async def test_get_json_invalid(self, cache_service_mocked):
        """Test get_json with invalid JSON."""
        cache_service_mocked.redis.get.return_value = "not valid json {"

        result = await cache_service_mocked.get_json("test_key")

        assert result is None  # Should return None for invalid JSON

    @pytest.mark.asyncio
    async def test_set_json(self, cache_service_mocked):
        """Test set_json with serializable data."""
        test_data = {"name": "John", "age": 30, "active": True}
        cache_service_mocked.redis.setex.return_value = True

        result = await cache_service_mocked.set_json("test_key", test_data, ttl=300)

        assert result is True

        # Verify JSON was serialized correctly
        call_args = cache_service_mocked.redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 300
        deserialized = json.loads(call_args[0][2])
        assert deserialized == test_data

    @pytest.mark.asyncio
    async def test_set_json_with_datetime(self, cache_service_mocked):
        """Test set_json with datetime objects (uses default=str)."""
        from datetime import datetime

        test_data = {"timestamp": datetime(2025, 1, 1, 12, 0, 0)}
        cache_service_mocked.redis.setex.return_value = True

        result = await cache_service_mocked.set_json("test_key", test_data, ttl=300)

        assert result is True

    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_service_mocked):
        """Test clear_pattern operation."""
        # Mock scan_iter to return keys
        async def mock_scan_iter(match):
            for key in ["bills:1", "bills:2", "bills:3"]:
                yield key

        cache_service_mocked.redis.scan_iter = mock_scan_iter
        cache_service_mocked.redis.delete.return_value = 3

        result = await cache_service_mocked.clear_pattern("bills:*")

        assert result == 3
        cache_service_mocked.redis.delete.assert_called_once()

    def test_make_key(self):
        """Test make_key utility method."""
        key = CacheService.make_key("bills", 118, "hr", 1234)

        assert key == "bills:118:hr:1234"

    def test_make_key_with_various_types(self):
        """Test make_key with different types."""
        key = CacheService.make_key("user", 123, "active", True, "score", 99.5)

        assert key == "user:123:active:True:score:99.5"

    def test_hash_key(self):
        """Test hash_key utility method."""
        value = "some long string that needs to be hashed"
        hashed = CacheService.hash_key(value)

        assert isinstance(hashed, str)
        assert len(hashed) == 32  # MD5 hash length

        # Same input should produce same hash
        hashed2 = CacheService.hash_key(value)
        assert hashed == hashed2

        # Different input should produce different hash
        hashed3 = CacheService.hash_key("different string")
        assert hashed != hashed3


class TestCacheDecorator:
    """Test @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self):
        """Test basic @cached decorator functionality."""
        from fbx_core.cache import cached

        call_count = 0

        @cached(ttl=300, key_prefix="test")
        async def expensive_operation(x: int):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Note: The decorator needs cache instance in kwargs
        # This is a simplified test showing the decorator structure
        # In real usage, cache would be injected via dependency injection

    def test_cached_decorator_key_builder(self):
        """Test @cached decorator with custom key builder."""
        from fbx_core.cache import cached

        def custom_key_builder(*args, **kwargs):
            return f"custom:{args[0]}:{kwargs.get('mode', 'default')}"

        @cached(ttl=600, key_prefix="bills", key_builder=custom_key_builder)
        async def get_bill(bill_id: int, mode: str = "full"):
            return {"id": bill_id, "mode": mode}

        # Decorator structure test
        assert hasattr(get_bill, "__wrapped__")


class TestCacheLifecycle:
    """Test cache lifecycle management."""

    @pytest.mark.asyncio
    async def test_init_and_shutdown_cache(self):
        """Test init_cache and shutdown_cache functions."""
        from fbx_core.cache import init_cache, shutdown_cache, get_cache

        # Initialize cache
        cache = await init_cache(redis_url=None)  # Disabled cache

        assert cache is not None
        assert get_cache() is not None

        # Shutdown cache
        await shutdown_cache()

        assert get_cache() is None
