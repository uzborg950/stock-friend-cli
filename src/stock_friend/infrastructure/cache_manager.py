"""
Simplified cache manager using DiskCache library.

Provides persistent caching with automatic expiration and LRU eviction.
"""

import fnmatch
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import diskcache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache manager wrapping DiskCache for persistent caching.

    Features:
    - Persistent disk-based cache with automatic expiration
    - LRU eviction when size limit reached
    - Thread-safe operations
    - Simple API wrapping DiskCache

    Benefits:
    - Reduced API calls (cost savings, rate limit compliance)
    - Faster response times
    - Offline capability (stale data better than no data)
    - Production-ready with DiskCache reliability
    """

    def __init__(self, cache_dir: str = "data/cache", size_limit_mb: int = 500):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            size_limit_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize DiskCache with size limit
        size_limit_bytes = size_limit_mb * 1024 * 1024
        self.cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=size_limit_bytes,
            eviction_policy="least-recently-used",
        )

        logger.info(
            f"Initialized cache at {self.cache_dir} with {size_limit_mb}MB limit"
        )

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: timedelta) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live duration
        """
        try:
            expire = ttl.total_seconds()
            self.cache.set(key, value, expire=expire)
            logger.debug(f"Cached: {key} (TTL: {ttl})")
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")

    def invalidate(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "stock:AAPL:*")

        Note:
            DiskCache doesn't support glob patterns directly, so we iterate
            through all keys. For large caches, consider using tags instead.
        """
        try:
            keys_to_delete = [k for k in self.cache if fnmatch.fnmatch(k, pattern)]

            for key in keys_to_delete:
                del self.cache[key]

            logger.info(
                f"Invalidated {len(keys_to_delete)} cache entries matching: {pattern}"
            )
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern {pattern}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.cache.clear()
            logger.info("Cleared all cache entries")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            size_mb = self.cache.volume() / (1024 * 1024)
            return {
                "entries": len(self.cache),
                "size_mb": round(size_mb, 2),
                "cache_dir": str(self.cache_dir),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"entries": 0, "size_mb": 0, "cache_dir": str(self.cache_dir)}

    def close(self) -> None:
        """Close the cache (cleanup resources)."""
        try:
            self.cache.close()
            logger.info("Cache closed")
        except Exception as e:
            logger.error(f"Cache close error: {e}")
