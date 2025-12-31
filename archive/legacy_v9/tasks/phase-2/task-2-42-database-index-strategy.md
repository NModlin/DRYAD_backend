# Task 2-42: Database Index Strategy

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive database indexing strategy to optimize query performance, including analysis of query patterns, index creation, and monitoring.

---

## 🎯 OBJECTIVES

1. Analyze query patterns
2. Identify missing indexes
3. Create performance indexes
4. Implement composite indexes
5. Monitor index usage
6. Document indexing strategy

---

## 📊 CURRENT STATE

**Existing:**
- Basic primary key indexes
- Some foreign key indexes
- No composite indexes

**Gaps:**
- Missing indexes on frequently queried columns
- No composite indexes for complex queries
- No index usage monitoring

---

## 🔧 IMPLEMENTATION

### 1. Index Analysis Script

Create `scripts/database/analyze-indexes.py`:

```python
#!/usr/bin/env python3
"""
Database Index Analyzer

Analyze query patterns and recommend indexes.
"""
from __future__ import annotations

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def analyze_missing_indexes():
    """Analyze and recommend missing indexes."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    print("🔍 Analyzing database indexes...\n")
    
    # Common query patterns to check
    queries_to_check = [
        ("users", "email", "User login queries"),
        ("conversations", "user_id", "User conversations"),
        ("messages", "conversation_id", "Conversation messages"),
        ("messages", "created_at", "Recent messages"),
        ("documents", "user_id", "User documents"),
        ("document_chunks", "document_id", "Document chunks"),
        ("groves", "client_app_id", "Client groves"),
        ("branches", "grove_id", "Grove branches"),
    ]
    
    recommendations = []
    
    async with engine.begin() as conn:
        for table, column, description in queries_to_check:
            # Check if index exists
            if "postgresql" in settings.DATABASE_URL:
                result = await conn.execute(text(f"""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = '{table}'
                    AND indexdef LIKE '%{column}%'
                """))
            else:  # SQLite
                result = await conn.execute(text(f"""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'index'
                    AND tbl_name = '{table}'
                    AND sql LIKE '%{column}%'
                """))
            
            indexes = result.fetchall()
            
            if not indexes:
                recommendations.append({
                    "table": table,
                    "column": column,
                    "description": description,
                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column});"
                })
    
    await engine.dispose()
    
    # Print recommendations
    if recommendations:
        print("📋 Recommended Indexes:\n")
        for rec in recommendations:
            print(f"  {rec['description']}")
            print(f"  Table: {rec['table']}, Column: {rec['column']}")
            print(f"  SQL: {rec['sql']}\n")
    else:
        print("✅ All recommended indexes exist\n")
    
    return recommendations


if __name__ == "__main__":
    asyncio.run(analyze_missing_indexes())
```

---

### 2. Index Migration

Create `alembic/versions/add_performance_indexes.py`:

```python
"""Add performance indexes

Revision ID: add_performance_indexes
"""
from alembic import op


def upgrade():
    """Add performance indexes."""
    
    # User indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Conversation indexes
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('idx_conversations_user_created', 'conversations', ['user_id', 'created_at'])
    
    # Message indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_conv_created', 'messages', ['conversation_id', 'created_at'])
    
    # Document indexes
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    
    # Document chunk indexes
    op.create_index('idx_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    
    # Grove indexes
    op.create_index('idx_groves_client_app_id', 'groves', ['client_app_id'])
    op.create_index('idx_groves_created_at', 'groves', ['created_at'])
    
    # Branch indexes
    op.create_index('idx_branches_grove_id', 'branches', ['grove_id'])
    op.create_index('idx_branches_status', 'branches', ['status'])
    
    # Multi-tenant indexes
    op.create_index('idx_conversations_tenant', 'conversations', ['tenant_id', 'user_id'])
    op.create_index('idx_documents_tenant', 'documents', ['tenant_id', 'user_id'])


def downgrade():
    """Remove performance indexes."""
    
    # Drop all indexes
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_created_at')
    op.drop_index('idx_conversations_user_id')
    op.drop_index('idx_conversations_created_at')
    op.drop_index('idx_conversations_user_created')
    op.drop_index('idx_messages_conversation_id')
    op.drop_index('idx_messages_created_at')
    op.drop_index('idx_messages_conv_created')
    op.drop_index('idx_documents_user_id')
    op.drop_index('idx_documents_created_at')
    op.drop_index('idx_documents_status')
    op.drop_index('idx_chunks_document_id')
    op.drop_index('idx_chunks_chunk_index')
    op.drop_index('idx_groves_client_app_id')
    op.drop_index('idx_groves_created_at')
    op.drop_index('idx_branches_grove_id')
    op.drop_index('idx_branches_status')
    op.drop_index('idx_conversations_tenant')
    op.drop_index('idx_documents_tenant')
```

