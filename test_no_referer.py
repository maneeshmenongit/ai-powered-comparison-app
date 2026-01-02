"""Test Google Places API without referer header."""

import os
import requests
import json

# Load .env manually
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def test_without_referer():
    """Test Google Places API without referer header (like Railway backend)."""
    print("=" * 70)
    print("TESTING WITHOUT REFERER (simulating Railway backend)")
    print("=" * 70)

    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}\n")

    url = "https://places.googleapis.com/v1/places:searchText"

    # Headers WITHOUT Referer (like backend requests)
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.photos"
    }

    payload = {
        "textQuery": "Italian food near Times Square, NYC",
        "locationBias": {
            "circle": {
                "center": {"latitude": 40.758896, "longitude": -73.985130},
                "radius": 8046.72
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print(f"Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"\n❌ ERROR:")
        print(response.text)
        try:
            error_data = response.json()
            print("\nParsed error:")
            print(json.dumps(error_data, indent=2))
        except:
            pass
    else:
        print("✓ Success!\n")
        data = response.json()
        places = data.get('places', [])
        print(f"Found {len(places)} places")
        if places:
            print(f"First place: {places[0].get('displayName', {}).get('text')}")
            print(f"Photos: {len(places[0].get('photos', []))} photos")

if __name__ == "__main__":
    test_without_referer()
