"""
Create Level 3 Database Tables

This script creates all database tables required for Level 3 components:
1. Orchestration (task_forces, task_force_members, task_force_logs, orchestration_decisions)
2. HITL (consultation_requests, consultation_messages)

Run this before Level 3 validation.
"""

import sys
import sqlite3
import os

# Database path (same as Level 1 and Level 2)
DB_PATH = "data/DRYAD.AI.db"


def create_tables():
    """Create all Level 3 tables using raw SQL."""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("   Run create_level1_tables.py first!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 Creating Level 3 database tables...")
    
    # Drop existing tables to ensure clean schema
    print("  📦 Dropping existing Level 3 tables if they exist...")
    tables_to_drop = [
        "consultation_messages",
        "consultation_requests",
        "orchestration_decisions",
        "task_force_logs",
        "task_force_members",
        "task_forces"
    ]
    
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        except Exception as e:
            print(f"  ⚠️  Could not drop {table}: {e}")
    
    conn.commit()
    
    # Create task_forces table
    print("  📦 Creating task_forces table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_forces (
                task_force_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'failed', 'paused')),
                master_orchestrator_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_result TEXT
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_forces_status ON task_forces(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_forces_orchestrator ON task_forces(master_orchestrator_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_forces_created ON task_forces(created_at DESC)")
        
        conn.commit()
        print("  ✅ task_forces table created")
    except Exception as e:
        print(f"  ❌ Error creating task_forces: {e}")
        conn.close()
        return False
    
    # Create task_force_members table
    print("  📦 Creating task_force_members table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_force_members (
                member_id TEXT PRIMARY KEY,
                task_force_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                FOREIGN KEY (task_force_id) REFERENCES task_forces(task_force_id) ON DELETE CASCADE,
                UNIQUE(task_force_id, agent_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_task_force ON task_force_members(task_force_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_agent ON task_force_members(agent_id)")
        
        conn.commit()
        print("  ✅ task_force_members table created")
    except Exception as e:
        print(f"  ❌ Error creating task_force_members: {e}")
        conn.close()
        return False
    
    # Create task_force_logs table
    print("  📦 Creating task_force_logs table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_force_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_force_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                message_type TEXT NOT NULL CHECK (message_type IN ('proposal', 'critique', 'refinement', 'agreement', 'question', 'answer')),
                message_content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (task_force_id) REFERENCES task_forces(task_force_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_task_force ON task_force_logs(task_force_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_agent ON task_force_logs(agent_id)")
        
        conn.commit()
        print("  ✅ task_force_logs table created")
    except Exception as e:
        print(f"  ❌ Error creating task_force_logs: {e}")
        conn.close()
        return False
    
    # Create orchestration_decisions table
    print("  📦 Creating orchestration_decisions table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orchestration_decisions (
                decision_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                decision_type TEXT NOT NULL CHECK (decision_type IN ('sequential', 'task_force', 'escalation')),
                complexity_score REAL,
                reasoning TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_task ON orchestration_decisions(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_type ON orchestration_decisions(decision_type)")
        
        conn.commit()
        print("  ✅ orchestration_decisions table created")
    except Exception as e:
        print(f"  ❌ Error creating orchestration_decisions: {e}")
        conn.close()
        return False
    
    # Create consultation_requests table
    print("  📦 Creating consultation_requests table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultation_requests (
                consultation_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_force_id TEXT,
                consultation_type TEXT NOT NULL CHECK (consultation_type IN ('approval', 'guidance', 'clarification', 'escalation')),
                context TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'resolved', 'timeout')),
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution TEXT,
                timeout_at TEXT NOT NULL,
                FOREIGN KEY (task_force_id) REFERENCES task_forces(task_force_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_agent ON consultation_requests(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_task ON consultation_requests(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultation_requests(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultations_timeout ON consultation_requests(timeout_at)")
        
        conn.commit()
        print("  ✅ consultation_requests table created")
    except Exception as e:
        print(f"  ❌ Error creating consultation_requests: {e}")
        conn.close()
        return False
    
    # Create consultation_messages table
    print("  📦 Creating consultation_messages table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultation_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                consultation_id TEXT NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('agent', 'human')),
                sender_id TEXT NOT NULL,
                message_content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (consultation_id) REFERENCES consultation_requests(consultation_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_consultation ON consultation_messages(consultation_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON consultation_messages(sender_id)")
        
        conn.commit()
        print("  ✅ consultation_messages table created")
    except Exception as e:
        print(f"  ❌ Error creating consultation_messages: {e}")
        conn.close()
        return False
    
    # Verify tables exist
    print("\n🔍 Verifying tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"  📋 Found {len(tables)} tables in database")
    
    level3_tables = [
        "task_forces",
        "task_force_members",
        "task_force_logs",
        "orchestration_decisions",
        "consultation_requests",
        "consultation_messages"
    ]
    
    all_verified = True
    for table in level3_tables:
        if table in tables:
            print(f"  ✅ {table} table verified")
            
            # Show columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"     Columns: {', '.join(columns)}")
        else:
            print(f"  ❌ {table} table NOT found")
            all_verified = False
    
    conn.close()
    
    if all_verified:
        print("\n✅ Level 3 database schema created successfully!")
        return True
    else:
        print("\n❌ Some tables were not created successfully")
        return False


if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)

