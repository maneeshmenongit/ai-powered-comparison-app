#!/usr/bin/env python3
"""
Database Initialization Script

Creates all tables in the database based on SQLAlchemy models.
Run this script to set up a new database (dev, staging, or production).

Usage:
    ./venv/bin/python init_database.py

The script will use the DATABASE_URL from your environment (.env, .env.local, or .env.staging).
"""

import os
import sys
from dotenv import load_dotenv
from api.database import Base, engine
from api.models import User, SavedRestaurant

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database with all tables."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Make sure you have .env, .env.local, or .env.staging configured")
        return False

    print("\n" + "="*70)
    print(" DATABASE INITIALIZATION")
    print("="*70 + "\n")

    # Mask password in URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        user_pass = parts[0].split('://')[-1]
        if ':' in user_pass:
            user, _ = user_pass.split(':', 1)
            display_url = display_url.replace(user_pass, f"{user}:****")

    print(f"📍 Database: {display_url}")
    print()

    try:
        # Create all tables
        print("📝 Creating tables...")
        Base.metadata.create_all(bind=engine)

        print("✅ Created table: users")
        print("   - id: UUID (primary key)")
        print("   - device_id: VARCHAR(255) (unique, nullable)")
        print("   - username: VARCHAR(80) (unique, nullable)")
        print("   - email: VARCHAR(120) (unique, nullable)")
        print("   - password_hash: VARCHAR(255)")
        print("   - is_guest: BOOLEAN")
        print("   - is_premium: BOOLEAN")
        print("   - created_at: TIMESTAMP")
        print()

        print("✅ Created table: saved_restaurants")
        print("   - id: UUID (primary key)")
        print("   - user_id: UUID (foreign key -> users.id)")
        print("   - restaurant_id: VARCHAR(255)")
        print("   - restaurant_data: JSONB")
        print("   - created_at: TIMESTAMP")
        print()

        print("="*70)
        print(" ✅ DATABASE INITIALIZATION COMPLETE!")
        print("="*70)
        print()
        print("Tables created successfully!")
        print("You can now start your application.")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check which environment we're initializing
    if os.path.exists('.env.local'):
        print("🔵 Using .env.local (development)")
        load_dotenv('.env.local', override=True)
    elif os.path.exists('.env.staging'):
        print("🟡 Using .env.staging (staging)")
        load_dotenv('.env.staging', override=True)
    else:
        print("🔴 Using .env (production)")
        load_dotenv('.env')

    success = init_database()
    sys.exit(0 if success else 1)
