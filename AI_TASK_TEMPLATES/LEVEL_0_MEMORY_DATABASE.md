# AI Task: Memory Guild Database Schema
## Level 0 - Foundation Service

---

## Context

**Dependency Level:** 0 (No dependencies - can build immediately)  
**Prerequisites:** None  
**Integration Points:** Will be used by Memory Guild agents (Level 1-2)  
**Parallel Work:** Can be built simultaneously with Tool Registry and Structured Logging

---

## Specification Reference

See `docs/FInalRoadmap/COMPONENT_SPECIFICATIONS.md` Section 2.2 for complete details.

---

## What to Build

### Purpose

Data foundation for the Memory Keeper Guild microservice. Provides polyglot persistence layer for agent memory and knowledge management.

### Files to Create

```
app/services/memory_guild/
├── __init__.py
└── models.py          # SQLAlchemy models for all memory tables

alembic/versions/
└── xxx_create_memory_guild_tables.py  # Database migration

tests/services/memory_guild/
└── test_models.py     # Model tests (constraints, relationships)
```

### Database Schema

```sql
-- Memory records: Core memory storage
CREATE TABLE memory_records (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('conversation', 'tool_output', 'document', 'observation', 'external')),
    content_text TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- MD5 hash for deduplication
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT unique_content_hash UNIQUE(agent_id, tenant_id, content_hash)
);

CREATE INDEX idx_memory_agent ON memory_records(agent_id);
CREATE INDEX idx_memory_tenant ON memory_records(tenant_id);
CREATE INDEX idx_memory_source ON memory_records(source_type);
CREATE INDEX idx_memory_created ON memory_records(created_at DESC);
CREATE INDEX idx_memory_hash ON memory_records(content_hash);
CREATE INDEX idx_memory_active ON memory_records(is_deleted) WHERE is_deleted = false;

-- Memory embeddings: Vector representations for semantic search
CREATE TABLE memory_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    vector_id VARCHAR(255) NOT NULL,  -- ID in vector database (Weaviate/Pinecone)
    embedding_model VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_memory_embedding UNIQUE(memory_id, embedding_model)
);

CREATE INDEX idx_embeddings_memory ON memory_embeddings(memory_id);
CREATE INDEX idx_embeddings_vector ON memory_embeddings(vector_id);

-- Memory relationships: Graph connections between memories
CREATE TABLE memory_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memory_records(memory_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('references', 'contradicts', 'supports', 'follows', 'related')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT no_self_reference CHECK (source_memory_id != target_memory_id),
    CONSTRAINT unique_relationship UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

CREATE INDEX idx_relationships_source ON memory_relationships(source_memory_id);
CREATE INDEX idx_relationships_target ON memory_relationships(target_memory_id);
CREATE INDEX idx_relationships_type ON memory_relationships(relationship_type);

-- Data sources: Allowlist of approved information sources
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('api', 'database', 'file_system', 'webhook', 'manual')),
    source_uri TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_ingestion_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_sources_active ON data_sources(is_active);
CREATE INDEX idx_sources_type ON data_sources(source_type);

-- Access policies: Fine-grained access control
CREATE TABLE memory_access_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name VARCHAR(255) NOT NULL UNIQUE,
    policy_rules JSONB NOT NULL,  -- OPA Rego rules
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_policies_active ON memory_access_policies(is_active);
```

---

## AI Prompt

