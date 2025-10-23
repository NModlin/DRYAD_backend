"""
Create Level 1 tables directly for validation testing.
This bypasses the migration system to avoid conflicts.

COMPREHENSIVE SCHEMA - Matches ALL fields from SQLAlchemy models:
- app/models/agent_tools.py (ToolSession, ToolExecution)
- app/models/agent_registry.py (SystemAgent)
- app/services/tool_registry/models.py (Tool, ToolPermission)
- app/services/memory_guild/models.py (MemoryRecord, MemoryEmbedding, etc.)
"""
import sqlite3
import os

# Database path
DB_PATH = "data/DRYAD.AI.db"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Delete existing database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"✅ Deleted existing database: {DB_PATH}")

# Create new database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("📦 Creating Level 1 tables with COMPLETE schema...")

# ============================================================================
# TOOL REGISTRY TABLES
# ============================================================================

# Create tools table (Tool Registry) - from app/services/tool_registry/models.py
cursor.execute("""
CREATE TABLE IF NOT EXISTS tools (
    tool_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    schema_json TEXT NOT NULL,
    docker_image_uri VARCHAR(500),
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    updated_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    UNIQUE(name, version)
)
""")

# Create tool_permissions table - from app/services/tool_registry/models.py
cursor.execute("""
CREATE TABLE IF NOT EXISTS tool_permissions (
    permission_id VARCHAR(36) PRIMARY KEY,
    principal_id VARCHAR(255) NOT NULL,
    principal_type VARCHAR(20) NOT NULL,
    tool_id VARCHAR(36) NOT NULL,
    allow_stateful_execution BOOLEAN NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    created_by VARCHAR(255),
    FOREIGN KEY(tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE,
    UNIQUE(principal_id, principal_type, tool_id),
    CHECK(principal_type IN ('agent', 'role'))
)
""")

# ============================================================================
# SANDBOX EXECUTION TABLES
# ============================================================================

# Create tool_sessions table - from app/models/agent_tools.py (ToolSession)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS tool_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    tool_id VARCHAR(36),
    agent_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255),
    sandbox_id VARCHAR(255),
    sandbox_status VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    expires_at DATETIME,
    closed_at DATETIME
)
""")

# Create tool_executions table - from app/models/agent_tools.py (ToolExecution)
# ALL fields from the model including security_violations
cursor.execute("""
CREATE TABLE IF NOT EXISTS tool_executions (
    id VARCHAR(36) PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL UNIQUE,
    session_id VARCHAR(255) NOT NULL,
    tool_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    command TEXT NOT NULL,
    working_directory VARCHAR(500),
    environment_variables TEXT,
    input_parameters TEXT,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    success BOOLEAN NOT NULL DEFAULT 0,
    error_message TEXT,
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent INTEGER,
    resource_limits_enforced BOOLEAN NOT NULL DEFAULT 1,
    security_violations TEXT,
    started_at DATETIME NOT NULL DEFAULT (datetime('now')),
    completed_at DATETIME
)
""")

# ============================================================================
# MEMORY GUILD TABLES
# ============================================================================

# Create memory_records table - from app/services/memory_guild/models.py (MemoryRecord)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory_records (
    memory_id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    content_text TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata TEXT DEFAULT '{}' NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    updated_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    is_deleted BOOLEAN DEFAULT 0 NOT NULL,
    deleted_at DATETIME,
    CHECK(source_type IN ('conversation', 'tool_output', 'document', 'observation', 'external')),
    UNIQUE(agent_id, tenant_id, content_hash)
)
""")

# Create memory_embeddings table - from app/services/memory_guild/models.py (MemoryEmbedding)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory_embeddings (
    embedding_id VARCHAR(36) PRIMARY KEY,
    memory_id VARCHAR(36) NOT NULL,
    vector_id VARCHAR(255) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    FOREIGN KEY(memory_id) REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    UNIQUE(memory_id, embedding_model)
)
""")

# Create memory_relationships table - from app/services/memory_guild/models.py (MemoryRelationship)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory_relationships (
    relationship_id VARCHAR(36) PRIMARY KEY,
    source_memory_id VARCHAR(36) NOT NULL,
    target_memory_id VARCHAR(36) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    confidence_score REAL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    FOREIGN KEY(source_memory_id) REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    FOREIGN KEY(target_memory_id) REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    CHECK(relationship_type IN ('references', 'contradicts', 'supports', 'follows', 'related')),
    CHECK(confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)),
    CHECK(source_memory_id != target_memory_id),
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
)
""")


# Create data_sources table - from app/services/memory_guild/models.py (DataSource)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS data_sources (
    source_id VARCHAR(36) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    source_uri TEXT,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    last_ingestion_at DATETIME,
    metadata TEXT DEFAULT '{}' NOT NULL,
    CHECK(source_type IN ('api', 'database', 'file_system', 'webhook', 'manual'))
)
""")

# Create memory_access_policies table - from app/services/memory_guild/models.py (MemoryAccessPolicy)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory_access_policies (
    policy_id VARCHAR(36) PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL UNIQUE,
    policy_rules TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    updated_at DATETIME DEFAULT (datetime('now')) NOT NULL
)
""")

# Create system_logs table (Structured Logging)
cursor.execute("""
CREATE TABLE IF NOT EXISTS system_logs (
    log_id VARCHAR(36) PRIMARY KEY,
    timestamp DATETIME DEFAULT (datetime('now')) NOT NULL,
    level VARCHAR(20) NOT NULL,
    logger_name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    context TEXT,
    trace_id VARCHAR(36),
    span_id VARCHAR(36),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    error_type VARCHAR(255),
    stack_trace TEXT,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL
)
""")

# ============================================================================
# AGENT REGISTRY TABLES
# ============================================================================

# Create system_agents table - from app/models/agent_registry.py (SystemAgent)
# ALL fields from the model - complete schema with ~30 fields
cursor.execute("""
CREATE TABLE IF NOT EXISTS system_agents (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    orchestration_pattern VARCHAR(50) NOT NULL DEFAULT 'hierarchical',
    can_collaborate_directly BOOLEAN DEFAULT 0,
    preferred_collaborators TEXT,
    capabilities TEXT NOT NULL,
    description TEXT,
    role TEXT,
    goal TEXT,
    backstory TEXT,
    configuration TEXT NOT NULL,
    llm_config TEXT,
    tools TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    health_check_url VARCHAR(500),
    last_health_check DATETIME,
    health_status VARCHAR(50),
    total_tasks INTEGER DEFAULT 0,
    successful_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    avg_execution_time REAL DEFAULT 0.0,
    total_tokens_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    updated_at DATETIME DEFAULT (datetime('now')) NOT NULL,
    last_used_at DATETIME,
    extra_data TEXT
)
""")

# Create agent_capability_matches table - from app/models/agent_registry.py (AgentCapabilityMatch)
# ALL fields from the model
cursor.execute("""
CREATE TABLE IF NOT EXISTS agent_capability_matches (
    id VARCHAR(36) PRIMARY KEY,
    capability VARCHAR(255) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    proficiency REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT (datetime('now')) NOT NULL
)
""")

# Commit changes
conn.commit()

# Verify tables were created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n✅ Level 1 tables created successfully:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()

print(f"\n🎉 Database ready for Level 1 validation: {DB_PATH}")

