"""
Analytics tracking middleware and utilities.

Tracks API usage, performance metrics, and user behavior.
"""

import time
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking API analytics.

    Tracks:
    - Request counts by endpoint
    - Response times
    - Status codes
    - User agents
    - Geographic data (from IP)
    - Error rates
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        self.in_memory_store = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0,
            'status_codes': defaultdict(int),
        })

    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()

        # Extract request metadata
        endpoint = request.url.path
        method = request.method
        user_agent = request.headers.get('user-agent', 'unknown')
        ip_address = self._get_client_ip(request)

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = status_code >= 400
        except Exception as e:
            logger.error(f"Request failed: {e}")
            status_code = 500
            error = True
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Track metrics
            await self._track_request(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration=duration,
                error=error,
                user_agent=user_agent,
                ip_address=ip_address,
            )

        # Add analytics headers
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"

        return response

    async def _track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        error: bool,
        user_agent: str,
        ip_address: str,
    ):
        """Track request metrics."""

        key = f"{method}:{endpoint}"
        timestamp = datetime.utcnow()

        # Update in-memory store
        self.in_memory_store[key]['count'] += 1
        self.in_memory_store[key]['total_time'] += duration
        self.in_memory_store[key]['status_codes'][status_code] += 1
        if error:
            self.in_memory_store[key]['errors'] += 1

        # Store in Redis if available
        if self.redis_client:
            try:
                # Store detailed metrics in Redis
                pipe = self.redis_client.pipeline()

                # Request count
                pipe.hincrby('analytics:requests:count', key, 1)

                # Response time (for percentiles)
                pipe.zadd(
                    f'analytics:requests:times:{key}',
                    {f"{timestamp.isoformat()}:{duration}": duration}
                )

                # Status codes
                pipe.hincrby(f'analytics:status:{key}', status_code, 1)

                # Errors
                if error:
                    pipe.hincrby('analytics:errors:count', key, 1)
                    pipe.lpush(
                        f'analytics:errors:recent',
                        json.dumps({
                            'endpoint': endpoint,
                            'method': method,
                            'status_code': status_code,
                            'timestamp': timestamp.isoformat(),
                        })
                    )
                    pipe.ltrim('analytics:errors:recent', 0, 99)  # Keep last 100

                # User agent tracking
                pipe.hincrby('analytics:user_agents', user_agent, 1)

                # IP tracking (for geographic analysis)
                pipe.hincrby('analytics:ips', ip_address, 1)

                # Hourly metrics
                hour_key = timestamp.strftime('%Y-%m-%d:%H')
                pipe.hincrby(f'analytics:hourly:{hour_key}', key, 1)
                pipe.expire(f'analytics:hourly:{hour_key}', 86400 * 7)  # 7 days

                # Daily metrics
                day_key = timestamp.strftime('%Y-%m-%d')
                pipe.hincrby(f'analytics:daily:{day_key}', key, 1)
                pipe.expire(f'analytics:daily:{day_key}', 86400 * 30)  # 30 days

                await pipe.execute()

            except Exception as e:
                logger.error(f"Failed to store analytics in Redis: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, accounting for proxies."""
        # Check X-Forwarded-For header (behind proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else 'unknown'

    def get_stats(self) -> Dict[str, Any]:
        """Get current in-memory statistics."""
        stats = {}
        for key, data in self.in_memory_store.items():
            avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
            error_rate = data['errors'] / data['count'] if data['count'] > 0 else 0

            stats[key] = {
                'count': data['count'],
                'avg_response_time': round(avg_time * 1000, 2),  # ms
                'error_rate': round(error_rate * 100, 2),  # percentage
                'status_codes': dict(data['status_codes']),
            }

        return stats


class AnalyticsCollector:
    """
    Analytics data collector and aggregator.
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client

    async def get_endpoint_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get endpoint statistics for the last N hours."""
        if not self.redis_client:
            return {}

        try:
            stats = {}

            # Get request counts
            counts = await self.redis_client.hgetall('analytics:requests:count')

            for endpoint, count in counts.items():
                endpoint_str = endpoint.decode() if isinstance(endpoint, bytes) else endpoint
                count_int = int(count)

                # Get response times
                times_key = f'analytics:requests:times:{endpoint_str}'
                times = await self.redis_client.zrange(times_key, 0, -1, withscores=True)

                # Calculate percentiles
                if times:
                    durations = [float(score) for _, score in times]
                    durations.sort()

                    p50 = durations[len(durations) // 2]
                    p95 = durations[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
                    p99 = durations[int(len(durations) * 0.99)] if len(durations) > 1 else durations[0]
                    avg = sum(durations) / len(durations)
                else:
                    p50 = p95 = p99 = avg = 0

                # Get error count
                error_count = await self.redis_client.hget('analytics:errors:count', endpoint_str)
                error_count = int(error_count) if error_count else 0

                stats[endpoint_str] = {
                    'count': count_int,
                    'error_count': error_count,
                    'error_rate': round((error_count / count_int * 100) if count_int > 0 else 0, 2),
                    'avg_response_time': round(avg * 1000, 2),
                    'p50_response_time': round(p50 * 1000, 2),
                    'p95_response_time': round(p95 * 1000, 2),
                    'p99_response_time': round(p99 * 1000, 2),
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get endpoint stats: {e}")
            return {}

    async def get_hourly_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get hourly request trends."""
        if not self.redis_client:
            return {}

        try:
            trends = {}
            now = datetime.utcnow()

            for i in range(hours):
                hour = now - timedelta(hours=i)
                hour_key = hour.strftime('%Y-%m-%d:%H')

                data = await self.redis_client.hgetall(f'analytics:hourly:{hour_key}')

                trends[hour_key] = {
                    endpoint.decode(): int(count)
                    for endpoint, count in data.items()
                } if data else {}

            return trends

        except Exception as e:
            logger.error(f"Failed to get hourly trends: {e}")
            return {}

    async def get_popular_endpoints(self, limit: int = 10) -> list:
        """Get most popular endpoints."""
        if not self.redis_client:
            return []

        try:
            counts = await self.redis_client.hgetall('analytics:requests:count')

            # Sort by count
            sorted_endpoints = sorted(
                [
                    {
                        'endpoint': endpoint.decode() if isinstance(endpoint, bytes) else endpoint,
                        'count': int(count)
                    }
                    for endpoint, count in counts.items()
                ],
                key=lambda x: x['count'],
                reverse=True
            )

            return sorted_endpoints[:limit]

        except Exception as e:
            logger.error(f"Failed to get popular endpoints: {e}")
            return []

    async def get_recent_errors(self, limit: int = 20) -> list:
        """Get recent errors."""
        if not self.redis_client:
            return []

        try:
            errors = await self.redis_client.lrange('analytics:errors:recent', 0, limit - 1)

            return [
                json.loads(error.decode() if isinstance(error, bytes) else error)
                for error in errors
            ]

        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []

    async def get_user_agent_stats(self) -> Dict[str, int]:
        """Get user agent statistics."""
        if not self.redis_client:
            return {}

        try:
            data = await self.redis_client.hgetall('analytics:user_agents')

            return {
                ua.decode() if isinstance(ua, bytes) else ua: int(count)
                for ua, count in data.items()
            }

        except Exception as e:
            logger.error(f"Failed to get user agent stats: {e}")
            return {}
