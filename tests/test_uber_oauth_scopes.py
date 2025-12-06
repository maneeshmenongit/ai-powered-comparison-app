#!/usr/bin/env python3
"""Test different OAuth scopes with Uber API."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("UBER_CLIENT_ID") or os.getenv("UBER_CLEINT_ID")
CLIENT_SECRET = os.getenv("UBER_CLIENT_SECRET")
TOKEN_URL = "https://login.uber.com/oauth/v2/token"

print("=" * 70)
print("TESTING UBER OAUTH SCOPES")
print("=" * 70)
print(f"\nClient ID: {CLIENT_ID}")
print(f"Client Secret: {CLIENT_SECRET[:10]}...")

# Try different scopes
scopes_to_try = [
    None,  # No scope
    "",  # Empty scope
    "profile",
    "history",
    "places",
    "ride_widgets",
    "all_trips",
    "request",
    "request.read",
    "delivery",
    "delivery.read",
]

for scope in scopes_to_try:
    print(f"\n{'-' * 70}")
    print(f"Testing scope: {scope if scope else '(none)'}")
    print("-" * 70)

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    if scope:
        payload["scope"] = scope

    try:
        response = requests.post(TOKEN_URL, data=payload, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"Access Token: {data.get('access_token', '')[:20]}...")
            print(f"Token Type: {data.get('token_type')}")
            print(f"Expires In: {data.get('expires_in')} seconds")
            print(f"Scope: {data.get('scope', '(none)')}")
            break  # Found a working scope!
        else:
            data = response.json() if response.text else {}
            error = data.get("error", "unknown")
            error_desc = data.get("error_description", "no description")
            print(f"❌ Error: {error}")
            print(f"Description: {error_desc}")

    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "=" * 70)
print("SCOPE TESTING COMPLETE")
print("=" * 70)
