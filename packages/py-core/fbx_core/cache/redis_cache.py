"""
Redis caching service for Federal Bills Explainer.

Provides caching for API responses, database queries, and computed results.
"""

import json
import logging
import hashlib
from typing import Optional, Any, Callable
from datetime import timedelta
from functools import wraps

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = Any  # Type hint fallback

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service with fallback to no-op if Redis unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.enabled = bool(redis_url and REDIS_AVAILABLE)

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Caching disabled.")
        elif not redis_url:
            logger.info("Redis URL not provided. Caching disabled.")

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.enabled:
            return

        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            # Test connection
            await self.redis.ping()
            logger.info(f"✓ Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.redis = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis:
            return False

        try:
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.redis:
            return False

        try:
            result = await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if exists, False otherwise
        """
        if not self.enabled or not self.redis:
            return False

        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "bills:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for '{pattern}': {e}")
            return 0

    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized JSON value or None
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key '{key}': {e}")
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON value in cache.

        Args:
            key: Cache key
            value: Value to serialize and cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key '{key}': {e}")
            return False

    @staticmethod
    def make_key(*parts: Any) -> str:
        """
        Create cache key from parts.

        Args:
            *parts: Key parts to join

        Returns:
            Cache key string
        """
        return ":".join(str(part) for part in parts)

    @staticmethod
    def hash_key(value: str) -> str:
        """
        Create hash of value for use as cache key.

        Args:
            value: Value to hash

        Returns:
            MD5 hash hex string
        """
        return hashlib.md5(value.encode()).hexdigest()


def cached(
    ttl: int = 300,
    key_prefix: str = "cache",
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
        key_builder: Optional function to build cache key from args

    Returns:
        Decorated function with caching

    Example:
        @cached(ttl=600, key_prefix="bills")
        async def get_bill(congress: int, bill_type: str, number: int):
            # Expensive operation
            return bill_data
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache service (assumes it's passed or available)
            cache = kwargs.get('cache')  # or inject via dependency

            if not cache or not cache.enabled:
                # No cache available, execute function
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: use function name and args
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = CacheService.make_key(*key_parts)

            # Try to get from cache
            cached_result = await cache.get_json(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_result

            # Execute function
            logger.debug(f"Cache MISS for {func.__name__}, executing...")
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set_json(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# Global cache instance (initialized in app startup)
cache_service: Optional[CacheService] = None


def get_cache() -> Optional[CacheService]:
    """
    Get global cache service instance.

    Returns:
        CacheService instance or None
    """
    return cache_service


async def init_cache(redis_url: Optional[str]) -> CacheService:
    """
    Initialize global cache service.

    Args:
        redis_url: Redis connection URL

    Returns:
        Initialized CacheService instance
    """
    global cache_service
    cache_service = CacheService(redis_url)
    await cache_service.connect()
    return cache_service


async def shutdown_cache() -> None:
    """Shutdown global cache service."""
    global cache_service
    if cache_service:
        await cache_service.close()
        cache_service = None
