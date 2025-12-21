"""tests/test_rate_limiter.py

Unit tests for production-ready rate limiter service.
"""

import sys
sys.path.insert(0, 'src')

import pytest
import time
import threading
from core.rate_limiter import (
    RateLimitConfig,
    TokenBucket,
    RateLimiter,
    create_rate_limiter
)


def test_rate_limit_config():
    """Test RateLimitConfig creation and properties."""
    config = RateLimitConfig(
        max_requests=1000,
        time_window=3600,
        name="test_api"
    )

    assert config.max_requests == 1000
    assert config.time_window == 3600
    assert config.name == "test_api"
    assert abs(config.tokens_per_second - 0.2778) < 0.0001  # 1000/3600


def test_token_bucket_initialization():
    """Test token bucket initialization."""
    config = RateLimitConfig(max_requests=10, time_window=60, name="test")
    bucket = TokenBucket(config)

    assert bucket.tokens == 10.0
    assert bucket.config == config
    assert bucket._total_requests == 0


def test_token_bucket_acquire_success():
    """Test successful token acquisition."""
    config = RateLimitConfig(max_requests=10, time_window=60, name="test")
    bucket = TokenBucket(config)

    # Should be able to acquire tokens
    assert bucket.acquire(1) is True
    assert bucket.tokens == 9.0
    assert bucket._total_requests == 1


def test_token_bucket_acquire_failure():
    """Test token acquisition failure when empty."""
    config = RateLimitConfig(max_requests=2, time_window=60, name="test")
    bucket = TokenBucket(config)

    # Acquire all tokens
    assert bucket.acquire(2) is True
    assert bucket.tokens == 0.0

    # Try to acquire more - should fail
    assert bucket.acquire(1) is False
    assert bucket._total_requests == 1  # Only first acquire counted


def test_token_bucket_refill():
    """Test token bucket refills over time."""
    config = RateLimitConfig(max_requests=10, time_window=1, name="test")  # 10 tokens/sec
    bucket = TokenBucket(config)

    # Consume all tokens
    bucket.acquire(10)
    assert bucket.tokens == 0.0

    # Wait for refill
    time.sleep(0.5)  # Should refill ~5 tokens

    available = bucket.available_tokens()
    assert 4.0 <= available <= 6.0  # Allow some variance


def test_token_bucket_wait_and_acquire():
    """Test waiting for tokens to become available."""
    config = RateLimitConfig(max_requests=5, time_window=1, name="test")
    bucket = TokenBucket(config)

    # Consume all tokens
    bucket.acquire(5)

    # Wait and acquire (should succeed after brief wait)
    start = time.time()
    result = bucket.wait_and_acquire(1, timeout=2.0)
    elapsed = time.time() - start

    assert result is True
    assert 0.1 <= elapsed <= 0.5  # Should wait ~0.2 seconds


def test_token_bucket_wait_timeout():
    """Test timeout when waiting for tokens."""
    config = RateLimitConfig(max_requests=10, time_window=3600, name="test")  # Very slow refill
    bucket = TokenBucket(config)

    # Consume all tokens
    bucket.acquire(10)

    # Try to wait with short timeout - should fail
    start = time.time()
    result = bucket.wait_and_acquire(1, timeout=0.2)
    elapsed = time.time() - start

    assert result is False
    assert 0.2 <= elapsed <= 0.4


def test_token_bucket_reset():
    """Test bucket reset."""
    config = RateLimitConfig(max_requests=10, time_window=60, name="test")
    bucket = TokenBucket(config)

    # Consume some tokens
    bucket.acquire(7)
    assert bucket.tokens == 3.0

    # Reset
    bucket.reset()
    assert bucket.tokens == 10.0


def test_token_bucket_stats():
    """Test bucket statistics tracking."""
    config = RateLimitConfig(max_requests=10, time_window=60, name="test")
    bucket = TokenBucket(config)

    # Make some requests
    bucket.acquire(3)
    bucket.acquire(2)

    stats = bucket.stats()

    assert stats['api_name'] == 'test'
    assert stats['max_requests'] == 10
    assert stats['time_window'] == 60
    assert stats['total_requests'] == 2
    assert stats['available_tokens'] <= 5.0


def test_rate_limiter_initialization():
    """Test rate limiter initialization."""
    limiter = RateLimiter(enabled=True)

    assert limiter.enabled is True
    assert 'uber' in limiter.buckets
    assert 'lyft' in limiter.buckets
    assert 'nominatim' in limiter.buckets


def test_rate_limiter_disabled():
    """Test rate limiter when disabled."""
    limiter = RateLimiter(enabled=False)

    # All operations should succeed immediately
    assert limiter.try_acquire('uber') is True
    assert limiter.acquire('uber') is True


def test_rate_limiter_add_limit():
    """Test adding custom rate limits."""
    limiter = RateLimiter()

    limiter.add_limit('custom_api', max_requests=100, time_window=3600)

    assert 'custom_api' in limiter.buckets
    assert limiter.buckets['custom_api'].config.max_requests == 100


