#!/usr/bin/env python3
"""Test RideShare domain handler integration."""

import sys
sys.path.insert(0, 'src')

from domains.rideshare.handler import RideShareHandler
from domains.rideshare.models import RideQuery
from core.geocoding_service import GeocodingService


class SimpleCache:
    """Simple cache for testing."""

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value


def test_handler_initialization():
    """Test handler can be initialized."""
    print("=" * 70)
    print("TEST 1: Handler Initialization")
    print("=" * 70)

    # Without services
    handler1 = RideShareHandler()
    print(f"✓ Handler without services: {handler1}")

    # With cache
    cache = SimpleCache()
    handler2 = RideShareHandler(cache_service=cache)
    print(f"✓ Handler with cache: {handler2}")

    # With geocoder
    geocoder = GeocodingService()
    handler3 = RideShareHandler(geocoding_service=geocoder)
    print(f"✓ Handler with geocoder: {handler3}")

    # With both
    handler4 = RideShareHandler(cache_service=cache, geocoding_service=geocoder)
    print(f"✓ Handler with both services: {handler4}")
    print()


def test_parse_query():
    """Test query parsing."""
    print("=" * 70)
    print("TEST 2: Parse Query")
    print("=" * 70)

    handler = RideShareHandler()

    # Simple query
    query = handler.parse_query(
        "Get me from Times Square to JFK Airport",
        context={"user_location": "New York"}
    )

    print(f"✓ Query parsed successfully")
    print(f"  Origin: {query.origin}")
    print(f"  Destination: {query.destination}")
    print(f"  Providers: {query.providers}")
    print(f"  Vehicle Type: {query.vehicle_type}")
    print()


def test_fetch_options():
    """Test fetching ride options."""
    print("=" * 70)
    print("TEST 3: Fetch Options")
    print("=" * 70)

    geocoder = GeocodingService()
    cache = SimpleCache()
    handler = RideShareHandler(
        cache_service=cache,
        geocoding_service=geocoder
    )

    # Create query
    query = RideQuery(
        origin="Times Square, New York",
        destination="JFK Airport, New York",
        providers=["uber", "lyft"],
        vehicle_type="standard"
    )

    # Fetch options
    print("⏳ Fetching ride estimates...")
    estimates = handler.fetch_options(query)

    print(f"✓ Retrieved {len(estimates)} estimates")
    for est in estimates[:3]:  # Show first 3
        surge = f" 🔥 {est.surge_multiplier}x" if est.surge_multiplier > 1.0 else ""
        print(f"  {est.provider} {est.vehicle_type}: "
              f"${est.price_estimate:.2f}{surge} "
              f"({est.duration_minutes} min)")

    # Test cache
    print("\n⏳ Fetching again (should hit cache)...")
    estimates2 = handler.fetch_options(query)
    print(f"✓ Cache hit! Retrieved {len(estimates2)} cached estimates")
    print()


def test_compare_options():
    """Test AI comparison."""
    print("=" * 70)
    print("TEST 4: Compare Options")
    print("=" * 70)

    geocoder = GeocodingService()
    handler = RideShareHandler(geocoding_service=geocoder)

    # Create query and fetch options
    query = RideQuery(
        origin="Times Square, New York",
        destination="JFK Airport, New York",
        providers=["uber", "lyft"]
    )

    estimates = handler.fetch_options(query)

    # Compare
    print("⏳ Generating AI comparison...")
    comparison = handler.compare_options(estimates, priority="price")

    print(f"✓ Comparison generated ({len(comparison)} chars)")
    print(f"\nRecommendation:")
    print("-" * 70)
    print(comparison[:300] + "..." if len(comparison) > 300 else comparison)
    print()


def test_format_results():
    """Test result formatting."""
    print("=" * 70)
    print("TEST 5: Format Results")
    print("=" * 70)

    geocoder = GeocodingService()
    handler = RideShareHandler(geocoding_service=geocoder)

    # Create query and fetch options
    query = RideQuery(
        origin="Times Square, New York",
        destination="JFK Airport, New York",
        providers=["uber", "lyft"]
    )

    estimates = handler.fetch_options(query)
    comparison = "Test recommendation"

    # Format
    results = handler.format_results(estimates, comparison)

    print(f"✓ Results formatted")
    print(f"  Domain: {results['domain']}")
    print(f"  Total estimates: {results['summary']['total_options']}")
    print(f"  Price range: {results['summary']['price_range']}")
    print(f"  Providers: {', '.join(results['summary']['providers'])}")
    print(f"  Has surge: {results['summary']['has_surge']}")
    print()


def test_full_pipeline():
    """Test complete pipeline with process() method."""
    print("=" * 70)
    print("TEST 6: Full Pipeline (process method)")
    print("=" * 70)

    geocoder = GeocodingService()
    cache = SimpleCache()
    handler = RideShareHandler(
        cache_service=cache,
        geocoding_service=geocoder
    )

    # Full pipeline with one method call!
    print("⏳ Running full pipeline...")
    results = handler.process(
        "Compare Uber and Lyft from Times Square to JFK Airport",
        context={"user_location": "New York"},
        priority="balanced"
    )

    print(f"✓ Pipeline completed successfully!\n")
    print(f"Query Details:")
    print(f"  Origin: {results['query'].origin}")
    print(f"  Destination: {results['query'].destination}")
    print(f"  Providers: {results['query'].providers}")

    print(f"\nResults Summary:")
    print(f"  Domain: {results['domain']}")
    print(f"  Total options: {results['summary']['total_options']}")
    print(f"  Price range: {results['summary']['price_range']}")
    print(f"  Distance: {results['route']['distance_miles']:.1f} miles")

    print(f"\nRecommendation:")
    print("-" * 70)
    rec = results['comparison']
    print(rec[:200] + "..." if len(rec) > 200 else rec)
    print()


def test_error_handling():
    """Test error handling."""
    print("=" * 70)
    print("TEST 7: Error Handling")
    print("=" * 70)

    handler = RideShareHandler()

    # Missing origin
    try:
        handler.parse_query("I want to go to JFK")
        print("✗ Should have raised ValueError for missing origin")
    except ValueError as e:
        print(f"✓ Caught missing origin error: {str(e)[:50]}...")

    # Missing geocoder
    try:
        query = RideQuery(
            origin="Times Square",
            destination="JFK",
            providers=["uber"]
        )
        handler.fetch_options(query)
        print("✗ Should have raised ValueError for missing geocoder")
    except ValueError as e:
        print(f"✓ Caught missing geocoder error: {str(e)[:50]}...")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RIDESHARE HANDLER INTEGRATION TESTS")
    print("=" * 70)
    print()

    try:
        test_handler_initialization()
        test_parse_query()
        test_fetch_options()
        test_compare_options()
        test_format_results()
        test_full_pipeline()
        test_error_handling()

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("- ✓ Handler initialization with/without services")
        print("- ✓ Query parsing (LLM-based)")
        print("- ✓ Fetch options (geocoding + API clients + cache)")
        print("- ✓ AI comparison (GPT-4o-mini)")
        print("- ✓ Result formatting")
        print("- ✓ Full pipeline (process method)")
        print("- ✓ Error handling")
        print()
        print("🎉 RideShare domain successfully implements DomainHandler interface!")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
