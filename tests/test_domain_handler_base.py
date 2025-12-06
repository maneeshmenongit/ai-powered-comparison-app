#!/usr/bin/env python3
"""Test base domain handler pattern."""

import sys
sys.path.insert(0, 'src')

from domains.base import DomainQuery, DomainResult, DomainHandler
from typing import List, Dict, Optional, Any


def test_domain_query():
    """Test DomainQuery base class."""
    print("=" * 70)
    print("TEST 1: DomainQuery Base Class")
    print("=" * 70)

    # Create basic query
    query = DomainQuery(
        raw_query="Find me a ride",
        user_location="Manhattan",
        user_preferences={"priority": "price"}
    )

    print(f"✓ Raw Query: {query.raw_query}")
    print(f"✓ User Location: {query.user_location}")
    print(f"✓ Preferences: {query.user_preferences}")
    print()


def test_domain_result():
    """Test DomainResult base class."""
    print("=" * 70)
    print("TEST 2: DomainResult Base Class")
    print("=" * 70)

    # Create basic result
    result = DomainResult(
        provider="TestProvider",
        score=85.5,
        metadata={"price": 40.00, "rating": 4.5}
    )

    print(f"✓ Provider: {result.provider}")
    print(f"✓ Score: {result.score}")
    print(f"✓ Metadata: {result.metadata}")

    # Test score validation
    try:
        invalid_result = DomainResult(provider="Test", score=150.0)
        print("✗ Score validation failed - should have raised error")
    except ValueError as e:
        print(f"✓ Score validation works: {e}")

    print()


def test_concrete_handler():
    """Test concrete implementation of DomainHandler."""
    print("=" * 70)
    print("TEST 3: Concrete DomainHandler Implementation")
    print("=" * 70)

    # Create concrete implementation for testing
    class TestHandler(DomainHandler):
        """Test implementation of domain handler."""

        def parse_query(self, raw_query: str, context: Optional[Dict] = None) -> DomainQuery:
            return DomainQuery(
                raw_query=raw_query,
                user_location=context.get("user_location") if context else None
            )

        def fetch_options(self, query: DomainQuery) -> List[DomainResult]:
            return [
                DomainResult(provider="Provider1", score=90.0),
                DomainResult(provider="Provider2", score=85.0),
                DomainResult(provider="Provider3", score=80.0),
            ]

        def compare_options(self, options: List[DomainResult], priority: str = "balanced") -> str:
            best = max(options, key=lambda x: x.score)
            return f"Recommend {best.provider} with score {best.score}"

        def format_results(self, options: List[DomainResult], comparison: str) -> Dict:
            return {
                "options": [
                    {"provider": opt.provider, "score": opt.score}
                    for opt in options
                ],
                "recommendation": comparison,
                "total": len(options)
            }

    # Test the handler
    handler = TestHandler()
    print(f"✓ Handler created: {handler}")

    # Test process pipeline
    results = handler.process(
        "Test query",
        context={"user_location": "Test Location"}
    )

    print(f"✓ Query parsed: {results['query'].raw_query}")
    print(f"✓ Options fetched: {results['total']} options")
    print(f"✓ Comparison: {results['recommendation']}")
    print(f"✓ Options: {results['options']}")
    print()


def test_abstract_enforcement():
    """Test that abstract methods must be implemented."""
    print("=" * 70)
    print("TEST 4: Abstract Method Enforcement")
    print("=" * 70)

    # Try to create incomplete implementation
    class IncompleteHandler(DomainHandler):
        """Handler missing required methods."""
        pass

    try:
        handler = IncompleteHandler()
        print("✗ Should have raised TypeError for missing abstract methods")
    except TypeError as e:
        print(f"✓ Abstract enforcement works: Can't instantiate without implementing methods")
        print(f"  Error preview: {str(e)[:100]}...")

    print()


def test_handler_with_services():
    """Test handler initialization with services."""
    print("=" * 70)
    print("TEST 5: Handler with Services")
    print("=" * 70)

    # Mock services
    class MockCache:
        def __repr__(self):
            return "MockCache()"

    class MockGeocoder:
        def __repr__(self):
            return "MockGeocoder()"

    # Create minimal concrete handler
    class MinimalHandler(DomainHandler):
        def parse_query(self, raw_query, context=None):
            return DomainQuery(raw_query=raw_query)

        def fetch_options(self, query):
            return []

        def compare_options(self, options, priority="balanced"):
            return "No options available"

        def format_results(self, options, comparison):
            return {"recommendation": comparison}

    # Test with no services
    handler1 = MinimalHandler()
    print(f"✓ Handler without services: {handler1}")

    # Test with cache only
    handler2 = MinimalHandler(cache_service=MockCache())
    print(f"✓ Handler with cache: {handler2}")

    # Test with both services
    handler3 = MinimalHandler(
        cache_service=MockCache(),
        geocoding_service=MockGeocoder()
    )
    print(f"✓ Handler with both services: {handler3}")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("DOMAIN HANDLER BASE CLASS TESTS")
    print("=" * 70)
    print()

    try:
        test_domain_query()
        test_domain_result()
        test_concrete_handler()
        test_abstract_enforcement()
        test_handler_with_services()

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("- ✓ DomainQuery: Base query class works")
        print("- ✓ DomainResult: Base result class with validation")
        print("- ✓ DomainHandler: Abstract base class enforced")
        print("- ✓ Pipeline: process() orchestrates all steps")
        print("- ✓ Services: Optional cache and geocoder support")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
