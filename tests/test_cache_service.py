"""tests/test_cache_service.py

Unit tests for production-ready cache service.
"""

import sys
sys.path.insert(0, 'src')

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from core.cache_service import CacheService, CacheEntry, create_cache_service


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    yield str(cache_dir)
    # Cleanup
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def cache(temp_cache_dir):
    """Create a cache service instance for testing."""
    return CacheService(base_dir=temp_cache_dir, enabled=True)


def test_cache_entry_creation():
    """Test CacheEntry dataclass creation."""
    entry = CacheEntry(
        key="test_key",
        value={"data": "test"},
        created_at=time.time(),
        ttl=300
    )

    assert entry.key == "test_key"
    assert entry.value == {"data": "test"}
    assert entry.ttl == 300
    assert not entry.is_expired()


def test_cache_entry_expiration():
    """Test cache entry expiration logic."""
    # Entry that expires in 1 second
    entry = CacheEntry(
        key="test",
        value="data",
        created_at=time.time() - 2,  # Created 2 seconds ago
        ttl=1  # Expires after 1 second
    )

    assert entry.is_expired()
    assert entry.age_seconds() >= 2


def test_cache_service_initialization(temp_cache_dir):
    """Test cache service initialization."""
    cache = CacheService(base_dir=temp_cache_dir)

    assert cache.enabled is True
    assert cache.base_dir == Path(temp_cache_dir)
    assert cache.default_ttl == 300
    assert Path(temp_cache_dir).exists()


def test_cache_service_disabled():
    """Test cache service when disabled."""
    cache = CacheService(enabled=False)

    # Operations should return None/False when disabled
    assert cache.set("key", "value") is False
    assert cache.get("key") is None
    assert cache.delete("key") is False


def test_cache_set_and_get(cache):
    """Test basic set and get operations."""
    # Set a value
    result = cache.set("test_key", {"data": "test_value"}, ttl=300)
    assert result is True

    # Get the value
    value = cache.get("test_key")
    assert value == {"data": "test_value"}


def test_cache_miss(cache):
    """Test cache miss (key doesn't exist)."""
    value = cache.get("nonexistent_key")
    assert value is None

    # Check statistics
    stats = cache.stats()
    assert stats['misses'] == 1
    assert stats['hits'] == 0


def test_cache_hit_statistics(cache):
    """Test cache hit statistics tracking."""
    # Set and get a value
    cache.set("key1", "value1")
    cache.get("key1")

    stats = cache.stats()
    assert stats['hits'] == 1
    assert stats['sets'] == 1


def test_cache_expiration(cache):
    """Test cache expiration with short TTL."""
    # Set with 1-second TTL
    cache.set("expiring_key", "value", ttl=1)

    # Should exist immediately
    assert cache.get("expiring_key") == "value"

    # Wait for expiration
    time.sleep(1.1)

    # Should be expired now
    assert cache.get("expiring_key") is None

    # Check statistics
    stats = cache.stats()
    assert stats['expired'] == 1


def test_cache_delete(cache):
    """Test cache deletion."""
    # Set a value
    cache.set("delete_me", "value")
    assert cache.get("delete_me") == "value"

    # Delete it
    result = cache.delete("delete_me")
    assert result is True

    # Verify it's gone
    assert cache.get("delete_me") is None

    # Check statistics
    stats = cache.stats()
    assert stats['deletes'] == 1


def test_cache_clear(cache):
    """Test clearing all cache entries."""
    # Set multiple values
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    # Clear cache
    deleted = cache.clear()
    assert deleted == 3

    # Verify all are gone
    assert cache.get("key1") is None
    assert cache.get("key2") is None
    assert cache.get("key3") is None


def test_cache_cleanup_expired(cache):
    """Test cleanup of expired entries."""
    # Set entries with different TTLs
    cache.set("fresh", "value", ttl=300)  # 5 minutes
    cache.set("expiring", "value", ttl=1)  # 1 second

    # Wait for one to expire
    time.sleep(1.1)

    # Cleanup expired
    removed = cache.cleanup_expired()
    assert removed == 1

    # Fresh entry should still exist
    assert cache.get("fresh") == "value"

    # Expired entry should be gone
    assert cache.get("expiring") is None


