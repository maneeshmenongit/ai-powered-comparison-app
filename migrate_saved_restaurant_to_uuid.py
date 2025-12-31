#!/usr/bin/env python3
"""
Database Migration: Convert SavedRestaurant IDs from INTEGER to UUID

This script migrates the saved_restaurants table from using integer IDs to UUID IDs.
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

def migrate_saved_restaurant_to_uuid():
    """Migrate saved_restaurants table from INTEGER id to UUID id."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False

    print("\n" + "="*70)
    print(" DATABASE MIGRATION: SavedRestaurant ID INTEGER → UUID")
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
            WHERE table_name = 'saved_restaurants' AND column_name = 'id';
        """)
        current_type = cursor.fetchone()
        print(f"   saved_restaurants.id: {current_type[1]}")

        if current_type[1] == 'uuid':
            print("\n✅ saved_restaurants table already uses UUID! No migration needed.")
            cursor.close()
            conn.close()
            return True

        # Step 2: Create mapping table
        print("\n📝 Creating ID mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_restaurant_id_mapping (
                old_id INTEGER PRIMARY KEY,
                new_uuid UUID NOT NULL
            );
        """)

        # Step 3: Generate UUIDs for existing saved restaurants
        print("🔄 Generating UUIDs for existing saved restaurants...")
        cursor.execute("SELECT id FROM saved_restaurants ORDER BY id;")
        existing_records = cursor.fetchall()

        for (old_id,) in existing_records:
            new_uuid = uuid.uuid4()
            cursor.execute(
                "INSERT INTO saved_restaurant_id_mapping (old_id, new_uuid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (old_id, new_uuid)
            )

        print(f"   Generated UUIDs for {len(existing_records)} saved restaurants")

        # Step 4: Add temporary UUID column
        print("\n🔧 Adding temporary UUID column...")
        cursor.execute("""
            ALTER TABLE saved_restaurants ADD COLUMN IF NOT EXISTS id_uuid UUID;
        """)

        # Step 5: Populate UUID column with mapped values
        print("🔄 Populating UUID column...")
        cursor.execute("""
            UPDATE saved_restaurants
            SET id_uuid = saved_restaurant_id_mapping.new_uuid
            FROM saved_restaurant_id_mapping
            WHERE saved_restaurants.id = saved_restaurant_id_mapping.old_id;
        """)

        # Step 6: Drop old primary key constraint
        print("\n🗑️  Dropping old primary key constraint...")
        cursor.execute("""
            ALTER TABLE saved_restaurants DROP CONSTRAINT IF EXISTS saved_restaurants_pkey;
        """)

        # Step 7: Drop old column
        print("🗑️  Dropping old integer ID column...")
        cursor.execute("ALTER TABLE saved_restaurants DROP COLUMN IF EXISTS id CASCADE;")

        # Step 8: Rename UUID column to final name
        print("\n🔄 Renaming UUID column...")
        cursor.execute("ALTER TABLE saved_restaurants RENAME COLUMN id_uuid TO id;")

        # Step 9: Add primary key constraint
        print("🔑 Adding primary key constraint...")
        cursor.execute("ALTER TABLE saved_restaurants ADD PRIMARY KEY (id);")

        # Step 10: Drop mapping table
        print("\n🗑️  Cleaning up mapping table...")
        cursor.execute("DROP TABLE IF EXISTS saved_restaurant_id_mapping;")

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
            WHERE table_name = 'saved_restaurants'
            ORDER BY ordinal_position;
        """)

        print("\n🗂️  saved_restaurants table:")
        for row in cursor.fetchall():
            print(f"   {row[0]:20s} {row[1]:20s} Nullable: {row[2]}")

        # Show record count
        cursor.execute("SELECT COUNT(*) FROM saved_restaurants;")
        record_count = cursor.fetchone()[0]
        print(f"\n💾 Total saved restaurants migrated: {record_count}")

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
    print("  1. Convert saved_restaurants.id from INTEGER to UUID")
    print("  2. Preserve all existing data")
    print()

    response = input("Do you want to proceed? (yes/no): ")

    if response.lower() == 'yes':
        success = migrate_saved_restaurant_to_uuid()
        if success:
            print("\n✅ Migration completed! You can now restart your application.")
        else:
            print("\n❌ Migration failed! Please check the errors above.")
    else:
        print("\n❌ Migration cancelled.")
