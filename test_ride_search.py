"""Test ride search from query"""
import requests
import json

print("=" * 70)
print("TESTING RIDE SEARCH QUERY")
print("=" * 70)

# Test with properly formatted destination
print("\nTest: Ride to Times Square, NYC")
print("-" * 70)

response = requests.post(
    'http://localhost:5001/api/rides',
    json={
        "origin": "Times Square, NYC",
        "destination": "Times Square, NYC"  # Properly capitalized with location
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ Success: {data.get('success')}")
    rides = data.get('data', {}).get('data', {}).get('rides', [])
    print(f"✓ Rides found: {len(rides)}")
    for ride in rides[:3]:
        print(f"  - {ride['provider']} {ride['vehicle_type']}: ${ride['price_estimate']}")
else:
    print(f"❌ Error: {response.text}")
