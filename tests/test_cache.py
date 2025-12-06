#!/usr/bin/env python3
"""Test caching functionality within same process."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'src')

from main_rideshare import RideShareApp, SimpleCache

def test_cache():
    """Test cache HIT/MISS within same process."""
    print("=" * 70)
    print("TESTING CACHE FUNCTIONALITY")
    print("=" * 70)

    app = RideShareApp()

    # Test coordinates (Times Square to JFK)
    origin_coords = (40.7580, -73.9855)
    dest_coords = (40.6413, -73.7781)

    # Generate cache key
    cache_key = SimpleCache.generate_key(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1]
    )

    print(f"\n📍 Route: Times Square → JFK Airport")
    print(f"🔑 Cache Key: {cache_key}\n")

    # First call - should be MISS
    print("=" * 70)
    print("FIRST CALL (Should be Cache MISS)")
    print("=" * 70)

    cached = app.cache.get(cache_key)
    if cached:
        print("✓ Cache HIT - Using cached data")
    else:
        print("✗ Cache MISS - Fetching fresh data")

    estimates1 = app.fetch_estimates(origin_coords, dest_coords, cache_key)
    print(f"Retrieved {len(estimates1)} estimates")

    # Second call - should be HIT
    print("\n" + "=" * 70)
    print("SECOND CALL (Should be Cache HIT)")
    print("=" * 70)

    cached = app.cache.get(cache_key)
    if cached:
        print("✓ Cache HIT - Using cached data")
        print(f"Retrieved {len(cached)} estimates from cache")
    else:
        print("✗ Cache MISS - Fetching fresh data")
        estimates2 = app.fetch_estimates(origin_coords, dest_coords, cache_key)
        print(f"Retrieved {len(estimates2)} estimates")

    # Verify cache contents
    print("\n" + "=" * 70)
    print("CACHE VERIFICATION")
    print("=" * 70)
    print(f"Cache contains {len(app.cache.cache)} entries")
    print(f"Cache TTL: {app.cache.ttl} seconds (5 minutes)")

    if cache_key in app.cache.cache:
        data, timestamp = app.cache.cache[cache_key]
        import time
        age = time.time() - timestamp
        print(f"✓ Entry found for key: {cache_key}")
        print(f"  - Data: {len(data)} estimates")
        print(f"  - Age: {age:.2f} seconds")
        print(f"  - Expires in: {app.cache.ttl - age:.2f} seconds")
    else:
        print(f"✗ No entry found for key: {cache_key}")

    print("\n" + "=" * 70)
    print("✅ CACHE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_cache()
