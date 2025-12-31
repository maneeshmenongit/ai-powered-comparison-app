#!/usr/bin/env python3
"""
Database Migration: Convert user IDs from INTEGER to UUID

This script migrates the users table from using integer IDs to UUID IDs.
It preserves all existing data and relationships.

WARNING: This migration is irreversible. Backup your database first!
"""

import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import uuid

# Register UUID adapter for psycopg2
psycopg2.extras.register_uuid()

load_dotenv()

def migrate_to_uuid():
    """Migrate users table from INTEGER id to UUID id."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False

    print("\n" + "="*70)
    print(" DATABASE MIGRATION: INTEGER ID → UUID")
    print("="*70 + "\n")

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Connected to database")

        # Step 1: Check current table structure
        print("\n📊 Current table structure:")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'id';
        """)
        current_type = cursor.fetchone()
        print(f"   users.id: {current_type[1]}")

        if current_type[1] == 'uuid':
            print("\n✅ Users table already uses UUID! No migration needed.")
            cursor.close()
            conn.close()
            return True

        # Step 2: Create mapping table to store old_id → new_uuid
        print("\n📝 Creating ID mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_id_mapping (
                old_id INTEGER PRIMARY KEY,
                new_uuid UUID NOT NULL
            );
        """)

        # Step 3: Generate UUIDs for existing users
        print("🔄 Generating UUIDs for existing users...")
        cursor.execute("SELECT id FROM users ORDER BY id;")
        existing_users = cursor.fetchall()

        for (old_id,) in existing_users:
            new_uuid = uuid.uuid4()
            cursor.execute(
                "INSERT INTO user_id_mapping (old_id, new_uuid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (old_id, new_uuid)
            )

        print(f"   Generated UUIDs for {len(existing_users)} users")

        # Step 4: Add temporary UUID column to users table
        print("\n🔧 Adding temporary UUID column to users table...")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS id_uuid UUID;
        """)

        # Step 5: Populate UUID column with mapped values
        print("🔄 Populating UUID column...")
        cursor.execute("""
            UPDATE users
            SET id_uuid = user_id_mapping.new_uuid
            FROM user_id_mapping
            WHERE users.id = user_id_mapping.old_id;
        """)

        # Step 6: Add temporary UUID column to saved_restaurants
        print("\n🔧 Adding temporary UUID column to saved_restaurants...")
        cursor.execute("""
            ALTER TABLE saved_restaurants ADD COLUMN IF NOT EXISTS user_id_uuid UUID;
        """)

        # Step 7: Populate foreign key UUID column
        print("🔄 Updating foreign keys...")
        cursor.execute("""
            UPDATE saved_restaurants
            SET user_id_uuid = user_id_mapping.new_uuid
            FROM user_id_mapping
            WHERE saved_restaurants.user_id = user_id_mapping.old_id;
        """)

        # Step 8: Drop old foreign key constraint
        print("\n🗑️  Dropping old foreign key constraint...")
        cursor.execute("""
            ALTER TABLE saved_restaurants
            DROP CONSTRAINT IF EXISTS saved_restaurants_user_id_fkey;
        """)

        # Step 9: Drop old columns
        print("🗑️  Dropping old integer ID columns...")
        cursor.execute("ALTER TABLE users DROP COLUMN IF EXISTS id CASCADE;")
        cursor.execute("ALTER TABLE saved_restaurants DROP COLUMN IF EXISTS user_id;")

        # Step 10: Rename UUID columns to final names
        print("\n🔄 Renaming UUID columns...")
        cursor.execute("ALTER TABLE users RENAME COLUMN id_uuid TO id;")
        cursor.execute("ALTER TABLE saved_restaurants RENAME COLUMN user_id_uuid TO user_id;")

        # Step 11: Add primary key constraint
        print("🔑 Adding primary key constraint...")
        cursor.execute("ALTER TABLE users ADD PRIMARY KEY (id);")

        # Step 12: Add foreign key constraint
        print("🔗 Adding foreign key constraint...")
        cursor.execute("""
            ALTER TABLE saved_restaurants
            ADD CONSTRAINT saved_restaurants_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """)

        # Step 13: Create indexes
        print("📇 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_restaurants_user_id ON saved_restaurants(user_id);")

        # Step 14: Drop mapping table
        print("\n🗑️  Cleaning up mapping table...")
        cursor.execute("DROP TABLE IF EXISTS user_id_mapping;")

        # Commit all changes
        conn.commit()

        print("\n" + "="*70)
        print(" ✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*70)

        # Show final table structure
        print("\n📊 Final table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)

        print("\n🗂️  users table:")
        for row in cursor.fetchall():
            print(f"   {row[0]:20s} {row[1]:20s} Nullable: {row[2]}")

        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'saved_restaurants'
            ORDER BY ordinal_position;
        """)

        print("\n🗂️  saved_restaurants table:")
        for row in cursor.fetchall():
            print(f"   {row[0]:20s} {row[1]:20s} Nullable: {row[2]}")

        # Show user count
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Total users migrated: {user_count}")

        cursor.execute("SELECT COUNT(*) FROM saved_restaurants;")
        saved_count = cursor.fetchone()[0]
        print(f"💾 Total saved restaurants migrated: {saved_count}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Database may be in an inconsistent state!")
        print("⚠️  Please restore from backup if needed.")
        return False

if __name__ == "__main__":
    print("\n⚠️  WARNING: This migration is IRREVERSIBLE!")
    print("⚠️  Make sure you have a database backup before proceeding.")
    print("\nThis migration will:")
    print("  1. Convert users.id from INTEGER to UUID")
    print("  2. Convert saved_restaurants.user_id from INTEGER to UUID")
    print("  3. Preserve all existing data and relationships")
    print()

    response = input("Do you want to proceed? (yes/no): ")

    if response.lower() == 'yes':
        success = migrate_to_uuid()
        if success:
            print("\n✅ Migration completed! You can now restart your application.")
        else:
            print("\n❌ Migration failed! Please check the errors above.")
    else:
        print("\n❌ Migration cancelled.")
