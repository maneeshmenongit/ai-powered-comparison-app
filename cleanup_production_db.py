#!/usr/bin/env python3
"""
Production Database Cleanup Script

Removes test/junk data from the production database.
This script identifies and removes:
1. Test users (usernames/emails containing 'test')
2. Test device IDs (non-UUID format)
3. Orphaned saved restaurants

WARNING: This is destructive! Only run on production after backing up.
"""

import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import uuid

# Register UUID adapter
psycopg2.extras.register_uuid()

load_dotenv()

def is_valid_uuid(device_id):
    """Check if device_id is a valid UUID."""
    try:
        uuid.UUID(device_id)
        return True
    except (ValueError, AttributeError):
        return False

def cleanup_production_db(dry_run=True):
    """
    Clean up test data from production database.

    Args:
        dry_run: If True, only shows what would be deleted without actually deleting
    """
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False

    print("\n" + "="*70)
    print(f" PRODUCTION DATABASE CLEANUP {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print("="*70 + "\n")

    # Safety check
    if not dry_run:
        print("⚠️  WARNING: This will PERMANENTLY DELETE data!")
        print("⚠️  Make sure you have a database backup!")
        print()
        confirm = input("Type 'DELETE JUNK DATA' to confirm: ")
        if confirm != "DELETE JUNK DATA":
            print("\n❌ Cleanup cancelled.")
            return False
        print()

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("✅ Connected to database")
        print()

        # 1. Find test users (by username/email)
        print("🔍 Finding test users (username/email contains 'test')...")
        cursor.execute("""
            SELECT id, username, email, device_id, is_guest, created_at
            FROM users
            WHERE LOWER(username) LIKE '%test%'
               OR LOWER(email) LIKE '%test%'
            ORDER BY created_at;
        """)
        test_users = cursor.fetchall()

        if test_users:
            print(f"   Found {len(test_users)} test users:")
            for user in test_users:
                user_id, username, email, device_id, is_guest, created_at = user
                print(f"   - ID: {user_id}")
                print(f"     Username: {username}")
                print(f"     Email: {email}")
                print(f"     Device ID: {device_id}")
                print(f"     Is Guest: {is_guest}")
                print(f"     Created: {created_at}")
                print()
        else:
            print("   ✅ No test users found")

        # 2. Find users with invalid device IDs (non-UUID)
        print("\n🔍 Finding users with invalid device IDs (non-UUID format)...")
        cursor.execute("""
            SELECT id, username, email, device_id, is_guest, created_at
            FROM users
            WHERE device_id IS NOT NULL
            ORDER BY created_at;
        """)
        all_device_users = cursor.fetchall()

        invalid_device_users = []
        for user in all_device_users:
            user_id, username, email, device_id, is_guest, created_at = user
            if not is_valid_uuid(device_id):
                invalid_device_users.append(user)

        if invalid_device_users:
            print(f"   Found {len(invalid_device_users)} users with invalid device IDs:")
            for user in invalid_device_users:
                user_id, username, email, device_id, is_guest, created_at = user
                print(f"   - ID: {user_id}")
                print(f"     Username: {username}")
                print(f"     Email: {email}")
                print(f"     Device ID: {device_id} (INVALID)")
                print(f"     Created: {created_at}")
                print()
        else:
            print("   ✅ All device IDs are valid UUIDs")

        # 3. Count saved restaurants for these users
        test_user_ids = [str(u[0]) for u in test_users]
        invalid_user_ids = [str(u[0]) for u in invalid_device_users]
        all_junk_user_ids = list(set(test_user_ids + invalid_user_ids))

        if all_junk_user_ids:
            placeholders = ','.join(['%s'] * len(all_junk_user_ids))
            cursor.execute(f"""
                SELECT COUNT(*) FROM saved_restaurants
                WHERE user_id::text IN ({placeholders});
            """, all_junk_user_ids)
            saved_count = cursor.fetchone()[0]
            print(f"\n📊 These users have {saved_count} saved restaurants (will also be deleted)")

        # Summary
        print("\n" + "="*70)
        print(" CLEANUP SUMMARY")
        print("="*70)
        print(f"Test users to delete: {len(test_users)}")
        print(f"Invalid device ID users to delete: {len(invalid_device_users)}")
        print(f"Total users to delete: {len(all_junk_user_ids)}")
        if all_junk_user_ids:
            print(f"Saved restaurants to delete: {saved_count}")
        print()

        # Execute deletion
        if not dry_run and all_junk_user_ids:
            print("🗑️  Deleting junk data...")

            # Delete users (CASCADE will delete saved restaurants)
            cursor.execute(f"""
                DELETE FROM users
                WHERE id::text IN ({placeholders});
            """, all_junk_user_ids)

            conn.commit()

            print("✅ Junk data deleted successfully!")
            print()
        elif dry_run and all_junk_user_ids:
            print("ℹ️  DRY RUN: No data was actually deleted")
            print("   Run with --live flag to actually delete this data")
            print()
        else:
            print("✅ No junk data to clean up!")
            print()

        # Show final counts
        cursor.execute("SELECT COUNT(*) FROM users;")
        final_user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM saved_restaurants;")
        final_saved_count = cursor.fetchone()[0]

        print("="*70)
        print(" FINAL DATABASE STATS")
        print("="*70)
        print(f"Total users: {final_user_count}")
        print(f"Total saved restaurants: {final_saved_count}")
        print()

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    # Check if --live flag is provided
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        dry_run = False

    if dry_run:
        print("\n🔵 Running in DRY RUN mode (no data will be deleted)")
        print("   Use --live flag to actually delete data")
    else:
        print("\n🔴 Running in LIVE mode (data will be PERMANENTLY deleted!)")

    success = cleanup_production_db(dry_run=dry_run)
    sys.exit(0 if success else 1)