```
You are implementing the Memory Guild Database Schema for the DRYAD.AI agentic system.

CONTEXT:
- This is dependency level 0 (no dependencies)
- Prerequisites: None
- Will be used by: Memory Guild agents (Coordinator, Scribe, Archivist, Librarian) in Levels 1-2

SPECIFICATION:
The Memory Guild database provides the data foundation for agent memory and knowledge management.
It supports:
1. Memory storage with deduplication (content_hash)
2. Vector embeddings for semantic search
3. Knowledge graph relationships between memories
4. Data source tracking and allowlisting
5. Fine-grained access control policies
6. Multi-tenant isolation (tenant_id)

DATABASE SCHEMA:
Implement exactly as specified above:
- memory_records table (core memory storage)
- memory_embeddings table (vector representations)
- memory_relationships table (knowledge graph)
- data_sources table (source allowlist)
- memory_access_policies table (access control)

REQUIREMENTS:
1. Use SQLAlchemy for database models
2. All models should use async SQLAlchemy
3. Implement all foreign key relationships
4. Implement all check constraints
5. Implement all unique constraints
6. Create all indexes for performance
7. Include proper cascade delete behavior
8. Use UUID primary keys (gen_random_uuid())
9. Use TIMESTAMPTZ for all timestamps
10. Include docstrings (Google style)
11. Type hints on all model fields

VALIDATION:
Your implementation must pass these tests:
- [ ] All 5 tables created successfully
- [ ] Foreign key constraints enforced (memory_embeddings → memory_records, etc.)
- [ ] Unique constraints enforced (content_hash per agent/tenant, etc.)
- [ ] Check constraints enforced (source_type enum, relationship_type enum, etc.)
- [ ] No self-referencing relationships allowed (source_memory_id != target_memory_id)
- [ ] Cascade delete works (deleting memory deletes embeddings and relationships)
- [ ] Indexes created for performance
- [ ] Multi-tenant isolation maintained (tenant_id)

CONSTRAINTS:
- Use async/await patterns
- Follow Python 3.11+ best practices
- Use Pydantic v2 for any schemas (if needed)
- Use built-in generics (list[str] not List[str])
- Use | for unions (str | None not Optional[str])

EXAMPLE MEMORY RECORD:
```python
# Example memory record
{
    "agent_id": "agent_123",
    "tenant_id": "tenant_456",
    "source_type": "conversation",
    "content_text": "User prefers dark mode for all interfaces",
    "content_hash": "a1b2c3d4e5f6...",  # MD5 of content_text
    "metadata": {
        "conversation_id": "conv_789",
        "timestamp": "2025-01-10T10:30:00Z",
        "confidence": 0.95
    }
}
```

EXAMPLE MEMORY RELATIONSHIP:
```python
# Example relationship
{
    "source_memory_id": "memory_uuid_1",
    "target_memory_id": "memory_uuid_2",
    "relationship_type": "supports",
    "confidence_score": 0.87
}
```

OUTPUT:
Provide complete, production-ready code for:
1. SQLAlchemy models (app/services/memory_guild/models.py)
   - MemoryRecord model
   - MemoryEmbedding model
   - MemoryRelationship model
   - DataSource model
   - MemoryAccessPolicy model
2. Alembic migration (alembic/versions/xxx_create_memory_guild_tables.py)
3. Model tests (tests/services/memory_guild/test_models.py)
   - Test all constraints
   - Test relationships
   - Test cascade deletes
   - Test multi-tenant isolation
```

---

## Acceptance Criteria

- [ ] All files created as specified
- [ ] Database schema matches specification exactly
- [ ] All 5 tables created
- [ ] All foreign keys, unique constraints, check constraints enforced
- [ ] All indexes created
- [ ] Cascade delete behavior correct
- [ ] Model tests pass (>90% coverage)
- [ ] Multi-tenant isolation validated

---

## Validation Command

```bash
# Create database migration
alembic revision --autogenerate -m "Create memory guild tables"
alembic upgrade head

# Run tests
pytest tests/services/memory_guild/test_models.py -v --cov=app/services/memory_guild/models --cov-report=term-missing

# Validate schema
python scripts/validate_component.py --component memory_guild_schema

# Manual validation
psql -d dryad_db -c "\d memory_records"
psql -d dryad_db -c "\d memory_embeddings"
psql -d dryad_db -c "\d memory_relationships"
psql -d dryad_db -c "\d data_sources"
psql -d dryad_db -c "\d memory_access_policies"
```

---

## Next Steps

After this component is complete and validated:
1. Proceed to other Level 0 components (Tool Registry, Structured Logging)
2. Once all Level 0 components pass validation, proceed to Level 1
3. Memory Guild agents (Coordinator, Scribe) in Level 1 will use this schema
4. Memory Guild agents (Archivist, Librarian) in Level 2 will complete the system

---

## Notes

- This is **data-only** - no API yet (that comes with Memory Guild agents)
- Focus on **schema correctness** - agents depend on exact structure
- **Multi-tenant isolation** is critical for security
- **Deduplication** via content_hash prevents duplicate memories
- **Knowledge graph** via relationships enables multi-hop reasoning

