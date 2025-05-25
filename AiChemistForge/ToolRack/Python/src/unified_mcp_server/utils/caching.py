"""Caching utilities for the unified MCP server."""

import asyncio
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional

from .exceptions import CacheMissError


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = 0.0
    size_bytes: int = 0

    def __post_init__(self):
        if self.last_accessed == 0.0:
            self.last_accessed = time.time()
        if self.size_bytes == 0:
            self.size_bytes = len(json.dumps(self.value, default=str))

    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)


class MemoryCache:
    """In-memory LRU cache with TTL support."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300.0,  # 5 minutes
        cleanup_interval: float = 60.0,  # 1 minute
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: Dict[str, float] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the cache cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the cache cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value

        Raises:
            CacheMissError: If key is not found or expired
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                raise CacheMissError(f"Cache miss for key: {key}")

            if entry.is_expired():
                del self._cache[key]
                self._access_order.pop(key, None)
                raise CacheMissError(f"Cache entry expired for key: {key}")

            entry.touch()
            self._access_order[key] = time.time()
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        async with self._lock:
            # Calculate expiration time
            ttl_to_use = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + ttl_to_use if ttl_to_use > 0 else None

            # Create cache entry
            entry = CacheEntry(
                key=key, value=value, created_at=time.time(), expires_at=expires_at
            )

            # Evict if necessary
            while len(self._cache) >= self.max_size:
                await self._evict_lru()

            # Store entry
            self._cache[key] = entry
            self._access_order[key] = time.time()

    async def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_order.pop(key, None)
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        try:
            await self.get(key)
            return True
        except CacheMissError:
            return False

    async def size(self) -> int:
        """Get the current cache size."""
        return len(self._cache)

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            total_accesses = sum(entry.access_count for entry in self._cache.values())

            return {
                "entries": len(self._cache),
                "max_size": self.max_size,
                "total_size_bytes": total_size,
                "total_accesses": total_accesses,
                "default_ttl": self.default_ttl,
                "cleanup_interval": self.cleanup_interval,
            }

    async def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._access_order:
            return

        # Find the oldest accessed key
        oldest_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])

        # Remove from cache and access order
        self._cache.pop(oldest_key, None)
        self._access_order.pop(oldest_key, None)

    async def _cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = []

        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_order.pop(key, None)

        return len(expired_keys)

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                async with self._lock:
                    expired_count = await self._cleanup_expired()
                    if expired_count > 0:
                        print(f"Cleaned up {expired_count} expired cache entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cache cleanup: {e}")


class CacheManager:
    """Manages multiple cache instances and provides caching decorators."""

    def __init__(self):
        self.caches: Dict[str, MemoryCache] = {}
        self._default_cache = MemoryCache()

    async def start(self) -> None:
        """Start all cache instances."""
        await self._default_cache.start()
        for cache in self.caches.values():
            await cache.start()

    async def stop(self) -> None:
        """Stop all cache instances."""
        await self._default_cache.stop()
        for cache in self.caches.values():
            await cache.stop()

    def get_cache(self, name: str = "default") -> MemoryCache:
        """Get a cache instance by name."""
        if name == "default":
            return self._default_cache

        if name not in self.caches:
            self.caches[name] = MemoryCache()

        return self.caches[name]

    def create_cache(
        self,
        name: str,
        max_size: int = 1000,
        default_ttl: float = 300.0,
        cleanup_interval: float = 60.0,
    ) -> MemoryCache:
        """Create a new named cache instance."""
        cache = MemoryCache(max_size, default_ttl, cleanup_interval)
        self.caches[name] = cache
        return cache

    def generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Create a stable hash from arguments
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def cached(
        self,
        cache_name: str = "default",
        ttl: Optional[float] = None,
        key_prefix: str = "",
    ):
        """Decorator for caching function results.

        Args:
            cache_name: Name of the cache to use
            ttl: Time to live for cached results
            key_prefix: Prefix for cache keys

        Returns:
            Decorated function
        """

        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                cache = self.get_cache(cache_name)

                # Generate cache key
                func_name = f"{func.__module__}.{func.__name__}"
                key_suffix = self.generate_key(*args, **kwargs)
                cache_key = f"{key_prefix}{func_name}:{key_suffix}"

                # Try to get from cache
                try:
                    return await cache.get(cache_key)
                except CacheMissError:
                    pass

                # Execute function and cache result
                try:
                    result = await func(*args, **kwargs)
                    await cache.set(cache_key, result, ttl)
                    return result
                except Exception:
                    # Don't cache errors
                    raise

            return wrapper

        return decorator

    async def invalidate_pattern(
        self, pattern: str, cache_name: str = "default"
    ) -> int:
        """Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match (simple string contains)
            cache_name: Name of the cache

        Returns:
            Number of entries invalidated
        """
        cache = self.get_cache(cache_name)

        async with cache._lock:
            keys_to_delete = []
            for key in cache._cache.keys():
                if pattern in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                await cache.delete(key)

            return len(keys_to_delete)

    async def stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}

        stats["default"] = await self._default_cache.stats()

        for name, cache in self.caches.items():
            stats[name] = await cache.stats()

        return stats


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def cached_get(key: str, cache_name: str = "default") -> Any:
    """Get a value from cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.get(key)


async def cached_set(
    key: str, value: Any, ttl: Optional[float] = None, cache_name: str = "default"
) -> None:
    """Set a value in cache."""
    cache = cache_manager.get_cache(cache_name)
    await cache.set(key, value, ttl)


async def cached_delete(key: str, cache_name: str = "default") -> bool:
    """Delete a key from cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.delete(key)


def cached(cache_name: str = "default", ttl: Optional[float] = None):
    """Convenience decorator for caching."""
    return cache_manager.cached(cache_name, ttl)
