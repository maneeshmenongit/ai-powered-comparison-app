#!/usr/bin/env python3
"""Test database setup."""

import os
import sys

# Load .env file
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

sys.path.insert(0, '.')

from api.db_init import initialize_database

if __name__ == '__main__':
    print("Testing database initialization...")
    success = initialize_database()

    if success:
        print("\n✅ Database test passed!")
        sys.exit(0)
    else:
        print("\n❌ Database test failed!")
        sys.exit(1)
