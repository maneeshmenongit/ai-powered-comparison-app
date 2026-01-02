"""
Migration script to add authentication columns to users table
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def migrate_database():
    """Add authentication columns to existing users table."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Connected to database")

        # Add username column
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS username VARCHAR(80) UNIQUE;
            """)
            print("✅ Added username column")
        except Exception as e:
            print(f"ℹ️  Username column: {e}")

        # Add email column
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS email VARCHAR(120) UNIQUE;
            """)
            print("✅ Added email column")
        except Exception as e:
            print(f"ℹ️  Email column: {e}")

        # Add password_hash column
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
            """)
            print("✅ Added password_hash column")
        except Exception as e:
            print(f"ℹ️  Password_hash column: {e}")

        # Add is_guest column
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_guest BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            print("✅ Added is_guest column")
        except Exception as e:
            print(f"ℹ️  Is_guest column: {e}")

        # Add is_premium column
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_premium BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            print("✅ Added is_premium column")
        except Exception as e:
            print(f"ℹ️  Is_premium column: {e}")

        # Create indexes for performance
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """)
            print("✅ Created index on username")
        except Exception as e:
            print(f"ℹ️  Username index: {e}")

        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """)
            print("✅ Created index on email")
        except Exception as e:
            print(f"ℹ️  Email index: {e}")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Show current table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)

        print("\nCurrent users table structure:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]:20s} {row[1]:20s} Nullable: {row[2]}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Adding Authentication Columns")
    print("=" * 60)
    print()
    migrate_database()
