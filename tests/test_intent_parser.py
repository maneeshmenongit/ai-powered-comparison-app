#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'src')

from domains.rideshare.intent_parser import RideShareIntentParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Check OpenAI key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Set it in your .env file or export it")
        sys.exit(1)

    # Initialize parser
    parser = RideShareIntentParser()

    # Test queries
    test_cases = [
    {
        "query": "Get me from Times Square to JFK Airport",
        "location": "New York",
        "expected": "Should parse Times Square as origin, JFK as destination"
    },
    {
        "query": "Compare Uber and Lyft from Central Park to LaGuardia",
        "location": "New York",
        "expected": "Should extract both providers"
    },
    {
        "query": "I need a cheap ride downtown",
        "location": "New York, staying at The Plaza Hotel",
        "expected": "Should infer origin from location, downtown as destination"
    },
    {
        "query": "Cheapest way to get to Brooklyn Bridge",
        "location": "Times Square, New York",
        "expected": "Should infer origin, Brooklyn Bridge as destination"
    },
    {
        "query": "Get me a big car to the airport for 4 people",
        "location": "Manhattan",
        "expected": "Should extract passengers=4, vehicle_type=xl"
    }
    ]

    print("="*70)
    print("TESTING INTENT PARSER")
    print("="*70)

    success_count = 0
    total_count = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{total_count}")
        print(f"{'='*70}")
        print(f"Query: \"{test['query']}\"")
        print(f"Location: {test['location']}")
        print(f"Expected: {test['expected']}")
        print()

        try:
            result = parser.parse_query(test['query'], user_location=test['location'])

            print("✅ PARSED SUCCESSFULLY:")
            print(f"  Origin:      {result.origin}")
            print(f"  Destination: {result.destination}")
            print(f"  Providers:   {result.providers}")
            print(f"  Vehicle:     {result.vehicle_type}")
            print(f"  Passengers:  {result.passengers}")
            print(f"  When:        {result.when}")

            success_count += 1

        except ValueError as e:
            print(f"⚠️  VALIDATION ERROR: {e}")
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")

    print(f"\n{'='*70}")
    print(f"RESULTS: {success_count}/{total_count} tests passed")
    print(f"{'='*70}")

    if success_count == total_count:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"⚠️  {total_count - success_count} tests failed")
        sys.exit(1)