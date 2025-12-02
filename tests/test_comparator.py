#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'src')

from domains.rideshare.comparator import RideShareComparator
from domains.rideshare.api_clients.mock_uber_client import MockUberClient
from domains.rideshare.api_clients.mock_lyft_client import MockLyftClient
from dotenv import load_dotenv

load_dotenv()

# Check OpenAI key
if not os.getenv('OPENAI_API_KEY'):
    print("❌ ERROR: OPENAI_API_KEY not found")
    sys.exit(1)

print("="*70)
print("TESTING RIDE-SHARE COMPARATOR")
print("="*70)

# Get mock estimates
print("\n📍 Route: Times Square → JFK Airport\n")

uber_client = MockUberClient()
lyft_client = MockLyftClient()

uber_estimates = uber_client.get_price_estimates(
    pickup_lat=40.7580,
    pickup_lng=-73.9855,
    dropoff_lat=40.6413,
    dropoff_lng=-73.7781
)

lyft_estimates = lyft_client.get_price_estimates(
    pickup_lat=40.7580,
    pickup_lng=-73.9855,
    dropoff_lat=40.6413,
    dropoff_lng=-73.7781
)

all_estimates = uber_estimates + lyft_estimates

# Show what we're comparing
print("Available Options:")
print("-" * 70)
for est in all_estimates:
    surge = f" 🔥 {est.surge_multiplier:.1f}x" if est.surge_multiplier and est.surge_multiplier > 1.0 else ""
    print(f"{est.provider.upper()} {est.vehicle_type}: "
          f"${est.price_estimate:.2f}{surge}, "
          f"ETA {est.pickup_eta_minutes}min, "
          f"Trip {est.duration_minutes}min")

# Test comparator
comparator = RideShareComparator()

# Test 1: Balanced priority
print("\n" + "="*70)
print("TEST 1: BALANCED PRIORITY (Best Overall Value)")
print("="*70)
try:
    recommendation = comparator.compare_rides(all_estimates, user_priority="balanced")
    print(f"\n✅ Recommendation:\n{recommendation}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Price priority
print("="*70)
print("TEST 2: PRICE PRIORITY (Cheapest Option)")
print("="*70)
try:
    recommendation = comparator.compare_rides(all_estimates, user_priority="price")
    print(f"\n✅ Recommendation:\n{recommendation}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 3: Time priority
print("="*70)
print("TEST 3: TIME PRIORITY (Fastest)")
print("="*70)
try:
    recommendation = comparator.compare_rides(all_estimates, user_priority="time")
    print(f"\n✅ Recommendation:\n{recommendation}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: Programmatic fallback
print("="*70)
print("TEST 4: PROGRAMMATIC FALLBACK (No LLM)")
print("="*70)
try:
    best_balanced = comparator.identify_best_option(all_estimates, "balanced")
    best_price = comparator.identify_best_option(all_estimates, "price")
    best_time = comparator.identify_best_option(all_estimates, "time")
    
    print(f"\n✅ Best Balanced: {best_balanced.provider.upper()} {best_balanced.vehicle_type} - ${best_balanced.price_estimate:.2f}")
    print(f"✅ Best Price: {best_price.provider.upper()} {best_price.vehicle_type} - ${best_price.price_estimate:.2f}")
    print(f"✅ Best Time: {best_time.provider.upper()} {best_time.vehicle_type} - ETA {best_time.pickup_eta_minutes}min + Trip {best_time.duration_minutes}min")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("🎉 COMPARATOR TESTING COMPLETE")
print("="*70)