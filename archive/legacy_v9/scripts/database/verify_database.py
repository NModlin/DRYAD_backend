"""Verify database schema and seeded data."""
import sqlite3
import sys

def verify_database():
    """Verify all tables and data exist."""
    try:
        conn = sqlite3.connect('data/DRYAD.AI.db')
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("🔍 DATABASE VERIFICATION")
    print("=" * 60)
    print()
    
    # Check tables exist
    print("📋 Checking Tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    expected_tables = [
        'agent_tool_catalog',
        'tool_permissions',
        'tool_usage_logs',
        'collaboration_workflows',
        'collaboration_steps',
        'collaboration_patterns',
        'execution_guardrails',
        'guardrail_configurations',
        'guardrail_metrics',
        'pending_approvals',
        'approval_policies',
        'approval_audit_logs'
    ]
    
    found_tables = [t[0] for t in tables]
    
    for table in expected_tables:
        if table in found_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING!")
    
    print()
    print("=" * 60)
    print("📊 Checking Seeded Data...")
    print("=" * 60)
    print()
    
    # Check seeded data
    data_checks = [
        ('agent_tool_catalog', 'Tools'),
        ('collaboration_patterns', 'Collaboration Patterns'),
        ('guardrail_configurations', 'Guardrail Configurations'),
        ('approval_policies', 'Approval Policies')
    ]
    
    for table, name in data_checks:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {name}: {count} entries")
            
            # Show sample data
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            if row:
                print(f"    Sample columns: {', '.join(columns[:5])}...")
        except sqlite3.OperationalError as e:
            print(f"  ❌ {name}: Error - {e}")
    
    print()
    print("=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    verify_database()