def test_rate_limiter_try_acquire():
    """Test try_acquire method."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=3, time_window=60)

    # Should succeed
    assert limiter.try_acquire('test') is True
    assert limiter.try_acquire('test') is True
    assert limiter.try_acquire('test') is True

    # Should fail (no tokens left)
    assert limiter.try_acquire('test') is False


def test_rate_limiter_acquire_with_wait():
    """Test acquire with automatic waiting."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=2, time_window=1)  # 2 tokens/sec

    # Consume all tokens
    limiter.try_acquire('test')
    limiter.try_acquire('test')

    # Acquire with wait (should succeed after brief wait)
    start = time.time()
    result = limiter.acquire('test', timeout=2.0)
    elapsed = time.time() - start

    assert result is True
    assert 0.3 <= elapsed <= 1.0  # Should wait for refill


def test_rate_limiter_unknown_api():
    """Test rate limiter with unknown API (should allow)."""
    limiter = RateLimiter()

    # Unknown API should be unlimited
    assert limiter.try_acquire('unknown_api') is True
    assert limiter.acquire('unknown_api') is True
    assert limiter.available_tokens('unknown_api') == float('inf')


def test_rate_limiter_wait_if_needed():
    """Test wait_if_needed convenience method."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=5, time_window=1)

    # Should work fine
    limiter.wait_if_needed('test')
    limiter.wait_if_needed('test')

    # Consume remaining tokens
    limiter.try_acquire('test', tokens=3)

    # Should wait and succeed
    limiter.wait_if_needed('test')


def test_rate_limiter_wait_if_needed_timeout():
    """Test wait_if_needed timeout exception."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=10, time_window=3600)  # Very slow refill

    # Consume all tokens
    for _ in range(10):
        limiter.try_acquire('test')

    # Should raise TimeoutError
    with pytest.raises(TimeoutError, match="Could not acquire"):
        limiter.wait_if_needed('test')


def test_rate_limiter_reset():
    """Test resetting a specific API."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=5, time_window=60)

    # Consume tokens
    limiter.try_acquire('test', tokens=5)
    assert limiter.available_tokens('test') < 0.01  # Allow for tiny refill during test

    # Reset
    limiter.reset('test')
    assert limiter.available_tokens('test') == 5.0


def test_rate_limiter_reset_all():
    """Test resetting all APIs."""
    limiter = RateLimiter()
    limiter.add_limit('api1', max_requests=5, time_window=60)
    limiter.add_limit('api2', max_requests=10, time_window=60)

    # Consume tokens from both
    limiter.try_acquire('api1', tokens=5)
    limiter.try_acquire('api2', tokens=10)

    # Reset all
    limiter.reset_all()

    assert limiter.available_tokens('api1') == 5.0
    assert limiter.available_tokens('api2') == 10.0


def test_rate_limiter_stats_single_api():
    """Test getting statistics for a single API."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=10, time_window=60)

    limiter.try_acquire('test', tokens=3)

    stats = limiter.stats('test')

    assert stats['api_name'] == 'test'
    assert stats['total_requests'] == 1
    assert stats['max_requests'] == 10


def test_rate_limiter_stats_all_apis():
    """Test getting statistics for all APIs."""
    limiter = RateLimiter()

    stats = limiter.stats()

    assert isinstance(stats, dict)
    assert 'uber' in stats
    assert 'lyft' in stats
    assert stats['uber']['api_name'] == 'uber'


def test_rate_limiter_thread_safety():
    """Test rate limiter thread safety with concurrent requests."""
    limiter = RateLimiter()
    limiter.add_limit('test', max_requests=100, time_window=10)

    successful_acquires = []

    def make_requests():
        for _ in range(20):
            if limiter.try_acquire('test'):
                successful_acquires.append(1)
            time.sleep(0.01)

    # Create multiple threads
    threads = [threading.Thread(target=make_requests) for _ in range(5)]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Should have acquired exactly 100 tokens (the limit)
    # Note: might be slightly less due to refilling during test
    assert 90 <= len(successful_acquires) <= 110


def test_default_rate_limits():
    """Test that default rate limits are configured correctly."""
    limiter = RateLimiter()

    # Check Uber limit
    uber_stats = limiter.stats('uber')
    assert uber_stats['max_requests'] == 1000
    assert uber_stats['time_window'] == 3600

    # Check Lyft limit
    lyft_stats = limiter.stats('lyft')
    assert lyft_stats['max_requests'] == 500
    assert lyft_stats['time_window'] == 3600

    # Check Nominatim (1 req/sec)
    nominatim_stats = limiter.stats('nominatim')
    assert nominatim_stats['max_requests'] == 1
    assert nominatim_stats['time_window'] == 1


def test_create_rate_limiter():
    """Test convenience function for creating rate limiter."""
    limiter = create_rate_limiter(enabled=True)

    assert isinstance(limiter, RateLimiter)
    assert limiter.enabled is True
    assert 'uber' in limiter.buckets


def test_nominatim_rate_limit():
    """Test Nominatim 1 request/second rate limit."""
    limiter = RateLimiter()

    # First request should succeed
    assert limiter.try_acquire('nominatim') is True

    # Second immediate request should fail
    assert limiter.try_acquire('nominatim') is False

    # Wait 1 second
    time.sleep(1.1)

    # Should succeed now
    assert limiter.try_acquire('nominatim') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
