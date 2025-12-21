"""Debug Uber API scopes and authentication."""

import sys
sys.path.insert(0, 'src')

import os
import requests
from dotenv import load_dotenv
load_dotenv(override=True)

print('=' * 70)
print('UBER API SCOPE DIAGNOSTIC')
print('=' * 70)

client_id = os.getenv('UBER_CLIENT_ID')
client_secret = os.getenv('UBER_CLIENT_SECRET')

print(f'\n📋 Credentials Loaded:')
print(f'   Client ID: {client_id}')
print(f'   Client Secret: {"✓ Present" if client_secret else "✗ Missing"}\n')

# Try different scopes
scopes_to_test = [
    "",  # No scope
    "request.read",  # Current scope
    "profile",  # User profile
    "history",  # Trip history
]

print('🔍 Testing different OAuth scopes...\n')

for scope in scopes_to_test:
    print(f'Testing scope: "{scope if scope else "(no scope)"}"')
    print('─' * 70)

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    if scope:
        payload["scope"] = scope

    try:
        response = requests.post(
            "https://login.uber.com/oauth/v2/token",
            data=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f'✅ SUCCESS!')
            print(f'   Access token: {data["access_token"][:20]}...')
            print(f'   Expires in: {data.get("expires_in", "N/A")} seconds')
            print(f'   Token type: {data.get("token_type", "N/A")}')
            if 'scope' in data:
                print(f'   Granted scope: {data["scope"]}')
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error_description", error_data.get("error", response.text))
            print(f'❌ FAILED: {response.status_code}')
            print(f'   Error: {error_msg}')

    except Exception as e:
        print(f'❌ Exception: {e}')

    print()

print('=' * 70)
print('\n💡 RECOMMENDATION:')
print('   1. Go to https://developer.uber.com/dashboard')
print('   2. Select your application')
print('   3. Go to "Settings" → "Scopes"')
print('   4. Enable the required scopes for your app')
print('   5. Common scopes needed:')
print('      • For price estimates: Usually no scope needed for server-to-server')
print('      • For user data: profile, history, etc.')
print('\n   6. Try using no scope (client_credentials only) for price estimates')
print('=' * 70)
