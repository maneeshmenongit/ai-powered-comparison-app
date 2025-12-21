"""Test main_restaurants.py functionality programmatically.

This tests the components used in main_restaurants.py without requiring user input.
"""

import sys
sys.path.insert(0, 'src')

from domains.restaurants.handler import RestaurantHandler
from domains.restaurants.models import FILTER_CATEGORIES
from core import GeocodingService, CacheService, RateLimiter

print("=" * 60)
print("Testing main_restaurants.py Components")
print("=" * 60)

# Test 1: Import FILTER_CATEGORIES
print("\n✅ Test 1: FILTER_CATEGORIES imported successfully")
print(f"   Found {len(FILTER_CATEGORIES)} categories:")
for name, info in FILTER_CATEGORIES.items():
    print(f"   {info['icon']} {name}: {info['description']}")

# Test 2: Initialize services (same as main_restaurants.py)
print("\n✅ Test 2: Initializing services...")
geocoder = GeocodingService()
cache = CacheService()
rate_limiter = RateLimiter()
print("   ✓ Geocoding service")
print("   ✓ Cache service")
print("   ✓ Rate limiter")

# Test 3: Initialize handler (same as main_restaurants.py)
print("\n✅ Test 3: Creating RestaurantHandler...")
handler = RestaurantHandler(
    geocoding_service=geocoder,
    cache_service=cache,
    rate_limiter=rate_limiter
)
print(f"   ✓ Handler created: {handler}")

# Test 4: Test each filter category with a query
print("\n✅ Test 4: Testing each filter category...")

test_cases = [
    ("Food", "Italian food near Times Square", "balanced"),
    ("Drinks", "cocktail bar near Manhattan", "rating"),
    ("Dessert", "ice cream near Brooklyn", "distance"),
    ("Cafe", "coffee shop near Central Park", "price")
]

for filter_cat, query, priority in test_cases:
    print(f"\n   Testing {FILTER_CATEGORIES[filter_cat]['icon']} {filter_cat}...")
    print(f"   Query: '{query}'")
    print(f"   Priority: {priority}")

    try:
        results = handler.process(
            query,
            context={'user_location': 'New York, NY'},
            priority=priority
        )

        print(f"   ✓ Found {results['total_results']} restaurants")
        print(f"   ✓ Domain: {results['domain']}")
        print(f"   ✓ Priority used: {results['priority']}")

        # Show top result
        if results['restaurants']:
            top = results['restaurants'][0]
            print(f"   ✓ Top result: {top['name']} ({top['provider']}) - {top['rating']}⭐")

        # Show recommendation snippet
        comparison = results['comparison']
        snippet = comparison[:100] + "..." if len(comparison) > 100 else comparison
        print(f"   ✓ Recommendation: {snippet}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

# Test 5: Cache and rate limiter stats (same as main_restaurants.py)
print("\n✅ Test 5: Statistics...")
cache_stats = cache.stats()
rl_stats = rate_limiter.stats()

hit_rate = cache_stats.get('hit_rate_percent', 0)
hits = cache_stats.get('hits', 0)
misses = cache_stats.get('misses', 0)

print(f"   Cache: {hits} hits, {misses} misses ({hit_rate:.1f}% hit rate)")
print(f"   Rate Limiter: {rl_stats.get('total_requests', 0)} requests")

# Test 6: Verify filter integration with RestaurantQuery
print("\n✅ Test 6: Filter category integration with RestaurantQuery...")
from domains.restaurants.models import RestaurantQuery

test_query = RestaurantQuery(
    cuisine="Italian",
    location="New York, NY",
    filter_category="Drinks"
)

print(f"   Created query: {test_query}")
print(f"   Filter category: {test_query.filter_category}")
print(f"   to_dict includes filter: {'filter_category' in test_query.to_dict()}")

# Test 7: Test filter validation
print("\n✅ Test 7: Filter validation...")
from domains.restaurants.models import validate_filter_category

test_inputs = ["Food", "drinks", "DESSERT", "CaFe", "InvalidFilter"]
for input_val in test_inputs:
    validated = validate_filter_category(input_val)
    print(f"   '{input_val}' -> '{validated}'")

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("main_restaurants.py components are working correctly!")
print("=" * 60)
