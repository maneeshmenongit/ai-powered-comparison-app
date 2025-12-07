"""
Production-ready rate limiting service using token bucket algorithm.
Prevents API rate limit violations with automatic backoff.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass
from threading import Lock


@dataclass
class RateLimitConfig:
    """Configuration for a rate-limited API."""
    max_requests: int      # Maximum requests allowed
    time_window: int       # Time window in seconds
    name: str             # API name for logging

    @property
    def tokens_per_second(self) -> float:
        """Calculate token refill rate per second."""
        return self.max_requests / self.time_window


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    The bucket starts full and refills at a constant rate.
    Each request consumes one token. If no tokens available, request must wait.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize token bucket.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.tokens = float(config.max_requests)  # Start with full bucket
        self.last_refill = time.time()
        self.lock = Lock()  # Thread-safe operations

        # Statistics
        self._total_requests = 0
        self._total_waits = 0
        self._total_wait_time = 0.0

    def _refill(self):
        """Refill tokens based on time elapsed since last refill."""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.config.tokens_per_second

        # Add tokens (capped at max)
        self.tokens = min(self.config.max_requests, self.tokens + tokens_to_add)
        self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if not available
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                self._total_requests += 1
                return True

            return False

    def wait_and_acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until tokens are available, then acquire.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if acquired, False if timeout
        """
        start_time = time.time()

        while True:
            with self.lock:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self._total_requests += 1

                    # Record wait time if we waited
                    wait_time = time.time() - start_time
                    if wait_time > 0.1:  # Only count significant waits
                        self._total_waits += 1
                        self._total_wait_time += wait_time

                    return True

                # Check timeout
                if timeout and (time.time() - start_time) >= timeout:
                    return False

                # Calculate wait time needed
                tokens_needed = tokens - self.tokens
                wait_seconds = tokens_needed / self.config.tokens_per_second

            # Sleep outside the lock (allow other threads to acquire)
            time.sleep(min(wait_seconds, 0.1))  # Check at least every 100ms

    def reset(self):
        """Reset the bucket to full capacity."""
        with self.lock:
            self.tokens = float(self.config.max_requests)
            self.last_refill = time.time()

    def available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            self._refill()
            return self.tokens

    def stats(self) -> Dict:
        """Get bucket statistics."""
        with self.lock:
            self._refill()  # Refill tokens before getting stats
            avg_wait = (self._total_wait_time / self._total_waits) if self._total_waits > 0 else 0

            return {
                'api_name': self.config.name,
                'max_requests': self.config.max_requests,
                'time_window': self.config.time_window,
                'available_tokens': round(self.tokens, 2),  # Use self.tokens directly to avoid deadlock
                'total_requests': self._total_requests,
                'total_waits': self._total_waits,
                'total_wait_time': round(self._total_wait_time, 2),
                'average_wait_time': round(avg_wait, 2),
                'refill_rate': round(self.config.tokens_per_second, 4),
            }


class RateLimiter:
    """
    Centralized rate limiting service for all APIs.

    Features:
    - Token bucket algorithm per API
    - Automatic waiting/retry
    - Thread-safe operations
    - Statistics tracking
    - Configurable per API

    Usage:
        limiter = RateLimiter()

        # Add API configurations
        limiter.add_limit('uber', max_requests=1000, time_window=3600)
        limiter.add_limit('lyft', max_requests=500, time_window=3600)

        # Acquire before API call (waits if needed)
        limiter.acquire('uber')
        response = uber_client.get_estimate(...)

        # Or try without waiting
        if limiter.try_acquire('uber'):
            response = uber_client.get_estimate(...)
        else:
            print("Rate limit reached, try later")
    """

    # Default rate limits for common APIs
    DEFAULT_LIMITS = {
        'uber': RateLimitConfig(max_requests=1000, time_window=3600, name='uber'),
        'lyft': RateLimitConfig(max_requests=500, time_window=3600, name='lyft'),
        'via': RateLimitConfig(max_requests=1000, time_window=3600, name='via'),
        'yelp': RateLimitConfig(max_requests=5000, time_window=86400, name='yelp'),
        'google_places': RateLimitConfig(max_requests=1000, time_window=86400, name='google_places'),
        'nominatim': RateLimitConfig(max_requests=1, time_window=1, name='nominatim'),  # 1 req/sec
    }

    def __init__(self, enabled: bool = True):
        """
        Initialize rate limiter.

        Args:
            enabled: Whether rate limiting is enabled (useful for testing)
        """
        self.enabled = enabled
        self.buckets: Dict[str, TokenBucket] = {}

        # Initialize with default limits
        for api_name, config in self.DEFAULT_LIMITS.items():
            self.buckets[api_name] = TokenBucket(config)

    def add_limit(self, api_name: str, max_requests: int, time_window: int):
        """
        Add or update rate limit for an API.

        Args:
            api_name: Name of the API
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        config = RateLimitConfig(
            max_requests=max_requests,
            time_window=time_window,
            name=api_name
        )
        self.buckets[api_name] = TokenBucket(config)

    def try_acquire(self, api_name: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            api_name: Name of the API
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if acquired, False if not available
        """
        if not self.enabled:
            return True

        if api_name not in self.buckets:
            # No limit configured, allow request
            return True

        return self.buckets[api_name].acquire(tokens)

    def acquire(self, api_name: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens, waiting if necessary.

        Args:
            api_name: Name of the API
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if acquired, False if timeout
        """
        if not self.enabled:
            return True

        if api_name not in self.buckets:
            # No limit configured, allow request
            return True

        return self.buckets[api_name].wait_and_acquire(tokens, timeout)

    def wait_if_needed(self, api_name: str, tokens: int = 1):
        """
        Convenience method that waits if rate limit reached.
        Raises exception if can't acquire within reasonable time.

        Args:
            api_name: Name of the API
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            TimeoutError: If can't acquire tokens within 60 seconds
        """
        if not self.acquire(api_name, tokens, timeout=60.0):
            raise TimeoutError(f"Could not acquire rate limit for {api_name} within 60 seconds")

    def reset(self, api_name: str):
        """
        Reset rate limit for an API.

        Args:
            api_name: Name of the API
        """
        if api_name in self.buckets:
            self.buckets[api_name].reset()

    def reset_all(self):
        """Reset all rate limits."""
        for bucket in self.buckets.values():
            bucket.reset()

    def available_tokens(self, api_name: str) -> float:
        """
        Get available tokens for an API.

        Args:
            api_name: Name of the API

        Returns:
            Number of available tokens
        """
        if api_name not in self.buckets:
            return float('inf')  # Unlimited

        return self.buckets[api_name].available_tokens()

    def stats(self, api_name: Optional[str] = None) -> Dict:
        """
        Get rate limiter statistics.

        Args:
            api_name: Optional API name (if None, returns all)

        Returns:
            Statistics dictionary
        """
        if api_name:
            if api_name in self.buckets:
                return self.buckets[api_name].stats()
            return {}

        # Return stats for all APIs
        return {
            name: bucket.stats()
            for name, bucket in self.buckets.items()
        }


# Convenience function for creating rate limiter
def create_rate_limiter(enabled: bool = True) -> RateLimiter:
    """
    Create a rate limiter instance with default limits.

    Args:
        enabled: Whether rate limiting is enabled

    Returns:
        RateLimiter instance
    """
    return RateLimiter(enabled=enabled)
