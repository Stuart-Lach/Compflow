# Database Migration Required

## Issue

The `payroll_run_id` column has been added to the `runs` table as part of Task 2 (audit purity).

**Existing databases will be incompatible** with the updated code.

## Symptoms

If you see errors like:
- `Unknown column 'payroll_run_id'`
- `FOREIGN KEY constraint failed`
- `No such column: payroll_run_id`

This means your database schema is outdated.

## Solution Options

### Option 1: Fresh Start (Recommended for Development)

Delete the existing database and let it recreate:

```bash
cd C:\Users\adria\Compflow\compliance-engine

# Stop the server if running
# Then delete the database:
Remove-Item compliance.db -Force

# Start the server - database will be recreated with new schema
.\start_server.ps1
```

### Option 2: Manual Migration (For Production/Existing Data)

If you have existing runs you want to preserve:

```sql
-- Connect to the database
sqlite3 compliance.db

-- Add the new column
ALTER TABLE runs ADD COLUMN payroll_run_id TEXT NOT NULL DEFAULT 'MIGRATED';

-- Create index
CREATE INDEX ix_runs_payroll_run_id ON runs(payroll_run_id);

-- Update existing runs to use run_id as payroll_run_id
UPDATE runs SET payroll_run_id = id WHERE payroll_run_id = 'MIGRATED';

-- Verify
SELECT id, payroll_run_id FROM runs LIMIT 5;
```

### Option 3: Python Migration Script

```python
# scripts/migrate_add_payroll_run_id.py
import sqlite3

def migrate_database():
    conn = sqlite3.connect('compliance.db')
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(runs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'payroll_run_id' in columns:
            print("✅ Column already exists")
            return
        
        # Add column
        cursor.execute("""
            ALTER TABLE runs 
            ADD COLUMN payroll_run_id TEXT NOT NULL DEFAULT 'MIGRATED'
        """)
        
        # Update existing rows
        cursor.execute("""
            UPDATE runs 
            SET payroll_run_id = id 
            WHERE payroll_run_id = 'MIGRATED'
        """)
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_runs_payroll_run_id 
            ON runs(payroll_run_id)
        """)
        
        conn.commit()
        print("✅ Migration complete")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
```

Run with:
```bash
python scripts/migrate_add_payroll_run_id.py
```

## Verification

After migration, verify the schema:

```bash
sqlite3 compliance.db ".schema runs"
```

Should show:
```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    payroll_run_id TEXT NOT NULL,  -- <-- New column
    company_id TEXT NOT NULL,
    pay_date TEXT NOT NULL,
    ...
);
CREATE INDEX ix_runs_payroll_run_id ON runs(payroll_run_id);
```

## Future Migrations

For production systems, consider using a proper migration tool:
- Alembic (SQLAlchemy's migration tool)
- Django migrations
- Flyway
- Custom migration scripts

This ensures versioned, trackable database changes.

## Testing After Migration

1. Start the server
2. Upload a test CSV
3. Verify payroll_run_id appears in:
   - POST /api/v1/runs response
   - GET /api/v1/runs/{id} response
   - GET /api/v1/runs/{id}/export CSV header

```bash
# Quick test
curl -X POST "http://localhost:8000/api/v1/runs" \
  -F "file=@data/samples/payroll_input_sample_v1.csv" \
  | grep payroll_run_id
```

Expected output should include:
```json
{
  "run_id": "run_20260126...",
  "payroll_run_id": "PAY_2025_03",  // <-- From CSV
  ...
}
```

