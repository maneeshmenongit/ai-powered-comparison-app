#!/usr/bin/env python3
"""Debug Uber API connection."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_uber_api():
    """Debug Uber API authentication and response."""
    print("=" * 70)
    print("UBER API DEBUG")
    print("=" * 70)

    server_token = os.getenv("UBER_SERVER_TOKEN")
    app_id = os.getenv("UBER_APPLICATION_ID")

    print(f"\n✓ Server Token: {server_token[:10]}...{server_token[-4:]}")
    if app_id:
        print(f"✓ Application ID: {app_id}")

    # Test 1: Price Estimates endpoint
    print("\n" + "=" * 70)
    print("TEST 1: Price Estimates API")
    print("=" * 70)

    url = "https://api.uber.com/v1.2/estimates/price"
    headers = {
        "Authorization": f"Token {server_token}",
        "Accept-Language": "en_US",
        "Content-Type": "application/json"
    }
    params = {
        "start_latitude": 40.7580,
        "start_longitude": -73.9855,
        "end_latitude": 40.6413,
        "end_longitude": -73.7781
    }

    print(f"\nURL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")

    try:
        print("\n⏳ Making API request...")
        response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"\n✓ Response Status: {response.status_code}")
        print(f"✓ Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        print(f"\n✓ Response Body:")
        print(response.text)

        if response.status_code == 401:
            print("\n❌ AUTHENTICATION FAILED (401)")
            print("\nPossible reasons:")
            print("1. Invalid or expired server token")
            print("2. Server token format is incorrect")
            print("3. App doesn't have Ride Request scope enabled")
            print("4. Uber changed their API authentication")
            print("\nNext steps:")
            print("- Verify token in Uber Developer Dashboard")
            print("- Check if token has 'Request' scope")
            print("- Try regenerating the server token")
            print("- Check if Uber API v1.2 is still active")

        elif response.status_code == 200:
            print("\n✅ SUCCESS! API authentication working")
            data = response.json()
            print(f"\nReceived {len(data.get('prices', []))} price estimates")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")

    # Test 2: Try alternative authentication method
    print("\n" + "=" * 70)
    print("TEST 2: Alternative Auth Header Format")
    print("=" * 70)

    headers_alt = {
        "Authorization": f"Bearer {server_token}",
        "Accept-Language": "en_US",
        "Content-Type": "application/json"
    }

    print(f"Trying Bearer token instead of Token...")

    try:
        response = requests.get(url, headers=headers_alt, params=params, timeout=10)
        print(f"\n✓ Response Status: {response.status_code}")
        print(f"✓ Response: {response.text[:200]}...")

        if response.status_code == 200:
            print("\n✅ Bearer token works!")
        else:
            print("\n✗ Bearer token also failed")

    except Exception as e:
        print(f"\n❌ Request failed: {e}")

    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    debug_uber_api()
