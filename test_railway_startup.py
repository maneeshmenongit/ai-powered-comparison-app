#!/usr/bin/env python3
"""
Test Railway startup environment.
Simulates Railway's environment to test if the app can start.
"""

import os
import sys

# Simulate Railway environment (env vars set, no .env files)
os.environ['DATABASE_URL'] = 'postgresql://postgres:test@localhost:5432/test'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
os.environ['GOOGLE_PLACES_API_KEY'] = 'test-key'
os.environ['PORT'] = '5001'

print("=" * 70)
print(" RAILWAY STARTUP SIMULATION TEST")
print("=" * 70)
print()

print("Environment:")
print(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')}")
print(f"  JWT_SECRET_KEY: {os.environ.get('JWT_SECRET_KEY', 'NOT SET')}")
print(f"  GOOGLE_PLACES_API_KEY: {os.environ.get('GOOGLE_PLACES_API_KEY', 'NOT SET')}")
print()

print("Testing imports...")
try:
    # Test core imports
    print("  - Importing Flask...")
    from flask import Flask

    print("  - Importing api.database...")
    from api.database import SessionLocal, Base

    print("  - Importing api.models...")
    from api.models import User, SavedRestaurant

    print("  - Importing api.cost_tracker...")
    from api.cost_tracker import CostTracker

    print("  - Importing api.app...")
    from api.app import app

    print()
    print("✅ ALL IMPORTS SUCCESSFUL")
    print()

    # Test that app is configured
    print("Testing Flask app configuration...")
    print(f"  App name: {app.name}")
    print(f"  JWT configured: {'JWT_SECRET_KEY' in app.config}")
    print(f"  Routes registered: {len(app.url_map._rules)}")
    print()

    # List all routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        if not str(rule).startswith('/static'):
            print(f"  {rule.methods} {rule}")

    print()
    print("=" * 70)
    print(" ✅ RAILWAY STARTUP TEST PASSED")
    print("=" * 70)
    sys.exit(0)

except Exception as e:
    print()
    print("=" * 70)
    print(" ❌ RAILWAY STARTUP TEST FAILED")
    print("=" * 70)
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
