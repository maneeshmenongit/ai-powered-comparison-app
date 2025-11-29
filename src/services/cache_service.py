"""Simple file-based caching for API responses."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
import hashlib


class CacheService:
    """
    File-based cache for API responses.

    Caches API responses to disk to:
    1. Reduce API costs
    2. Speed up repeated queries
    3. Work offline for development/testing
    """

    def __init__(self, cache_dir: str = "data/cache", ttl_minutes: int = 60):
        """
        Initialize cache service.

        Args:
            cache_dir: Directory to store cache files
            ttl_minutes: Time-to-live for cached data in minutes
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)

    def _get_cache_key(self, *args) -> str:
        """
        Generate a unique cache key from arguments.

        Args:
            *args: Arguments to hash

        Returns:
            MD5 hash of the arguments
        """
        key_string = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, *args) -> Optional[Any]:
        """
        Retrieve cached data if available and not expired.

        Args:
            *args: Arguments that identify the cached data

        Returns:
            Cached data if available and fresh, None otherwise
        """
        cache_key = self._get_cache_key(*args)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - cached_time > self.ttl:
                # Cache expired, delete it
                cache_path.unlink()
                return None

            return cached["data"]

        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache file, delete it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, data: Any, *args) -> None:
        """
        Store data in cache.

        Args:
            data: Data to cache (must be JSON-serializable)
            *args: Arguments that identify this cached data
        """
        cache_key = self._get_cache_key(*args)
        cache_path = self._get_cache_path(cache_key)

        cached = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        with open(cache_path, 'w') as f:
            json.dump(cached, f, indent=2)

    def clear(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def clear_expired(self) -> int:
        """
        Clear only expired cache entries.

        Returns:
            Number of expired cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                cached_time = datetime.fromisoformat(cached["timestamp"])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                cache_file.unlink()
                count += 1
        return count

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_entries": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }
