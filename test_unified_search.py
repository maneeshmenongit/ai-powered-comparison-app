"""Test unified search endpoint."""

import requests
import json

API_URL = "http://localhost:5001/api"

test_queries = [
    {
        "query": "need a ride to times square",
        "location": "Central Park, NYC",
        "expected_domain": "rideshare"
    },
    {
        "query": "find me Italian food",
        "location": "Times Square, NYC",
        "expected_domain": "restaurants"
    },
    {
        "query": "uber to JFK airport",
        "location": "Manhattan, NYC",
        "expected_domain": "rideshare"
    },
    {
        "query": "best pizza near me",
        "location": "Brooklyn, NYC",
        "expected_domain": "restaurants"
    }
]

def test_unified_search():
    """Test the /api/search endpoint."""
    print("=" * 70)
    print("TESTING UNIFIED SEARCH ENDPOINT")
    print("=" * 70)

    for test in test_queries:
        print(f"\nTest Query: '{test['query']}'")
        print(f"Location: '{test['location']}'")
        print(f"Expected Domain: {test['expected_domain']}")
        print("-" * 70)

        try:
            response = requests.post(
                f"{API_URL}/search",
                json={
                    "query": test["query"],
                    "location": test["location"]
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                actual_domain = data.get('domain')
                success = data.get('success')

                print(f"✓ Status: {response.status_code}")
                print(f"✓ Success: {success}")
                print(f"✓ Routed to: {actual_domain}")

                if actual_domain == test['expected_domain']:
                    print(f"✅ PASS - Correctly routed to {actual_domain}")
                else:
                    print(f"❌ FAIL - Expected {test['expected_domain']}, got {actual_domain}")

                # Show query parsing for rideshare
                if 'query_parsed' in data:
                    print(f"  Parsed: {data['query_parsed']}")

            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")

        except requests.exceptions.ConnectionError:
            print("❌ ERROR: Could not connect to API (is the server running?)")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_unified_search()