def test_cache_statistics(cache):
    """Test comprehensive cache statistics."""
    # Perform various operations
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.get("key1")  # Hit
    cache.get("key3")  # Miss
    cache.delete("key2")

    stats = cache.stats()

    assert stats['sets'] == 2
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['deletes'] == 1
    assert stats['total_requests'] == 2  # 1 hit + 1 miss
    assert stats['hit_rate_percent'] == 50.0  # 1/2 = 50%
    assert stats['enabled'] is True


def test_cache_ttl_for_domain(cache):
    """Test domain-specific TTL values."""
    assert cache.get_ttl_for_domain('rideshare') == 300  # 5 minutes
    assert cache.get_ttl_for_domain('restaurants') == 3600  # 1 hour
    assert cache.get_ttl_for_domain('geocoding') == 86400  # 24 hours
    assert cache.get_ttl_for_domain('unknown') == 300  # Default


def test_backward_compatibility_old_interface(cache):
    """Test backward compatibility with old cache interface."""
    # Old interface: set(data, arg1, arg2)
    cache.set("test_data", "arg1", "arg2")
    result = cache.get("arg1", "arg2")
    assert result == "test_data"


def test_backward_compatibility_get_stats(cache):
    """Test backward compatible get_stats() method."""
    cache.set("key1", "value1")

    stats = cache.get_stats()

    # Should return old format
    assert 'total_entries' in stats
    assert 'total_size_bytes' in stats
    assert 'total_size_mb' in stats
    assert 'cache_dir' in stats


def test_backward_compatibility_clear_expired(cache):
    """Test backward compatible clear_expired() method."""
    # Set an expiring entry
    cache.set("expiring", "value", ttl=1)
    time.sleep(1.1)

    # Use old method name
    removed = cache.clear_expired()
    assert removed == 1


def test_create_cache_service():
    """Test convenience function for creating cache service."""
    cache = create_cache_service(enabled=True)

    assert isinstance(cache, CacheService)
    assert cache.enabled is True


def test_cache_with_complex_data(cache):
    """Test caching complex data structures."""
    complex_data = {
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "number": 42,
        "string": "test"
    }

    cache.set("complex", complex_data)
    retrieved = cache.get("complex")

    assert retrieved == complex_data
    assert retrieved["list"] == [1, 2, 3]
    assert retrieved["dict"]["nested"] == "value"


def test_cache_file_creation(temp_cache_dir):
    """Test that cache files are created properly."""
    cache = CacheService(base_dir=temp_cache_dir)
    cache.set("test", "value")

    # Check that a cache file was created
    cache_files = list(Path(temp_cache_dir).glob("*.json"))
    assert len(cache_files) == 1

    # File should be JSON
    import json
    with open(cache_files[0], 'r') as f:
        data = json.load(f)

    assert 'key' in data
    assert 'value' in data
    assert 'created_at' in data
    assert 'ttl' in data


def test_cache_corrupted_file_handling(cache, temp_cache_dir):
    """Test handling of corrupted cache files."""
    # Get the hashed filename for the key "corrupted"
    import hashlib
    key_hash = hashlib.md5("corrupted".encode()).hexdigest()
    corrupted_file = Path(temp_cache_dir) / f"{key_hash}.json"

    # Create a corrupted cache file
    with open(corrupted_file, 'w') as f:
        f.write("invalid json {{{")

    # Should handle gracefully and return None
    result = cache.get("corrupted")
    assert result is None

    # Corrupted file should be deleted
    assert not corrupted_file.exists()


def test_cache_hit_rate_calculation(cache):
    """Test hit rate percentage calculation."""
    # No requests yet
    stats = cache.stats()
    assert stats['hit_rate_percent'] == 0.0

    # Set some values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # 2 hits, 1 miss = 66.67%
    cache.get("key1")  # Hit
    cache.get("key2")  # Hit
    cache.get("key3")  # Miss

    stats = cache.stats()
    assert stats['total_requests'] == 3
    assert stats['hits'] == 2
    assert stats['misses'] == 1
    assert abs(stats['hit_rate_percent'] - 66.67) < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
