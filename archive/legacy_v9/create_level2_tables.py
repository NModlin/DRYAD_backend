"""
Create Level 2 Database Tables

This script creates all database tables required for Level 2 components:
1. Persistent Volumes (for Stateful Tool Management)
2. Additional session tracking fields

Run this before Level 2 validation.
"""

import sys
import sqlite3
import os

# Database path (same as Level 1)
DB_PATH = "data/DRYAD.AI.db"


def create_tables():
    """Create all Level 2 tables using raw SQL."""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("   Run create_level1_tables.py first!")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔧 Creating Level 2 database tables...")

    # Drop existing tables to ensure clean schema
    print("  📦 Dropping existing persistent_volumes table if exists...")
    try:
        cursor.execute("DROP TABLE IF EXISTS persistent_volumes")
        conn.commit()
    except Exception as e:
        print(f"  ⚠️  Could not drop persistent_volumes: {e}")

    # Create persistent_volumes table
    print("  📦 Creating persistent_volumes table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persistent_volumes (
                volume_id TEXT PRIMARY KEY,
                session_id TEXT,
                size_bytes INTEGER,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL,
                sanitized_at TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'orphaned', 'sanitized', 'deleted')),
                FOREIGN KEY (session_id) REFERENCES tool_sessions(session_id) ON DELETE SET NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_volumes_session ON persistent_volumes(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_volumes_status ON persistent_volumes(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_volumes_last_accessed ON persistent_volumes(last_accessed_at)")

        conn.commit()
        print("  ✅ persistent_volumes table created")
    except Exception as e:
        print(f"  ❌ Error creating persistent_volumes: {e}")
        conn.close()
        return False

    # Verify tables exist
    print("\n🔍 Verifying tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"  📋 Found {len(tables)} tables in database")

    if "persistent_volumes" in tables:
        print("  ✅ persistent_volumes table verified")

        # Show columns
        cursor.execute("PRAGMA table_info(persistent_volumes)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"     Columns: {', '.join(columns)}")
    else:
        print("  ❌ persistent_volumes table NOT found")
        conn.close()
        return False

    conn.close()
    print("\n✅ Level 2 database schema created successfully!")
    return True


if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)

