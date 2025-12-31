# Task 2-02: Database Query Optimization

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5  
**Estimated Hours:** 6 hours  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Optimize database queries through indexing, query analysis, and N+1 query elimination.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Analyze slow queries
- Add database indexes
- Eliminate N+1 queries
- Optimize joins
- Add query monitoring

### Technical Requirements
- PostgreSQL EXPLAIN ANALYZE
- SQLAlchemy query optimization
- Index creation
- Query profiling

### Performance Requirements
- Query time: <50ms (P95)
- Index usage: >90%
- N+1 queries: 0

---

## 🔧 IMPLEMENTATION

**File:** `alembic/versions/xxx_add_performance_indexes.py`

```python
"""Add performance indexes"""

from alembic import op


def upgrade():
    """Add indexes for performance."""
    # Agent execution indexes
    op.create_index(
        'idx_agent_executions_agent_id_created',
        'agent_executions',
        ['agent_id', 'created_at'],
    )
    
    op.create_index(
        'idx_agent_executions_status',
        'agent_executions',
        ['status'],
    )
    
    op.create_index(
        'idx_agent_executions_user_id',
        'agent_executions',
        ['user_id'],
    )
    
    # Sandbox indexes
    op.create_index(
        'idx_sandboxes_expires_at',
        'sandboxes',
        ['expires_at'],
        postgresql_where="status = 'ACTIVE'",
    )


def downgrade():
    """Remove indexes."""
    op.drop_index('idx_agent_executions_agent_id_created')
    op.drop_index('idx_agent_executions_status')
    op.drop_index('idx_agent_executions_user_id')
    op.drop_index('idx_sandboxes_expires_at')
```

**File:** `app/services/optimized_queries.py`

```python
"""Optimized Database Queries"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def get_agent_with_executions(agent_id: UUID):
    """Get agent with executions - optimized."""
    # ✅ Use selectinload to avoid N+1
    query = (
        select(Agent)
        .where(Agent.id == agent_id)
        .options(selectinload(Agent.executions))
    )
    
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

---

## ✅ DEFINITION OF DONE

- [ ] Slow queries identified
- [ ] Indexes added
- [ ] N+1 queries eliminated
- [ ] Query performance improved
- [ ] Monitoring configured

---

## 📊 SUCCESS METRICS

- Query time: <50ms (P95)
- Index usage: >90%
- N+1 queries: 0

---

**Estimated Completion:** 6 hours  
**Status:** NOT STARTED

