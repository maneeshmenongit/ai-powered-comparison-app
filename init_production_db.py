#!/usr/bin/env python3
"""
Initialize production database tables
Run this with: railway run python init_production_db.py
"""
import sys
import os

# Add parent directory to path for api module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import init_db

print("=" * 60)
print("INITIALIZING PRODUCTION DATABASE")
print("=" * 60)
print()

try:
    init_db()
    print()
    print("=" * 60)
    print("✅ SUCCESS: Production database tables created!")
    print("=" * 60)
except Exception as e:
    print()
    print("=" * 60)
    print(f"❌ ERROR: {str(e)}")
    print("=" * 60)
    sys.exit(1)
