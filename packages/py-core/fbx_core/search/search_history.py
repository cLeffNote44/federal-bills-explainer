"""
Search history tracking service.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class SearchHistory:
    """Service for tracking and retrieving search history."""

    def __init__(self, redis_client=None):
        """
        Initialize search history service.

        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis = redis_client
        self.use_redis = redis_client is not None

    async def track_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        results_count: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Track a search query.

        Args:
            query: Search query text
            user_id: User ID (if authenticated)
            ip_address: IP address
            results_count: Number of results returned
            filters: Applied filters
        """
        if not query or not query.strip():
            return

        timestamp = datetime.utcnow().isoformat()

        # Track in popular searches (global)
        await self._track_popular_search(query)

        # Track in user's search history (if user_id provided)
        if user_id:
            await self._track_user_search(user_id, query, timestamp, results_count, filters)

        # Track in recent searches by IP (for anonymous users)
        if ip_address and not user_id:
            await self._track_ip_search(ip_address, query, timestamp, results_count, filters)

    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular search queries.

        Args:
            limit: Number of results

        Returns:
            List of popular searches with counts
        """
        if not self.use_redis:
            return []

        try:
            # Get top searches from sorted set
            results = await self.redis.zrevrange(
                "search:popular",
                0,
                limit - 1,
                withscores=True
            )

            return [
                {"query": query.decode() if isinstance(query, bytes) else query, "count": int(score)}
                for query, score in results
            ]

        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return []

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get search history for a specific user.

        Args:
            user_id: User ID
            limit: Number of results

        Returns:
            List of recent searches
        """
        if not self.use_redis:
            return []

        try:
            key = f"search:user:{user_id}"

            # Get recent searches from list
            searches = await self.redis.lrange(key, 0, limit - 1)

            return [
                json.loads(search.decode() if isinstance(search, bytes) else search)
                for search in searches
            ]

        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return []

    async def get_ip_history(
        self,
        ip_address: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get search history for an IP address.

        Args:
            ip_address: IP address
            limit: Number of results

        Returns:
            List of recent searches
        """
        if not self.use_redis:
            return []

        try:
            key = f"search:ip:{ip_address}"

            # Get recent searches from list
            searches = await self.redis.lrange(key, 0, limit - 1)

            return [
                json.loads(search.decode() if isinstance(search, bytes) else search)
                for search in searches
            ]

        except Exception as e:
            logger.error(f"Error getting IP history: {e}")
            return []

    async def get_trending_searches(
        self,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending searches in the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Number of results

        Returns:
            List of trending searches
        """
        if not self.use_redis:
            return []

        try:
            # Get searches from the time window
            min_timestamp = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

            results = await self.redis.zrevrangebyscore(
                "search:trending",
                "+inf",
                min_timestamp,
                start=0,
                num=limit,
                withscores=True
            )

            return [
                {
                    "query": query.decode() if isinstance(query, bytes) else query,
                    "timestamp": datetime.fromtimestamp(score).isoformat()
                }
                for query, score in results
            ]

        except Exception as e:
            logger.error(f"Error getting trending searches: {e}")
            return []

    async def clear_user_history(self, user_id: str):
        """
        Clear search history for a user.

        Args:
            user_id: User ID
        """
        if not self.use_redis:
            return

        try:
            key = f"search:user:{user_id}"
            await self.redis.delete(key)
            logger.info(f"Cleared search history for user: {user_id}")

        except Exception as e:
            logger.error(f"Error clearing user history: {e}")

    async def _track_popular_search(self, query: str):
        """Track in popular searches (increments counter)."""
        if not self.use_redis:
            return

        try:
            # Increment score in sorted set
            await self.redis.zincrby("search:popular", 1, query)

            # Set expiry on the key (30 days)
            await self.redis.expire("search:popular", 30 * 24 * 3600)

        except Exception as e:
            logger.error(f"Error tracking popular search: {e}")

    async def _track_user_search(
        self,
        user_id: str,
        query: str,
        timestamp: str,
        results_count: int,
        filters: Optional[Dict[str, Any]]
    ):
        """Track in user's personal search history."""
        if not self.use_redis:
            return

        try:
            key = f"search:user:{user_id}"

            search_entry = json.dumps({
                "query": query,
                "timestamp": timestamp,
                "results_count": results_count,
                "filters": filters or {}
            })

            # Add to beginning of list
            await self.redis.lpush(key, search_entry)

            # Trim to keep only last 50 searches
            await self.redis.ltrim(key, 0, 49)

            # Set expiry (90 days)
            await self.redis.expire(key, 90 * 24 * 3600)

        except Exception as e:
            logger.error(f"Error tracking user search: {e}")

    async def _track_ip_search(
        self,
        ip_address: str,
        query: str,
        timestamp: str,
        results_count: int,
        filters: Optional[Dict[str, Any]]
    ):
        """Track in IP-based search history (for anonymous users)."""
        if not self.use_redis:
            return

        try:
            key = f"search:ip:{ip_address}"

            search_entry = json.dumps({
                "query": query,
                "timestamp": timestamp,
                "results_count": results_count,
                "filters": filters or {}
            })

            # Add to beginning of list
            await self.redis.lpush(key, search_entry)

            # Trim to keep only last 20 searches
            await self.redis.ltrim(key, 0, 19)

            # Set expiry (7 days for IP-based history)
            await self.redis.expire(key, 7 * 24 * 3600)

            # Also track in trending (with current timestamp as score)
            await self.redis.zadd(
                "search:trending",
                {query: datetime.utcnow().timestamp()}
            )

            # Trim trending to keep last 1000 entries
            await self.redis.zremrangebyrank("search:trending", 0, -1001)

        except Exception as e:
            logger.error(f"Error tracking IP search: {e}")
