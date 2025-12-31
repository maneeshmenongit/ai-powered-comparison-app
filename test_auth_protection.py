#!/usr/bin/env python3
"""
Test script to verify authentication protection on endpoints.

Tests:
1. Guest users (device_id only) should NOT access protected endpoints
2. Authenticated users (JWT token) SHOULD access protected endpoints
3. Saved restaurants should be user-specific
"""

import requests
import json

API_BASE = 'http://localhost:5000/api'

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test(test_name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")

def test_guest_access():
    """Test 1: Guest users should NOT access protected endpoints."""
    print_section("TEST 1: Guest User Access (Should be RESTRICTED)")

    guest_device_id = "test-guest-device-123"

    # Try to save restaurant as guest (device_id only, no JWT)
    print("\n1.1 - Trying to save restaurant with device_id only (no JWT)...")
    response = requests.post(
        f"{API_BASE}/user/saved",
        headers={"X-Device-ID": guest_device_id},
        json={
            "device_id": guest_device_id,
            "restaurant_id": "test_place_123",
            "restaurant_data": {"name": "Test Restaurant", "rating": 4.5}
        }
    )
    print(f"     Status: {response.status_code}")
    try:
        print(f"     Response: {response.json()}")
    except:
        print(f"     Response: {response.text[:100]}")

    # Should FAIL (401/403) if properly protected
    save_rejected = response.status_code in [401, 403]
    print_test("Guest SAVE should be rejected", save_rejected)

    # Try to get saved restaurants as guest
    print("\n1.2 - Trying to get saved restaurants with device_id only (no JWT)...")
    response = requests.get(
        f"{API_BASE}/user/saved",
        headers={"X-Device-ID": guest_device_id}
    )
    print(f"     Status: {response.status_code}")
    try:
        print(f"     Response: {response.json()}")
    except:
        print(f"     Response: {response.text[:100]}")

    # Should FAIL (401/403) if properly protected
    get_rejected = response.status_code in [401, 403]
    print_test("Guest GET should be rejected", get_rejected)

    return save_rejected and get_rejected

def test_authenticated_access():
    """Test 2: Authenticated users SHOULD access protected endpoints."""
    print_section("TEST 2: Authenticated User Access (Should be ALLOWED)")

    # Register a new user
    print("\n2.1 - Registering test user...")
    register_data = {
        "username": "testuser_auth",
        "email": "testuser_auth@example.com",
        "password": "testpassword123"
    }

    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    print(f"     Status: {response.status_code}")
    print(f"     Response: {response.json()}")

    if response.status_code != 201:
        # User might already exist, try login
        print("\n2.2 - User exists, logging in instead...")
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "email": register_data["email"],
                "password": register_data["password"]
            }
        )
        print(f"     Status: {response.status_code}")

    if response.status_code not in [200, 201]:
        print("     ❌ Failed to authenticate user")
        return False

    token = response.json()['access_token']
    print(f"     ✅ Got JWT token: {token[:20]}...")

    # Try to save restaurant with JWT token
    print("\n2.3 - Trying to save restaurant with JWT token...")
    response = requests.post(
        f"{API_BASE}/user/saved",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "restaurant_id": "test_place_456",
            "restaurant_data": {"name": "Authenticated Restaurant", "rating": 5.0}
        }
    )
    print(f"     Status: {response.status_code}")
    print(f"     Response: {response.json()}")

    # Should PASS (201 Created) if properly protected
    save_passed = response.status_code == 201
    print_test("Authenticated SAVE should succeed", save_passed)

    # Try to get saved restaurants with JWT token
    print("\n2.4 - Trying to get saved restaurants with JWT token...")
    response = requests.get(
        f"{API_BASE}/user/saved",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"     Status: {response.status_code}")
    print(f"     Response: {response.json()}")

    # Should PASS (200 OK) if properly protected
    get_passed = response.status_code == 200
    print_test("Authenticated GET should succeed", get_passed)

    return save_passed and get_passed

def test_no_auth_rejection():
    """Test 3: No authentication should be rejected."""
    print_section("TEST 3: No Authentication (Should be REJECTED)")

    # Try to save without any auth
    print("\n3.1 - Trying to save restaurant without any authentication...")
    response = requests.post(
        f"{API_BASE}/user/saved",
        json={
            "restaurant_id": "test_place_789",
            "restaurant_data": {"name": "No Auth Restaurant", "rating": 3.0}
        }
    )
    print(f"     Status: {response.status_code}")
    try:
        print(f"     Response: {response.json()}")
    except:
        print(f"     Response: {response.text[:100]}")

    # Should FAIL (401/403)
    save_rejected = response.status_code in [401, 403]
    print_test("No auth SAVE should be rejected", save_rejected)

    # Try to get without any auth
    print("\n3.2 - Trying to get saved restaurants without any authentication...")
    response = requests.get(f"{API_BASE}/user/saved")
    print(f"     Status: {response.status_code}")
    try:
        print(f"     Response: {response.json()}")
    except:
        print(f"     Response: {response.text[:100]}")

    # Should FAIL (401/403)
    get_rejected = response.status_code in [401, 403]
    print_test("No auth GET should be rejected", get_rejected)

    return save_rejected and get_rejected

def test_current_behavior():
    """Test current behavior (likely allows device_id)."""
    print_section("CURRENT BEHAVIOR TEST")

    guest_device_id = "current-test-device-456"

    print("\nCurrent implementation check:")
    print("Attempting to save with device_id (no JWT)...")

    response = requests.post(
        f"{API_BASE}/user/saved",
        headers={"X-Device-ID": guest_device_id},
        json={
            "device_id": guest_device_id,
            "restaurant_id": "current_test_place",
            "restaurant_data": {"name": "Current Test Restaurant", "rating": 4.0}
        }
    )

    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text[:200]}")

    if response.status_code == 201:
        print("\n⚠️  WARNING: Saved endpoints are currently UNPROTECTED")
        print("   Guest users (device_id only) can access protected endpoints")
        print("   This is a security issue!")
        return False
    elif response.status_code in [401, 403]:
        print("\n✅ GOOD: Saved endpoints are properly protected")
        print(f"   Guest users are correctly rejected (HTTP {response.status_code})")
        return True
    else:
        print(f"\n❓ UNEXPECTED: Got status {response.status_code}")
        return False

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AUTH PROTECTION TEST SUITE" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Test current behavior first
        current_protected = test_current_behavior()

        # Run all tests
        guest_blocked = test_guest_access()
        auth_allowed = test_authenticated_access()
        no_auth_blocked = test_no_auth_rejection()

        # Summary
        print_section("TEST SUMMARY")
        print(f"\n✅ Guest users blocked: {guest_blocked}")
        print(f"✅ Authenticated users allowed: {auth_allowed}")
        print(f"✅ No auth blocked: {no_auth_blocked}")
        print(f"\n{'✅ ALL TESTS PASSED' if all([guest_blocked, auth_allowed, no_auth_blocked]) else '❌ SOME TESTS FAILED'}")

        if not current_protected:
            print("\n" + "⚠️  " * 20)
            print("SECURITY ISSUE DETECTED:")
            print("The /api/user/saved endpoints are NOT properly protected!")
            print("Guest users can currently save/retrieve restaurants.")
            print("\nRECOMMENDATION: Add @jwt_required() decorator to:")
            print("  - /api/user/saved POST")
            print("  - /api/user/saved GET")
            print("  - /api/user/saved/<id> DELETE")
            print("⚠️  " * 20)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API")
        print("Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
