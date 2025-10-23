#!/usr/bin/env python3
"""
Manual OAuth2 migration script to add User table and user_id columns.
This script handles the database migration manually since Alembic is having issues.
"""

import sqlite3
import os
from datetime import datetime

def run_oauth2_migration():
    """Run the OAuth2 migration manually."""
    db_path = "data/DRYAD.AI.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Starting OAuth2 migration...")
        
        # 1. Create users table if it doesn't exist
        print("📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                picture TEXT,
                email_verified BOOLEAN DEFAULT FALSE,
                roles TEXT DEFAULT '["user"]',
                permissions TEXT DEFAULT '["read", "write"]',
                provider TEXT DEFAULT 'google',
                provider_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE
            )
        """)
        
        # 2. Check if conversations table exists and add user_id column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
        if cursor.fetchone():
            print("📝 Adding user_id to conversations table...")
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT")
                print("✅ Added user_id column to conversations")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("✅ user_id column already exists in conversations")
                else:
                    raise
        
        # 3. Check if documents table exists and add user_id column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if cursor.fetchone():
            print("📝 Adding user_id to documents table...")
            try:
                cursor.execute("ALTER TABLE documents ADD COLUMN user_id TEXT")
                print("✅ Added user_id column to documents")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("✅ user_id column already exists in documents")
                else:
                    raise
        
        # 4. Create indexes for better performance
        print("📝 Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents (user_id)")
            print("✅ Created indexes")
        except sqlite3.OperationalError as e:
            print(f"⚠️  Index creation warning: {e}")
        
        # 5. Commit changes
        conn.commit()
        print("✅ OAuth2 migration completed successfully!")
        
        # 6. Show table structure
        print("\n📊 Current database structure:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                print(f"\n🔹 Table: {table_name}")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_oauth2_migration()
    if success:
        print("\n🎉 OAuth2 migration completed! You can now test the OAuth2 endpoints.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
