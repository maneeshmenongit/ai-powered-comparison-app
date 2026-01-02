"""Test local backend API"""
import requests
import json

response = requests.post(
    'http://localhost:5001/api/restaurants',
    json={
        "location": "Times Square, NYC",
        "query": "Italian",
        "filter_category": "Food",
        "priority": "rating",
        "use_ai": False
    }
)

data = response.json()
results = data['data']['data']['results']

print(f"Total: {len(results)} results")

providers = {}
for r in results:
    providers[r['provider']] = providers.get(r['provider'], 0) + 1

print(f"By provider: {providers}")

google_results = [r for r in results if r['provider'] == 'google_places']
print(f"\nGoogle Places: {len(google_results)} results")

for r in google_results[:5]:
    print(f"  - {r['name']}: {len(r.get('photos', []))} photos, image_url={bool(r.get('image_url'))}")
