"""Test Railway deployment with Google Places API"""
import requests
import json

print("=" * 70)
print("TESTING RAILWAY DEPLOYMENT")
print("=" * 70)

# Test restaurant search
print("\nTesting restaurant search...")
print("-" * 70)

response = requests.post(
    'https://hopwise-api.up.railway.app/api/restaurants',
    json={
        "location": "Times Square, NYC",
        "query": "Italian",
        "filter_category": "Food",
        "priority": "rating",
        "use_ai": False
    }
)

if response.status_code != 200:
    print(f"❌ Request failed with status {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

data = response.json()
results = data['data']['data']['results']

print(f"✓ Request successful")
print(f"  Total: {len(results)} results")

providers = {}
for r in results:
    providers[r['provider']] = providers.get(r['provider'], 0) + 1

print(f"  By provider: {providers}")

google_results = [r for r in results if r['provider'] == 'google_places']
print(f"\n✓ Google Places: {len(google_results)} results")

for r in google_results[:3]:
    print(f"  - {r['name']}: {len(r.get('photos', []))} photos, image_url={bool(r.get('image_url'))}")
    if r.get('image_url'):
        print(f"    Image: {r['image_url'][:80]}...")

print("\n" + "=" * 70)
print("DEPLOYMENT TEST COMPLETE")
print("=" * 70)
