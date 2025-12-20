"""
Rate limiting middleware for API endpoints.

Uses Redis for distributed rate limiting or in-memory for development.
"""

import time
import logging
from typing import Optional, Callable
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    key_prefix: str = "rate_limit"


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using token bucket algorithm.
    Use only for development - not distributed.
    """

    def __init__(self):
        self.requests = defaultdict(list)

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if the key is rate limited.

        Returns:
            Tuple of (is_limited, info_dict)
        """
        now = time.time()
        cutoff = now - window

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]

        current_count = len(self.requests[key])

        if current_count >= max_requests:
            oldest_request = min(self.requests[key]) if self.requests[key] else now
            retry_after = int(oldest_request + window - now) + 1

            return True, {
                "limit": max_requests,
                "remaining": 0,
                "reset": int(oldest_request + window),
                "retry_after": retry_after
            }

        # Add current request
        self.requests[key].append(now)

        return False, {
            "limit": max_requests,
            "remaining": max_requests - current_count - 1,
            "reset": int(now + window),
            "retry_after": 0
        }


class RedisRateLimiter:
    """
    Redis-based rate limiter for distributed systems.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis rate limiter connected")

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis rate limiter disconnected")

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if the key is rate limited using Redis.

        Uses Redis sorted sets for efficient sliding window rate limiting.
        """
        if not self.redis:
            await self.connect()

        now = time.time()
        cutoff = now - window

        # Redis key
        redis_key = f"rate_limit:{key}"

        # Remove old entries
        await self.redis.zremrangebyscore(redis_key, 0, cutoff)

        # Count current requests
        current_count = await self.redis.zcard(redis_key)

        if current_count >= max_requests:
            # Get oldest request time
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            oldest_time = oldest[0][1] if oldest else now

            retry_after = int(oldest_time + window - now) + 1

            return True, {
                "limit": max_requests,
                "remaining": 0,
                "reset": int(oldest_time + window),
                "retry_after": retry_after
            }

        # Add current request
        await self.redis.zadd(redis_key, {str(now): now})

        # Set expiration
        await self.redis.expire(redis_key, window)

        return False, {
            "limit": max_requests,
            "remaining": max_requests - current_count - 1,
            "reset": int(now + window),
            "retry_after": 0
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests.
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_config: Optional[RateLimitConfig] = None
    ):
        super().__init__(app)

        # Default configuration: 100 requests per minute
        self.default_config = default_config or RateLimitConfig(
            requests=100,
            window=60
        )

        # Initialize rate limiter
        if redis_url and REDIS_AVAILABLE:
            self.limiter = RedisRateLimiter(redis_url)
            logger.info("Using Redis-based rate limiter")
        else:
            self.limiter = InMemoryRateLimiter()
            logger.warning("Using in-memory rate limiter (not suitable for production)")

        # Endpoint-specific configurations
        self.endpoint_configs = {
            "/api/v1/bills/search": RateLimitConfig(requests=30, window=60),
            "/api/v1/admin": RateLimitConfig(requests=10, window=60),
        }

    def get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses X-Forwarded-For header if available, otherwise client IP.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get first IP from X-Forwarded-For
            return forwarded.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def get_rate_limit_config(self, request: Request) -> RateLimitConfig:
        """Get rate limit configuration for the request path."""
        for path, config in self.endpoint_configs.items():
            if request.url.path.startswith(path):
                return config
        return self.default_config

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/healthz", "/monitoring/health"]:
            return await call_next(request)

        # Get client identifier
        client_id = self.get_client_identifier(request)

        # Get rate limit config for this endpoint
        config = self.get_rate_limit_config(request)

        # Build rate limit key
        key = f"{config.key_prefix}:{request.method}:{request.url.path}:{client_id}"

        # Check rate limit
        is_limited, info = await self.limiter.is_rate_limited(
            key, config.requests, config.window
        )

        if is_limited:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "method": request.method,
                }
            )

            return JSONResponse(
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"]),
                },
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": info["retry_after"]
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response
