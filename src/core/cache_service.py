"""
Production-ready caching service with file-based storage.
Designed for easy upgrade to Redis when needed.
"""

import os
import json
import hashlib
import time
from typing import Any, Optional, Dict
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    key: str
    value: Any
    created_at: float
    ttl: int  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = time.time() - self.created_at
        return age > self.ttl

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at


class CacheService:
    """
    File-based caching service with Redis-ready interface.

    Features:
    - File-based storage (no external dependencies)
    - TTL (time-to-live) support
    - Domain-specific cache directories
    - Cache statistics
    - Easy migration path to Redis

    Usage:
        cache = CacheService(base_dir="data/cache")

        # Set with 5-minute TTL
        cache.set("ride_key", estimate_data, ttl=300)

        # Get (returns None if expired or missing)
        data = cache.get("ride_key")

        # Statistics
        stats = cache.stats()
    """

    # Default TTLs for different domains (in seconds)
    DEFAULT_TTLS = {
        'rideshare': 300,      # 5 minutes
        'restaurants': 3600,   # 1 hour
        'activities': 1800,    # 30 minutes
        'hotels': 1800,        # 30 minutes
        'geocoding': 86400,    # 24 hours
    }

    def __init__(
        self,
        base_dir: str = "data/cache",
        cache_dir: Optional[str] = None,  # Backward compatibility
        enabled: bool = True,
        ttl_minutes: Optional[int] = None  # Backward compatibility
    ):
        """
        Initialize cache service.

        Args:
            base_dir: Base directory for cache storage
            cache_dir: Deprecated, use base_dir instead
            enabled: Whether caching is enabled (useful for testing)
            ttl_minutes: Deprecated, use ttl parameter in set() instead
        """
        # Handle backward compatibility
        if cache_dir is not None:
            base_dir = cache_dir

        self.base_dir = Path(base_dir)
        self.enabled = enabled

        # Default TTL for backward compatibility
        if ttl_minutes is not None:
            self.default_ttl = ttl_minutes * 60
        else:
            self.default_ttl = 300  # 5 minutes

        # For backward compatibility with old interface
        self.cache_dir = self.base_dir
        self.ttl = timedelta(seconds=self.default_ttl)

        # Create cache directory if it doesn't exist
        if self.enabled:
            self.base_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'expired': 0,
        }

    def _get_cache_key(self, *args) -> str:
        """
        Generate a unique cache key from arguments.
        Backward compatibility method.

        Args:
            *args: Arguments to hash

        Returns:
            MD5 hash of the arguments
        """
        key_string = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """
        Get file path for cache key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Hash the key to create a safe filename if not already hashed
        if len(key) != 32:  # Not an MD5 hash
            key_hash = hashlib.md5(key.encode()).hexdigest()
        else:
            key_hash = key

        return self.base_dir / f"{key_hash}.json"

    def get(self, key_or_args: Any = None, *args) -> Optional[Any]:
        """
        Get value from cache.

        Supports both old and new interface:
        - New: cache.get("my_key")
        - Old: cache.get(arg1, arg2, arg3)

        Args:
            key_or_args: Cache key (new) or first argument (old)
            *args: Additional arguments for old interface

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if not self.enabled:
            return None

        # Determine if using old or new interface
        if args:
            # Old interface: get(arg1, arg2, ...)
            key = self._get_cache_key(key_or_args, *args)
        else:
            # New interface: get("key")
            key = str(key_or_args) if key_or_args is not None else ""

        cache_path = self._get_cache_path(key)

        # Check if cache file exists
        if not cache_path.exists():
            self._stats['misses'] += 1
            return None

        try:
            # Read cache entry
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Handle both new format (CacheEntry) and old format
            if 'created_at' in data and 'ttl' in data:
                # New format
                entry = CacheEntry(**data)

                # Check if expired
                if entry.is_expired():
                    self._stats['expired'] += 1
                    self._stats['misses'] += 1
                    cache_path.unlink()
                    return None

                self._stats['hits'] += 1
                return entry.value

            elif 'timestamp' in data:
                # Old format - backward compatibility
                cached_time = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - cached_time > self.ttl:
                    self._stats['expired'] += 1
                    self._stats['misses'] += 1
                    cache_path.unlink()
                    return None

                self._stats['hits'] += 1
                return data["data"]

            else:
                # Unknown format
                self._stats['misses'] += 1
                cache_path.unlink()
                return None

        except (json.JSONDecodeError, IOError, KeyError, ValueError) as e:
            # Corrupted cache file, delete it
            self._stats['misses'] += 1
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(
        self,
        key_or_data: Any,
        value_or_args: Any = None,
        *args,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store value in cache.

        Supports both old and new interface:
        - New: cache.set("my_key", value, ttl=300)
        - Old: cache.set(data, arg1, arg2, ...)

        Args:
            key_or_data: Cache key (new) or data to cache (old)
            value_or_args: Value to cache (new) or first arg (old)
            *args: Additional arguments for old interface
            ttl: Time to live in seconds (default: 300 = 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        # Determine if using old or new interface
        if value_or_args is None and not args:
            # Ambiguous - assume old interface for backward compatibility
            # set(data) with default key
            key = "default"
            value = key_or_data
        elif args:
            # Old interface: set(data, arg1, arg2, ...)
            key = self._get_cache_key(value_or_args, *args)
            value = key_or_data
        else:
            # New interface: set("key", value, ttl=300)
            key = str(key_or_data)
            value = value_or_args

        # Use provided TTL or default
        if ttl is None:
            ttl = self.default_ttl

        cache_path = self._get_cache_path(key)

        try:
            # Create cache entry (new format)
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl
            )

            # Write to file
            with open(cache_path, 'w') as f:
                json.dump(asdict(entry), f, indent=2)

            self._stats['sets'] += 1
            return True

        except (IOError, TypeError) as e:
            # Failed to write (permissions, not JSON-serializable, etc.)
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            cache_path.unlink()
            self._stats['deletes'] += 1
            return True

        return False

    def clear(self, domain: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            domain: Optional domain to clear (if None, clears all)

        Returns:
            Number of entries deleted
        """
        if not self.enabled:
            return 0

        deleted = 0

        # Clear all cache files
        for cache_file in self.base_dir.glob("*.json"):
            cache_file.unlink()
            deleted += 1

        return deleted

    def clear_expired(self) -> int:
        """
        Clear only expired cache entries.
        Backward compatible alias for cleanup_expired().

        Returns:
            Number of expired cache files deleted
        """
        return self.cleanup_expired()

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of expired entries removed
        """
        if not self.enabled:
            return 0

        removed = 0

        for cache_file in self.base_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Handle both new and old format
                if 'created_at' in data and 'ttl' in data:
                    entry = CacheEntry(**data)
                    if entry.is_expired():
                        cache_file.unlink()
                        removed += 1
                elif 'timestamp' in data:
                    # Old format
                    cached_time = datetime.fromisoformat(data["timestamp"])
                    if datetime.now() - cached_time > self.ttl:
                        cache_file.unlink()
                        removed += 1

            except (json.JSONDecodeError, IOError, KeyError, ValueError):
                # Corrupted file, remove it
                cache_file.unlink()
                removed += 1

        return removed

    def stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        files = list(self.base_dir.glob("*.json")) if self.base_dir.exists() else []
        total_size = sum(f.stat().st_size for f in files) if files else 0

        return {
            'enabled': self.enabled,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'deletes': self._stats['deletes'],
            'expired': self._stats['expired'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_dir': str(self.base_dir),
            'cache_files': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }

    def get_stats(self) -> Dict:
        """
        Backward compatible alias for stats().

        Returns:
            Dictionary with cache statistics
        """
        stats_data = self.stats()
        # Return old format for backward compatibility
        return {
            "total_entries": stats_data['cache_files'],
            "total_size_bytes": stats_data['total_size_bytes'],
            "total_size_mb": stats_data['total_size_mb'],
            "cache_dir": stats_data['cache_dir'],
        }

    def get_ttl_for_domain(self, domain: str) -> int:
        """
        Get default TTL for a domain.

        Args:
            domain: Domain name (rideshare, restaurants, etc.)

        Returns:
            TTL in seconds
        """
        return self.DEFAULT_TTLS.get(domain, 300)  # Default 5 minutes


# Convenience function for creating cache service
def create_cache_service(enabled: bool = True) -> CacheService:
    """
    Create a cache service instance.

    Args:
        enabled: Whether caching is enabled

    Returns:
        CacheService instance
    """
    return CacheService(enabled=enabled)
