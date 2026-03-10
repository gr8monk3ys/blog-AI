"""
Redis client for persistent storage.

This module provides a singleton Redis client with connection pooling
and graceful fallback behavior when Redis is unavailable.
"""

import logging
import os
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with connection management.

    Provides a singleton pattern for Redis connections with automatic
    reconnection and health checking capabilities.
    """

    def __init__(self) -> None:
        """Initialize RedisClient with configuration from environment."""
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._client: Optional[redis.Redis] = None
        self._is_available: bool = False
        self._connection_error: Optional[str] = None

    async def get_client(self) -> Optional[redis.Redis]:
        """
        Get or create a Redis client instance.

        Returns:
            Redis client if available, None if connection failed.
        """
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5.0,
                    socket_timeout=5.0,
                    retry_on_timeout=True,
                )
                # Test connection
                await self._client.ping()
                self._is_available = True
                self._connection_error = None
                logger.info("Redis connection established successfully")
            except redis.ConnectionError as e:
                self._connection_error = f"Redis connection failed: {str(e)}"
                logger.warning(self._connection_error)
                self._is_available = False
                self._client = None
            except redis.TimeoutError as e:
                self._connection_error = f"Redis connection timeout: {str(e)}"
                logger.warning(self._connection_error)
                self._is_available = False
                self._client = None
            except Exception as e:
                self._connection_error = f"Redis error: {str(e)}"
                logger.warning(self._connection_error)
                self._is_available = False
                self._client = None

        return self._client

    async def close(self) -> None:
        """Close the Redis connection and cleanup resources."""
        if self._client:
            try:
                await self._client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")
            finally:
                self._client = None
                self._is_available = False

    async def health_check(self) -> dict:
        """
        Check Redis connection health.

        Returns:
            Dictionary with health status information.
        """
        try:
            client = await self.get_client()
            if client is None:
                return {
                    "status": "unavailable",
                    "connected": False,
                    "error": self._connection_error or "Redis not configured",
                    "url_configured": bool(os.environ.get("REDIS_URL")),
                }

            # Ping to verify connection is alive
            await client.ping()

            # Get server info for detailed health
            info = await client.info("server")

            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "url_configured": True,
            }
        except redis.ConnectionError as e:
            self._is_available = False
            self._connection_error = str(e)
            return {
                "status": "unhealthy",
                "connected": False,
                "error": f"Connection error: {str(e)}",
                "url_configured": bool(os.environ.get("REDIS_URL")),
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "url_configured": bool(os.environ.get("REDIS_URL")),
            }

    @property
    def is_available(self) -> bool:
        """Check if Redis is currently available."""
        return self._is_available

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to Redis.

        Returns:
            True if reconnection successful, False otherwise.
        """
        # Close existing connection if any
        if self._client:
            await self.close()

        # Reset state
        self._client = None
        self._is_available = False

        # Try to connect
        client = await self.get_client()
        return client is not None


# Singleton instance
redis_client = RedisClient()
