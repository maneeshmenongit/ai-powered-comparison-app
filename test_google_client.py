"""Test GooglePlacesClient directly"""
import sys
sys.path.insert(0, 'src')

import os

# Load .env
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from domains.restaurants.api_clients.google_places_client import GooglePlacesClient

print("=" * 70)
print("TESTING GooglePlacesClient CLASS")
print("=" * 70)

# Initialize client
try:
    client = GooglePlacesClient()
    print(f"✓ Client initialized")
    print(f"  API Key (last 4): {client.api_key[-4:]}")
    print()
except Exception as e:
    print(f"❌ Client initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test search
print("Testing search for Italian restaurants near Times Square...")
print("-" * 70)

try:
    results = client.search(
        cuisine="Italian",
        latitude=40.758896,
        longitude=-73.985130,
        limit=5
    )

    print(f"✓ Search completed")
    print(f"  Results: {len(results)} restaurants")
    print()

    for i, r in enumerate(results[:3], 1):
        print(f"{i}. {r.name}")
        print(f"   Provider: {r.provider}")
        print(f"   Rating: {r.rating}")
        print(f"   Photos: {len(r.photos)}")
        print(f"   Image URL: {'Yes' if r.image_url else 'No'}")
        print()

except Exception as e:
    print(f"❌ Search failed: {e}")
    import traceback
    traceback.print_exc()
