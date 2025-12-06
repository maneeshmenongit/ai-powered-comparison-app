#!/usr/bin/env python3
"""Test that clean imports work with new __init__.py files."""

import sys
sys.path.insert(0, 'src')

def test_base_imports():
    """Test base domain imports."""
    print("=" * 70)
    print("TEST 1: Base Domain Imports")
    print("=" * 70)

    from domains.base import DomainHandler, DomainQuery, DomainResult

    print(f"✓ DomainHandler: {DomainHandler}")
    print(f"✓ DomainQuery: {DomainQuery}")
    print(f"✓ DomainResult: {DomainResult}")
    print()


def test_rideshare_imports():
    """Test rideshare domain imports."""
    print("=" * 70)
    print("TEST 2: RideShare Domain Imports")
    print("=" * 70)

    from domains.rideshare import (
        RideShareHandler,
        RideQuery,
        RideEstimate,
        RideShareIntentParser,
        RideShareComparator
    )

    print(f"✓ RideShareHandler: {RideShareHandler}")
    print(f"✓ RideQuery: {RideQuery}")
    print(f"✓ RideEstimate: {RideEstimate}")
    print(f"✓ RideShareIntentParser: {RideShareIntentParser}")
    print(f"✓ RideShareComparator: {RideShareComparator}")
    print()


def test_core_imports():
    """Test core service imports."""
    print("=" * 70)
    print("TEST 3: Core Services Imports")
    print("=" * 70)

    from core import GeocodingService

    print(f"✓ GeocodingService: {GeocodingService}")
    print()


def test_version():
    """Test version tracking."""
    print("=" * 70)
    print("TEST 4: Version Tracking")
    print("=" * 70)

    import domains

    print(f"✓ Domains package version: {domains.__version__}")
    print()


def test_combined_usage():
    """Test using imports together."""
    print("=" * 70)
    print("TEST 5: Combined Usage")
    print("=" * 70)

    from domains.base import DomainHandler
    from domains.rideshare import RideShareHandler
    from core import GeocodingService

    # Create instances
    geocoder = GeocodingService()
    handler = RideShareHandler(geocoding_service=geocoder)

    print(f"✓ Created GeocodingService: {geocoder}")
    print(f"✓ Created RideShareHandler: {handler}")
    print(f"✓ Handler is instance of DomainHandler: {isinstance(handler, DomainHandler)}")
    print()


def main():
    """Run all import tests."""
    print("\n" + "=" * 70)
    print("CLEAN IMPORTS TEST")
    print("=" * 70)
    print()

    try:
        test_base_imports()
        test_rideshare_imports()
        test_core_imports()
        test_version()
        test_combined_usage()

        print("=" * 70)
        print("✅ ALL IMPORT TESTS PASSED")
        print("=" * 70)
        print()
        print("Benefits:")
        print("- ✅ Clean imports: from domains.rideshare import RideShareHandler")
        print("- ✅ Explicit exports: Only public API exposed via __all__")
        print("- ✅ Documentation: Each package self-documents")
        print("- ✅ Version tracking: Package version available")
        print()

    except Exception as e:
        print(f"\n❌ IMPORT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
