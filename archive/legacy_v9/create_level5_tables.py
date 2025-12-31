"""
Level 5 Database Schema Creation
DRYAD.AI Agent Evolution Architecture

Creates tables for The Lyceum Self-Improvement Engine:
- research_projects: Self-improvement initiatives
- experiments: Individual improvement experiments
- research_budgets: Compute budget allocation
- improvement_proposals: Validated improvement proposals
"""

import sqlite3
import os
from datetime import datetime


def create_level5_tables():
    """Create all Level 5 database tables."""
    
    # Database path
    db_path = "data/DRYAD.AI.db"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating Level 5 tables...")
    
    try:
        # Table 1: research_projects - Self-improvement initiatives
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_projects (
                project_id TEXT PRIMARY KEY,
                professor_agent_id TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                target_component TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('analyzing', 'experimenting', 'validating', 'completed', 'abandoned')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                outcome TEXT
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_professor ON research_projects(professor_agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON research_projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_component ON research_projects(target_component)")
        
        print("✓ Created table: research_projects")
        
        # Table 2: experiments - Individual improvement experiments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                experiment_type TEXT NOT NULL CHECK (experiment_type IN ('prompt_optimization', 'parameter_tuning', 'architecture_change', 'tool_addition')),
                configuration TEXT NOT NULL,
                baseline_run_id TEXT,
                experimental_run_id TEXT,
                improvement_delta REAL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (baseline_run_id) REFERENCES evaluation_runs(run_id),
                FOREIGN KEY (experimental_run_id) REFERENCES evaluation_runs(run_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_project ON experiments(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_type ON experiments(experiment_type)")
        
        print("✓ Created table: experiments")
        
        # Table 3: research_budgets - Compute budget allocation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_budgets (
                budget_id TEXT PRIMARY KEY,
                professor_agent_id TEXT NOT NULL,
                allocated_compute_hours REAL NOT NULL,
                consumed_compute_hours REAL DEFAULT 0,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('active', 'exhausted', 'expired'))
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_professor ON research_budgets(professor_agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_status ON research_budgets(status)")
        
        print("✓ Created table: research_budgets")
        
        # Table 4: improvement_proposals - Validated improvement proposals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvement_proposals (
                proposal_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                implementation_details TEXT NOT NULL,
                validation_results TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending_review', 'approved', 'rejected', 'deployed')),
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                reviewer_id TEXT,
                review_notes TEXT,
                FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_project ON improvement_proposals(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_status ON improvement_proposals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_submitted ON improvement_proposals(submitted_at DESC)")
        
        print("✓ Created table: improvement_proposals")
        
        # Commit changes
        conn.commit()
        
        print("\n✅ All Level 5 tables created successfully!")
        print(f"Database: {db_path}")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%research%' OR name LIKE '%experiment%' OR name LIKE '%proposal%')")
        tables = cursor.fetchall()
        print(f"\nVerified tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    create_level5_tables()

