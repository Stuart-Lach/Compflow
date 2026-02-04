"""
Database migration script: Add payroll_run_id column

This migration adds the payroll_run_id column to the runs table
as part of Task 2 hardening changes.

Run this if you have an existing database with data you want to preserve.
Otherwise, just delete the database file and let it recreate.
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str = "compliance.db"):
    """
    Add payroll_run_id column to runs table.

    Args:
        db_path: Path to SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"❌ Database not found: {db_path}")
        print("No migration needed - database will be created with correct schema")
        return False

    print(f"📊 Migrating database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(runs)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'payroll_run_id' in columns:
            print("✅ Column 'payroll_run_id' already exists - no migration needed")
            conn.close()
            return True

        print("🔧 Adding payroll_run_id column...")

        # SQLite doesn't support adding NOT NULL columns directly to existing tables
        # We need to use a default value, then update
        cursor.execute("""
            ALTER TABLE runs 
            ADD COLUMN payroll_run_id TEXT NOT NULL DEFAULT 'MIGRATED'
        """)

        print("🔧 Updating existing rows...")

        # Set payroll_run_id to match run_id for existing records
        # (This is a fallback - ideally would extract from stored data)
        cursor.execute("""
            UPDATE runs 
            SET payroll_run_id = id 
            WHERE payroll_run_id = 'MIGRATED'
        """)

        rows_updated = cursor.rowcount
        print(f"   Updated {rows_updated} existing row(s)")

        print("🔧 Creating index...")

        # Create index for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_runs_payroll_run_id 
            ON runs(payroll_run_id)
        """)

        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(runs)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'payroll_run_id' in columns:
            print("✅ Migration successful!")
            print(f"   Added column: payroll_run_id")
            print(f"   Created index: ix_runs_payroll_run_id")
            print(f"   Updated {rows_updated} existing record(s)")
            success = True
        else:
            print("❌ Migration verification failed")
            success = False

        conn.close()
        return success

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False


def verify_migration(db_path: str = "compliance.db"):
    """Verify the migration was successful."""

    print("\n🔍 Verifying migration...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check schema
        cursor.execute("PRAGMA table_info(runs)")
        columns = {col[1]: col for col in cursor.fetchall()}

        if 'payroll_run_id' not in columns:
            print("❌ Column 'payroll_run_id' not found")
            return False

        print("✅ Column exists")

        # Check index
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='ix_runs_payroll_run_id'
        """)

        if cursor.fetchone():
            print("✅ Index exists")
        else:
            print("⚠️  Index missing (will be recreated on next run)")

        # Check data
        cursor.execute("SELECT COUNT(*) FROM runs WHERE payroll_run_id IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"✅ {count} row(s) have payroll_run_id values")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Database Migration: Add payroll_run_id column")
    print("="*60)
    print()

    # Allow custom database path
    db_path = sys.argv[1] if len(sys.argv) > 1 else "compliance.db"

    # Run migration
    success = migrate_database(db_path)

    # Verify if successful
    if success:
        verify_migration(db_path)

    print()
    print("="*60)

    if success:
        print("✅ Migration complete - restart your server")
        print()
        print("Next steps:")
        print("1. Restart the FastAPI server")
        print("2. Test by uploading a CSV file")
        print("3. Verify payroll_run_id appears in responses")
    else:
        print("❌ Migration failed")
        print()
        print("Options:")
        print("1. Delete the database and let it recreate (fresh start)")
        print("2. Check error messages above and retry")
        print("3. Manual SQL migration (see DATABASE_MIGRATION_REQUIRED.md)")

    print("="*60)

    sys.exit(0 if success else 1)

