"""Test Google Places API photos directly."""

import os
import sys
import requests
import json

# Load .env manually
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def test_google_places_photos():
    """Test Google Places API photo functionality."""
    print("=" * 70)
    print("TESTING GOOGLE PLACES API DIRECTLY")
    print("=" * 70)

    # Check if API key is set
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ ERROR: GOOGLE_PLACES_API_KEY not found in environment")
        return

    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Test direct API call
    print("Making direct API call to Google Places...")
    print("-" * 70)

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.priceLevel,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.currentOpeningHours,places.photos",
        "Referer": "https://hopwise-api.up.railway.app/"
    }

    payload = {
        "textQuery": "Italian food near Times Square, NYC",
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": 40.758896,
                    "longitude": -73.985130
                },
                "radius": 8046.72  # 5 miles in meters
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()

        if response.status_code != 200:
            print(f"❌ ERROR Response:")
            print(response.text)
            print()

            # Try to parse error
            try:
                error_data = response.json()
                print("Parsed error:")
                print(json.dumps(error_data, indent=2))
            except:
                pass
        else:
            data = response.json()
            places = data.get('places', [])

            print(f"✓ Success! Found {len(places)} places")

            if places:
                first = places[0]
                print(f"\nFirst place:")
                print(f"  Name: {first.get('displayName', {}).get('text', 'N/A')}")
                print(f"  Rating: {first.get('rating', 'N/A')}")
                print(f"  Photos: {len(first.get('photos', []))} photos")

                photos = first.get('photos', [])
                if photos:
                    photo = photos[0]
                    print(f"\n  First photo object:")
                    print(f"    Name: {photo.get('name', 'N/A')}")
                    print(f"    Width: {photo.get('widthPx', 'N/A')}")
                    print(f"    Height: {photo.get('heightPx', 'N/A')}")
                else:
                    print("  ❌ No photos in response")

    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_places_photos()
