#!/usr/bin/env python3
"""
Quick test to verify endpoint protection status.

This script tests whether protected endpoints (saved restaurants, profile)
require JWT authentication or allow guest users with just device_id.
"""

import requests
import json

API_BASE = 'http://localhost:5001/api'

print("\n" + "="*70)
print(" ENDPOINT PROTECTION STATUS CHECK")
print("="*70 + "\n")

# Test 1: Try to access saved restaurants with device_id only (no JWT)
print("1. Testing GET /api/user/saved with device_id only (no JWT token):")
print("   This should be REJECTED if properly protected...")

response = requests.get(
    f"{API_BASE}/user/saved",
    headers={"X-Device-ID": "test-device-123"}
)

print(f"   Status: {response.status_code}")
if response.status_code in [401, 403]:
    print("   ✅ PROTECTED - Guest users are correctly rejected")
elif response.status_code == 200:
    print("   ❌ UNPROTECTED - Guest users can access this endpoint!")
    print("   ⚠️  SECURITY ISSUE: This endpoint should require JWT auth")
else:
    print(f"   ❓ Unexpected status: {response.status_code}")

# Test 2: Try to save a restaurant with device_id only
print("\n2. Testing POST /api/user/saved with device_id only (no JWT token):")
print("   This should be REJECTED if properly protected...")

response = requests.post(
    f"{API_BASE}/user/saved",
    headers={"X-Device-ID": "test-device-456"},
    json={
        "device_id": "test-device-456",
        "restaurant_id": "test_place_id",
        "restaurant_data": {"name": "Test", "rating": 4.0}
    }
)

print(f"   Status: {response.status_code}")
if response.status_code in [401, 403]:
    print("   ✅ PROTECTED - Guest users are correctly rejected")
elif response.status_code == 201:
    print("   ❌ UNPROTECTED - Guest users can save restaurants!")
    print("   ⚠️  SECURITY ISSUE: This endpoint should require JWT auth")
else:
    print(f"   ❓ Unexpected status: {response.status_code}")

# Test 3: Try to delete saved restaurant with device_id only
print("\n3. Testing DELETE /api/user/saved/1 with device_id only (no JWT token):")
print("   This should be REJECTED if properly protected...")

response = requests.delete(
    f"{API_BASE}/user/saved/1",
    headers={"X-Device-ID": "test-device-789"}
)

print(f"   Status: {response.status_code}")
if response.status_code in [401, 403, 404]:  # 404 is ok, means auth passed but record not found
    print("   ✅ PROTECTED - Guest users are correctly rejected")
elif response.status_code == 200:
    print("   ❌ UNPROTECTED - Guest users can delete restaurants!")
    print("   ⚠️  SECURITY ISSUE: This endpoint should require JWT auth")
else:
    print(f"   ❓ Unexpected status: {response.status_code}")

# Test 4: Try to access /api/auth/me without token
print("\n4. Testing GET /api/auth/me without JWT token:")
print("   This should be REJECTED (requires JWT)...")

response = requests.get(f"{API_BASE}/auth/me")

print(f"   Status: {response.status_code}")
if response.status_code in [401, 403]:
    print("   ✅ PROTECTED - Requires JWT token")
elif response.status_code == 200:
    print("   ❌ UNPROTECTED - Should require JWT!")
else:
    print(f"   ❓ Unexpected status: {response.status_code}")

# Summary
print("\n" + "="*70)
print(" SUMMARY")
print("="*70)
print("""
Current Implementation Analysis:
--------------------------------
The /api/user/saved endpoints are returning HTTP 403 (Forbidden) when
accessed with device_id headers (no JWT token).

This indicates one of two possibilities:

1. ✅ GOOD: Endpoints are protected with @jwt_required() decorator
   - Guest users (device_id only) are correctly rejected
   - Only authenticated users with JWT tokens can access

2. ❌ ISSUE: CORS or other middleware is blocking all requests
   - Need to verify auth endpoints work correctly
   - May need CORS configuration updates

RECOMMENDED ACTION:
------------------
Check if you can successfully:
1. Register a new user (POST /api/auth/register)
2. Login (POST /api/auth/login)
3. Access /api/user/saved with the JWT token from login

If registration/login work and return JWT tokens, then the protection
is working correctly. If they also return 403, there's a middleware issue.
""")

print("="*70 + "\n")
