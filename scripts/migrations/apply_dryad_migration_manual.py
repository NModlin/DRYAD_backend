"""
Manually apply Dryad migration by executing the SQL directly
"""
import sqlite3

DB_PATH = "data/DRYAD.AI.db"

def apply_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Manually applying Dryad migration...")
        
        # Create dryad_groves table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_groves (
                id VARCHAR NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                is_favorite BOOLEAN NOT NULL,
                template_metadata JSON,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                last_accessed_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_groves_id ON dryad_groves (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_groves_name ON dryad_groves (name)")
        print("  ✅ Created dryad_groves")
        
        # Create dryad_observation_points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_observation_points (
                id VARCHAR NOT NULL,
                branch_id VARCHAR NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                context TEXT,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(branch_id) REFERENCES dryad_branches (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_observation_points_id ON dryad_observation_points (id)")
        print("  ✅ Created dryad_observation_points")
        
        # Create dryad_branches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_branches (
                id VARCHAR NOT NULL,
                grove_id VARCHAR NOT NULL,
                parent_id VARCHAR,
                observation_point_id VARCHAR,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                path_depth INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(grove_id) REFERENCES dryad_groves (id) ON DELETE CASCADE,
                FOREIGN KEY(parent_id) REFERENCES dryad_branches (id) ON DELETE SET NULL,
                FOREIGN KEY(observation_point_id) REFERENCES dryad_observation_points (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_branches_id ON dryad_branches (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_branches_grove_id ON dryad_branches (grove_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_branches_parent_id ON dryad_branches (parent_id)")
        print("  ✅ Created dryad_branches")
        
        # Create dryad_possibilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_possibilities (
                id VARCHAR NOT NULL,
                observation_point_id VARCHAR NOT NULL,
                description TEXT NOT NULL,
                probability_weight FLOAT NOT NULL,
                metadata JSON,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(observation_point_id) REFERENCES dryad_observation_points (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_possibilities_id ON dryad_possibilities (id)")
        print("  ✅ Created dryad_possibilities")
        
        # Create dryad_vessels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_vessels (
                id VARCHAR NOT NULL,
                branch_id VARCHAR NOT NULL,
                storage_path VARCHAR(500) NOT NULL,
                content_hash VARCHAR(64) NOT NULL,
                file_references JSON,
                is_compressed BOOLEAN NOT NULL,
                status VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(branch_id) REFERENCES dryad_branches (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_vessels_id ON dryad_vessels (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_vessels_branch_id ON dryad_vessels (branch_id)")
        print("  ✅ Created dryad_vessels")
        
        # Create dryad_dialogues table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_dialogues (
                id VARCHAR NOT NULL,
                branch_id VARCHAR NOT NULL,
                oracle_used VARCHAR(100) NOT NULL,
                insights JSON,
                storage_path VARCHAR(500) NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(branch_id) REFERENCES dryad_branches (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_dialogues_id ON dryad_dialogues (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_dialogues_branch_id ON dryad_dialogues (branch_id)")
        print("  ✅ Created dryad_dialogues")
        
        # Create dryad_dialogue_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dryad_dialogue_messages (
                id VARCHAR NOT NULL,
                dialogue_id VARCHAR NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(dialogue_id) REFERENCES dryad_dialogues (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_dryad_dialogue_messages_dialogue_id ON dryad_dialogue_messages (dialogue_id)")
        print("  ✅ Created dryad_dialogue_messages")
        
        conn.commit()
        print("\n✅ All Dryad tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migration()

