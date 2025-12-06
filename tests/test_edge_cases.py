#!/usr/bin/env python3
"""Test edge cases in rideshare comparison."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'src')

from main_rideshare import RideShareApp
from domains.rideshare.models import RideEstimate
from datetime import datetime

def test_empty_estimates():
    """Test comparator with empty list of estimates."""
    print("=" * 70)
    print("TEST 1: Empty Estimates List")
    print("=" * 70)

    app = RideShareApp()

    # Test with empty list
    try:
        result = app.comparator.compare_rides([], user_priority="balanced")
        print(f"✓ Result: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()

def test_single_estimate():
    """Test comparator with only one estimate."""
    print("=" * 70)
    print("TEST 2: Single Estimate")
    print("=" * 70)

    app = RideShareApp()

    # Create single estimate
    estimate = RideEstimate(
        provider="Uber",
        vehicle_type="UberX",
        price_low=35.0,
        price_high=45.0,
        price_estimate=40.0,
        duration_minutes=25,
        pickup_eta_minutes=5,
        distance_miles=12.5,
        last_updated=datetime.now()
    )

    result = app.comparator.compare_rides([estimate], user_priority="balanced")
    print(f"✓ Result: {result}")
    print()

def test_surge_pricing():
    """Test with surge pricing active."""
    print("=" * 70)
    print("TEST 3: Surge Pricing Display")
    print("=" * 70)

    app = RideShareApp()

    # Create estimates with surge
    estimates = [
        RideEstimate(
            provider="Uber",
            vehicle_type="UberX",
            price_low=40.0,
            price_high=60.0,
            price_estimate=50.0,
            surge_multiplier=2.0,
            duration_minutes=25,
            pickup_eta_minutes=5,
            distance_miles=12.5,
            last_updated=datetime.now()
        ),
        RideEstimate(
            provider="Lyft",
            vehicle_type="Lyft",
            price_low=35.0,
            price_high=45.0,
            price_estimate=40.0,
            surge_multiplier=1.0,
            duration_minutes=25,
            pickup_eta_minutes=7,
            distance_miles=12.5,
            last_updated=datetime.now()
        )
    ]

    # Display estimates table
    app.display_estimates_table(estimates)
    print("✓ Surge pricing (2.0x) should be visible with 🔥 emoji")
    print()

def test_all_priority_modes():
    """Test all three priority modes."""
    print("=" * 70)
    print("TEST 4: All Priority Modes")
    print("=" * 70)

    app = RideShareApp()

    # Create diverse estimates
    estimates = [
        RideEstimate(
            provider="Uber",
            vehicle_type="UberX",
            price_low=35.0,
            price_high=45.0,
            price_estimate=40.0,
            duration_minutes=25,
            pickup_eta_minutes=8,
            distance_miles=12.5,
            last_updated=datetime.now()
        ),
        RideEstimate(
            provider="Lyft",
            vehicle_type="Lyft",
            price_low=45.0,
            price_high=55.0,
            price_estimate=50.0,
            duration_minutes=25,
            pickup_eta_minutes=3,
            distance_miles=12.5,
            last_updated=datetime.now()
        )
    ]

    for priority in ["price", "time", "balanced"]:
        print(f"\n{priority.upper()} Priority:")
        print("-" * 70)
        best = app.comparator.identify_best_option(estimates, priority=priority)
        print(f"✓ Best option: {best.provider} {best.vehicle_type}")
        print(f"  - Price: ${best.price_estimate:.2f}")
        print(f"  - Total time: {best.pickup_eta_minutes + best.duration_minutes} min")

    print()

def test_very_long_distance():
    """Test with very long distance route."""
    print("=" * 70)
    print("TEST 5: Very Long Distance Route")
    print("=" * 70)

    app = RideShareApp()

    # New York to Boston distance (~215 miles)
    estimates = app.uber_client.get_price_estimates(
        pickup_lat=40.7580,
        pickup_lng=-73.9855,
        dropoff_lat=42.3601,
        dropoff_lng=-71.0589
    )

    print(f"✓ Generated {len(estimates)} estimates for ~215 mile route")
    print(f"  Distance: {estimates[0].distance_miles:.1f} miles")
    print(f"  Duration: {estimates[0].duration_minutes} minutes")
    print(f"  Price range: ${estimates[0].price_low:.2f} - ${estimates[0].price_high:.2f}")
    print()

def test_very_short_distance():
    """Test with very short distance route."""
    print("=" * 70)
    print("TEST 6: Very Short Distance Route")
    print("=" * 70)

    app = RideShareApp()

    # Times Square to nearby location (~0.5 miles)
    estimates = app.uber_client.get_price_estimates(
        pickup_lat=40.7580,
        pickup_lng=-73.9855,
        dropoff_lat=40.7614,
        dropoff_lng=-73.9776
    )

    print(f"✓ Generated {len(estimates)} estimates for ~0.5 mile route")
    print(f"  Distance: {estimates[0].distance_miles:.1f} miles")
    print(f"  Duration: {estimates[0].duration_minutes} minutes")
    print(f"  Price: ${estimates[0].price_estimate:.2f} (minimum fare applied)")
    print()

def main():
    """Run all edge case tests."""
    print("\n" + "=" * 70)
    print("RIDESHARE EDGE CASE TEST SUITE")
    print("=" * 70)
    print()

    test_empty_estimates()
    test_single_estimate()
    test_surge_pricing()
    test_all_priority_modes()
    test_very_long_distance()
    test_very_short_distance()

    print("=" * 70)
    print("✅ ALL EDGE CASE TESTS COMPLETE")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
