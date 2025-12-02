#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from domains.rideshare.api_clients.mock_uber_client import MockUberClient
from domains.rideshare.api_clients.mock_lyft_client import MockLyftClient

print("="*70)
print("TESTING MOCK API CLIENTS")
print("="*70)

# Test route: Times Square to JFK Airport
pickup_lat = 40.7580
pickup_lng = -73.9855
dropoff_lat = 40.6413
dropoff_lng = -73.7781

print(f"\nRoute: Times Square → JFK Airport")
print(f"Pickup:  ({pickup_lat}, {pickup_lng})")
print(f"Dropoff: ({dropoff_lat}, {dropoff_lng})")

# Test Uber
print(f"\n{'='*70}")
print("UBER ESTIMATES")
print(f"{'='*70}")

uber_client = MockUberClient()
uber_estimates = uber_client.get_price_estimates(
    pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
)

for est in uber_estimates:
    surge_info = ""
    if est.surge_multiplier and est.surge_multiplier > 1.0:
        surge_info = f" 🔥 {est.surge_multiplier:.1f}x surge"
    
    print(f"\n{est.vehicle_type}:")
    print(f"  Price:    ${est.price_low:.2f} - ${est.price_high:.2f}{surge_info}")
    print(f"  Duration: {est.duration_minutes} minutes")
    print(f"  Distance: {est.distance_miles:.2f} miles")
    print(f"  ETA:      {est.pickup_eta_minutes} minutes")

# Test Lyft
print(f"\n{'='*70}")
print("LYFT ESTIMATES")
print(f"{'='*70}")

lyft_client = MockLyftClient()
lyft_estimates = lyft_client.get_price_estimates(
    pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
)

for est in lyft_estimates:
    surge_info = ""
    if est.surge_multiplier and est.surge_multiplier > 1.0:
        surge_info = f" 🔥 {est.surge_multiplier:.1f}x primetime"
    
    print(f"\n{est.vehicle_type}:")
    print(f"  Price:    ${est.price_low:.2f} - ${est.price_high:.2f}{surge_info}")
    print(f"  Duration: {est.duration_minutes} minutes")
    print(f"  Distance: {est.distance_miles:.2f} miles")
    print(f"  ETA:      {est.pickup_eta_minutes} minutes")

# Compare
print(f"\n{'='*70}")
print("QUICK COMPARISON")
print(f"{'='*70}")

uber_x = next(e for e in uber_estimates if "X" in e.vehicle_type and "XL" not in e.vehicle_type)
lyft_standard = next(e for e in lyft_estimates if e.vehicle_type == "Lyft")

print(f"\nStandard Ride:")
print(f"  Uber:  ${uber_x.price_estimate:.2f}")
print(f"  Lyft:  ${lyft_standard.price_estimate:.2f}")

if uber_x.price_estimate < lyft_standard.price_estimate:
    savings = lyft_standard.price_estimate - uber_x.price_estimate
    print(f"  → Uber is ${savings:.2f} cheaper")
else:
    savings = uber_x.price_estimate - lyft_standard.price_estimate
    print(f"  → Lyft is ${savings:.2f} cheaper")

print(f"\n{'='*70}")
print("✅ All mock clients working!")
print(f"{'='*70}")