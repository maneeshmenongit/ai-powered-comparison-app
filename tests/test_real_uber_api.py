#!/usr/bin/env python3
"""Test real Uber API integration."""

import sys
import os
sys.path.insert(0, 'src')

from domains.rideshare.api_clients.uber_client import UberClient
from dotenv import load_dotenv

load_dotenv()

def test_uber_api():
    """Test real Uber API with live pricing."""
    print("=" * 70)
    print("TESTING REAL UBER API")
    print("=" * 70)

    # Check for API credentials
    if not os.getenv("UBER_SERVER_TOKEN"):
        print("❌ ERROR: UBER_SERVER_TOKEN not found in .env file")
        print("Please add your Uber server token to .env")
        sys.exit(1)

    print(f"\n✓ Uber Server Token found: {os.getenv('UBER_SERVER_TOKEN')[:10]}...")

    # Initialize client
    try:
        client = UberClient()
        print("✓ Uber API client initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)

    # Test 1: Times Square to JFK Airport
    print("=" * 70)
    print("TEST 1: Times Square → JFK Airport")
    print("=" * 70)

    pickup_lat, pickup_lng = 40.7580, -73.9855  # Times Square
    dropoff_lat, dropoff_lng = 40.6413, -73.7781  # JFK Airport

    try:
        print(f"Pickup: ({pickup_lat}, {pickup_lng})")
        print(f"Dropoff: ({dropoff_lat}, {dropoff_lng})")
        print("\n⏳ Fetching real pricing from Uber API...\n")

        estimates = client.get_price_estimates(
            pickup_lat, pickup_lng,
            dropoff_lat, dropoff_lng
        )

        print(f"✓ Received {len(estimates)} estimates\n")

        print("Real Uber Pricing:")
        print("-" * 70)
        for est in estimates:
            surge_note = ""
            if est.surge_multiplier > 1.0:
                surge_note = f" 🔥 {est.surge_multiplier}x surge"

            print(f"{est.vehicle_type}:")
            print(f"  Price: ${est.price_low:.2f} - ${est.price_high:.2f} "
                  f"(est. ${est.price_estimate:.2f}){surge_note}")
            print(f"  Distance: {est.distance_miles:.1f} miles")
            print(f"  Duration: {est.duration_minutes} minutes")
            print(f"  Currency: {est.currency}")
            print()

    except ValueError as e:
        print(f"❌ API Error: {e}")
        print("\nPossible issues:")
        print("- Invalid or expired server token")
        print("- Token doesn't have correct permissions")
        print("- Uber API access not enabled for your app")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Test 2: Get time estimates
    print("=" * 70)
    print("TEST 2: Time Estimates for Times Square")
    print("=" * 70)

    try:
        print("⏳ Fetching pickup time estimates...\n")
        time_estimates = client.get_time_estimates(pickup_lat, pickup_lng)

        if time_estimates:
            print("✓ Pickup Time Estimates:")
            print("-" * 70)
            for product, eta in time_estimates.items():
                print(f"{product}: {eta} minutes")
            print()
        else:
            print("⚠️  No time estimates available")
            print()

    except Exception as e:
        print(f"⚠️  Time estimates unavailable: {e}\n")

    # Test 3: Compare with mock data
    print("=" * 70)
    print("TEST 3: Comparison with Mock Data")
    print("=" * 70)

    try:
        from domains.rideshare.api_clients.mock_uber_client import MockUberClient

        mock_client = MockUberClient(deterministic=True)
        mock_estimates = mock_client.get_price_estimates(
            pickup_lat, pickup_lng,
            dropoff_lat, dropoff_lng
        )

        print("\nReal vs Mock Comparison (UberX):")
        print("-" * 70)

        real_uberx = next((e for e in estimates if "X" in e.vehicle_type.upper()), None)
        mock_uberx = next((e for e in mock_estimates if e.vehicle_type == "UberX"), None)

        if real_uberx and mock_uberx:
            print(f"Real API:  ${real_uberx.price_estimate:.2f} | "
                  f"{real_uberx.distance_miles:.1f} mi | "
                  f"{real_uberx.duration_minutes} min")
            print(f"Mock Data: ${mock_uberx.price_estimate:.2f} | "
                  f"{mock_uberx.distance_miles:.1f} mi | "
                  f"{mock_uberx.duration_minutes} min")

            price_diff = abs(real_uberx.price_estimate - mock_uberx.price_estimate)
            print(f"\nPrice difference: ${price_diff:.2f}")

            if price_diff < 10:
                print("✓ Mock data is reasonably close to real pricing")
            else:
                print("⚠️  Mock data differs significantly from real pricing")

    except Exception as e:
        print(f"⚠️  Could not compare with mock: {e}")

    print("\n" + "=" * 70)
    print("✅ UBER API TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_uber_api()