---

### 3. Index Monitoring

Create `app/core/index_monitor.py`:

```python
"""
Index Usage Monitoring

Track index usage and performance.
"""
from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class IndexMonitor:
    """Monitor database index usage."""
    
    async def get_index_usage(self, engine: AsyncEngine) -> list[dict]:
        """
        Get index usage statistics (PostgreSQL only).
        
        Args:
            engine: Database engine
        
        Returns:
            List of index usage stats
        """
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 20
            """))
            
            indexes = []
            for row in result:
                indexes.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "index": row.indexname,
                    "scans": row.scans,
                    "tuples_read": row.tuples_read,
                    "tuples_fetched": row.tuples_fetched
                })
            
            return indexes
    
    async def get_unused_indexes(self, engine: AsyncEngine) -> list[dict]:
        """
        Get unused indexes (PostgreSQL only).
        
        Args:
            engine: Database engine
        
        Returns:
            List of unused indexes
        """
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexrelname NOT LIKE '%_pkey'
                ORDER BY pg_relation_size(indexrelid) DESC
            """))
            
            indexes = []
            for row in result:
                indexes.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "index": row.indexname,
                    "size": row.size
                })
            
            return indexes


index_monitor = IndexMonitor()
```

---

### 4. Index Documentation

Create `docs/database/INDEX_STRATEGY.md`:

```markdown
# Database Index Strategy

## Index Types

### Single-Column Indexes
- **Purpose:** Optimize queries filtering on single column
- **Examples:**
  - `idx_users_email` - User login queries
  - `idx_documents_status` - Document status filtering

### Composite Indexes
- **Purpose:** Optimize queries with multiple WHERE conditions
- **Examples:**
  - `idx_conversations_user_created` - User's recent conversations
  - `idx_messages_conv_created` - Conversation's recent messages

### Covering Indexes
- **Purpose:** Include all columns needed by query
- **Example:**
  ```sql
  CREATE INDEX idx_users_email_name ON users(email) INCLUDE (name);
  ```

## Index Guidelines

### When to Add Index
1. Column frequently used in WHERE clauses
2. Column used in JOIN conditions
3. Column used in ORDER BY
4. Foreign key columns
5. Columns with high cardinality

### When NOT to Add Index
1. Small tables (<1000 rows)
2. Columns with low cardinality (few distinct values)
3. Columns rarely queried
4. Tables with frequent writes

## Maintenance

### Analyze Index Usage
```sql
-- PostgreSQL
SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

### Rebuild Indexes
```sql
-- PostgreSQL
REINDEX TABLE users;

-- SQLite
REINDEX;
```

## Performance Impact

### Benefits
- Faster SELECT queries
- Improved JOIN performance
- Better ORDER BY performance

### Costs
- Slower INSERT/UPDATE/DELETE
- Additional storage space
- Index maintenance overhead

## Monitoring

Check index usage monthly:
```bash
python scripts/database/analyze-indexes.py
```
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Index analysis script created
- [ ] Performance indexes added
- [ ] Composite indexes implemented
- [ ] Index monitoring working
- [ ] Unused indexes identified
- [ ] Documentation complete
- [ ] Query performance improved

---

## 🧪 TESTING

```bash
# Analyze indexes
python scripts/database/analyze-indexes.py

# Run migration
alembic upgrade head

# Test query performance
python -m pytest tests/performance/test_query_performance.py
```

---

## 📝 NOTES

- Add indexes based on actual query patterns
- Monitor index usage regularly
- Remove unused indexes
- Use EXPLAIN ANALYZE to verify improvements
- Balance read vs write performance


