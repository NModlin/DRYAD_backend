"""
Level 4 Database Schema Creation
DRYAD.AI Agent Evolution Architecture

Creates tables for The Dojo Evaluation Framework:
- benchmarks: Standardized evaluation problems
- evaluation_runs: Track agent evaluations
- evaluation_results: Detailed scores and metrics
"""

import sqlite3
import os
from datetime import datetime


def create_level4_tables():
    """Create all Level 4 database tables."""
    
    # Database path
    db_path = "data/DRYAD.AI.db"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating Level 4 tables...")
    
    try:
        # Table 1: benchmarks - Standardized evaluation problems
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                benchmark_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL CHECK (category IN ('reasoning', 'tool_use', 'memory', 'collaboration', 'general')),
                dataset_uri TEXT NOT NULL,
                evaluation_logic_uri TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                CONSTRAINT unique_benchmark_version UNIQUE(name, version)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_name ON benchmarks(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_category ON benchmarks(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_active ON benchmarks(is_active)")
        
        print("✓ Created table: benchmarks")
        
        # Table 2: evaluation_runs - Track agent evaluations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                run_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                agent_version TEXT NOT NULL,
                benchmark_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                execution_time_ms INTEGER,
                FOREIGN KEY (benchmark_id) REFERENCES benchmarks(benchmark_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_agent ON evaluation_runs(agent_id, agent_version)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON evaluation_runs(benchmark_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON evaluation_runs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_started ON evaluation_runs(started_at DESC)")
        
        print("✓ Created table: evaluation_runs")
        
        # Table 3: evaluation_results - Detailed scores and metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                result_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL UNIQUE,
                scores_json TEXT NOT NULL,
                raw_logs_uri TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_run ON evaluation_results(run_id)")
        
        print("✓ Created table: evaluation_results")
        
        # Commit changes
        conn.commit()
        
        print("\n✅ All Level 4 tables created successfully!")
        print(f"Database: {db_path}")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%benchmark%' OR name LIKE '%evaluation%'")
        tables = cursor.fetchall()
        print(f"\nVerified tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    create_level4_tables()

