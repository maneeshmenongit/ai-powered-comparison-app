"""api/db_init.py

Database initialization script.
Runs on startup to create tables if they don't exist.
"""

import os
import sys
from api.database import engine, init_db, Base
from api.models import User, SavedRestaurant, Trip, TripItem


def check_database_configured():
    """Check if DATABASE_URL is configured."""
    database_url = os.getenv('DATABASE_URL', '')

    if not database_url:
        print("⚠️  Warning: DATABASE_URL not configured")
        print("   Favorites feature will not work without a database")
        print("   Set DATABASE_URL in .env file for local development")
        return False

    return True


def check_tables_exist():
    """Check if database tables already exist."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        required_tables = ['users', 'saved_restaurants', 'trips', 'trip_items']
        missing_tables = [t for t in required_tables if t not in existing_tables]

        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            return False

        print(f"✅ All required tables exist: {existing_tables}")
        return True

    except Exception as e:
        print(f"Error checking tables: {e}")
        return False


def initialize_database():
    """Initialize database - create tables if they don't exist."""

    # Check if DATABASE_URL is configured
    if not check_database_configured():
        return False

    print("Checking database connection...")

    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")

        # Check if tables exist
        if check_tables_exist():
            print("✅ Database already initialized")
            return True

        # Create tables
        print("Creating database tables...")
        init_db()
        print("✅ Database initialization complete")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print(f"   Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False


if __name__ == '__main__':
    """Run database initialization manually."""
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)

    success = initialize_database()

    if success:
        print("\n✅ Database is ready!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)
