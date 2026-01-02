#!/usr/bin/env python3
"""Test favorites API endpoints."""

import requests
import json
import uuid

# Base URL
BASE_URL = "http://localhost:5001"

# Generate a test device_id
device_id = str(uuid.uuid4())
print(f"Using device_id: {device_id}")

# Test restaurant data
test_restaurant = {
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "name": "Test Restaurant",
    "rating": 4.5,
    "price_level": 2,
    "vicinity": "123 Test St, Test City"
}

print("\n" + "="*60)
print("Test 1: Save a restaurant")
print("="*60)

response = requests.post(
    f"{BASE_URL}/api/user/saved",
    json={
        "device_id": device_id,
        "restaurant_id": test_restaurant["place_id"],
        "restaurant_data": test_restaurant
    },
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code != 201:
    print("❌ Failed to save restaurant")
    exit(1)

saved_id = response.json()["data"]["id"]
print(f"✅ Restaurant saved with ID: {saved_id}")

print("\n" + "="*60)
print("Test 2: Try to save the same restaurant again (should fail)")
print("="*60)

response = requests.post(
    f"{BASE_URL}/api/user/saved",
    json={
        "device_id": device_id,
        "restaurant_id": test_restaurant["place_id"],
        "restaurant_data": test_restaurant
    },
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code != 409:
    print("❌ Should have returned 409 Conflict")
    exit(1)

print("✅ Correctly prevented duplicate save")

print("\n" + "="*60)
print("Test 3: Get saved restaurants")
print("="*60)

response = requests.get(
    f"{BASE_URL}/api/user/saved",
    headers={"X-Device-ID": device_id}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code != 200:
    print("❌ Failed to get saved restaurants")
    exit(1)

saved_count = len(response.json()["data"])
print(f"✅ Retrieved {saved_count} saved restaurant(s)")

print("\n" + "="*60)
print("Test 4: Delete saved restaurant")
print("="*60)

response = requests.delete(
    f"{BASE_URL}/api/user/saved/{saved_id}",
    headers={"X-Device-ID": device_id}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code != 200:
    print("❌ Failed to delete saved restaurant")
    exit(1)

print("✅ Restaurant deleted successfully")

print("\n" + "="*60)
print("Test 5: Verify empty list after deletion")
print("="*60)

response = requests.get(
    f"{BASE_URL}/api/user/saved",
    headers={"X-Device-ID": device_id}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

saved_count = len(response.json()["data"])
if saved_count != 0:
    print(f"❌ Should have 0 saved restaurants, found {saved_count}")
    exit(1)

print("✅ Saved list is empty as expected")

print("\n" + "="*60)
print("✅ All tests passed!")
print("="*60)
