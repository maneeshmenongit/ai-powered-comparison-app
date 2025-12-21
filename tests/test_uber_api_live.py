"""Test real Uber API with OAuth credentials."""

import sys
sys.path.insert(0, 'src')

import os
from dotenv import load_dotenv
load_dotenv(override=True)

from domains.rideshare.api_clients.uber_client import UberClient

print('=== Uber API Live Test ===\n')

# Show credentials being used
client_id = os.getenv('UBER_CLIENT_ID')
client_secret = os.getenv('UBER_CLIENT_SECRET')

print(f'📋 Credentials:')
print(f'   Client ID: {client_id}')
print(f'   Client Secret: {client_secret[:10]}...{client_secret[-10:] if client_secret else "None"}')
print()

try:
    # Initialize client
    print('🔧 Initializing Uber client...')
    client = UberClient()
    print(f'✅ Client initialized with {client.auth_type} authentication\n')

    # Get OAuth token
    print('🔑 Acquiring OAuth access token...')
    client._get_access_token()
    print(f'✅ Access token acquired')
    print(f'   Expires at: {client.token_expiry}\n')

    # Test price estimates API
    print('📍 Testing price estimates API...')
    print('   Route: Times Square, NYC → JFK Airport, NYC')
    print('   Coords: (40.7580, -73.9855) → (40.6413, -73.7781)\n')

    estimates = client.get_price_estimates(
        pickup_lat=40.7580,
        pickup_lng=-73.9855,
        dropoff_lat=40.6413,
        dropoff_lng=-73.7781
    )

    print(f'✅ Received {len(estimates)} estimates from Uber\n')

    # Display results
    print('📊 Uber Price Estimates:')
    print('─' * 70)
    for est in estimates:
        surge_info = f' 🔥 {est.surge_multiplier}x surge' if est.surge_multiplier > 1.0 else ''
        print(f'  {est.vehicle_type:15} ${est.price_estimate:6.2f}  '
              f'(${est.price_low:.2f}-${est.price_high:.2f}){surge_info}')
        print(f'  {"":15} ETA: {est.pickup_eta_minutes} min | '
              f'Trip: {est.duration_minutes} min | '
              f'Distance: {est.distance_miles:.1f} mi')
        print()

    print('=' * 70)
    print('🎉 UBER API TEST SUCCESSFUL!')
    print('=' * 70)

except ValueError as e:
    print(f'\n❌ Configuration Error: {e}')
except Exception as e:
    print(f'\n❌ API Error: {e}')
    print(f'\nError type: {type(e).__name__}')

    import traceback
    print(f'\nFull traceback:')
    print(traceback.format_exc())
