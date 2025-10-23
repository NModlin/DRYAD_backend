# AI Task: Structured Logging Service
## Level 0 - Foundation Service

---

## Context

**Dependency Level:** 0 (No dependencies - can build immediately)  
**Prerequisites:** None  
**Integration Points:** Will be used by all components for logging  
**Parallel Work:** Can be built simultaneously with Tool Registry and Memory Guild Database

---

## Specification Reference

See `docs/FInalRoadmap/COMPONENT_SPECIFICATIONS_PART2.md` Section 7 for complete details.

---

## What to Build

### Purpose

System-wide JSON logging with rich metadata for observability and Professor agent analysis. Enables distributed tracing and performance monitoring.

### Files to Create

```
app/services/logging/
├── __init__.py
├── models.py          # SQLAlchemy models for system_logs
├── schemas.py         # Pydantic models for log entries
├── logger.py          # Structured logger implementation
└── query_service.py   # Log querying service

app/api/v1/endpoints/
└── logging.py         # FastAPI router for log API

alembic/versions/
└── xxx_create_logging_tables.py  # Database migration

tests/services/logging/
├── test_logger.py     # Logger tests
└── test_query.py      # Query service tests
```

### Database Schema

```sql
-- System logs: Centralized structured logging
CREATE TABLE system_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    component VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    trace_id VARCHAR(255),
    span_id VARCHAR(255),
    agent_id VARCHAR(255),
    task_id VARCHAR(255)
);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_event_type ON system_logs(event_type);
CREATE INDEX idx_logs_trace ON system_logs(trace_id);
CREATE INDEX idx_logs_agent ON system_logs(agent_id);
CREATE INDEX idx_logs_task ON system_logs(task_id);
```

### API Contract

**Endpoints to implement:**

1. `POST /logs` - Write log entry
2. `GET /logs` - Query logs with filters

See `COMPONENT_SPECIFICATIONS_PART2.md` Section 7 for complete OpenAPI specification.

---

## AI Prompt

```
You are implementing the Structured Logging Service for the DRYAD.AI agentic system.

CONTEXT:
- This is dependency level 0 (no dependencies)
- Prerequisites: None
- Will be used by: All components for system-wide logging
- Critical for: The Lyceum (Level 5) - Professor agents analyze logs

SPECIFICATION:
The Structured Logging Service provides system-wide JSON logging with rich metadata.
It supports:
1. Structured log entries (JSON format)
2. Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
3. Distributed tracing (trace_id, span_id)
4. Component and event type tracking
5. Agent and task correlation
6. High-performance async writes
7. Rich querying capabilities

DATABASE SCHEMA:
Implement exactly as specified above:
- system_logs table with BIGSERIAL primary key (high volume)
- Indexes for common query patterns

API ENDPOINTS:
1. POST /logs - Write log entry
   - Accept structured log data
   - Validate log level
   - Store with timestamp
   - Return 201 on success
   - Async write for performance

2. GET /logs - Query logs
   - Filter by: time range, level, component, event_type, agent_id, task_id, trace_id
   - Support pagination (limit, offset)
   - Return logs in reverse chronological order
   - Default limit: 100, max: 1000

REQUIREMENTS:
1. Use SQLAlchemy for database models
2. Use Pydantic v2 for request/response schemas
3. Use FastAPI for API endpoints
4. Async writes for high performance (>1000 writes/sec)
5. Efficient querying with proper indexes
6. Support distributed tracing (OpenTelemetry compatible)
7. Include Python logging integration (custom handler)
8. Include docstrings (Google style)
9. Type hints on all functions

PYTHON LOGGING INTEGRATION:
Create a custom logging handler that writes to the database:

```python
import logging
from app.services.logging.logger import StructuredLogger

# Usage in other components
logger = StructuredLogger(component="tool_registry")

logger.info(
    event_type="tool_registered",
    message="Tool registered successfully",
    metadata={
        "tool_id": "uuid",
        "tool_name": "code_executor",
        "version": "1.0.0"
    },
    trace_id="trace_123",
    agent_id="agent_456"
)
```

VALIDATION:
Your implementation must pass these tests:
- [ ] Can write structured log entries
- [ ] Can query logs by time range
- [ ] Can filter logs by level
- [ ] Can filter logs by component
- [ ] Can filter logs by agent_id
- [ ] Can filter logs by trace_id
- [ ] Supports distributed tracing
- [ ] High-performance writes (>1000/sec)
- [ ] Pagination works correctly
- [ ] Log levels enforced (enum constraint)

CONSTRAINTS:
- Use async/await patterns throughout
- Follow Python 3.11+ best practices
- Use Pydantic v2 models
- Use built-in generics (list[str] not List[str])
- Use | for unions (str | None not Optional[str])
- Optimize for write performance (logs are high volume)

EXAMPLE LOG ENTRY:
```python
{
    "level": "INFO",
    "component": "sandbox",
    "event_type": "tool_execution_started",
    "message": "Starting tool execution",
    "metadata": {
        "tool_id": "uuid",
        "tool_name": "code_executor",
        "agent_id": "agent_123",
        "input_size_bytes": 1024
    },
    "trace_id": "trace_abc123",
    "span_id": "span_def456",
    "agent_id": "agent_123",
    "task_id": "task_789"
}
```

EXAMPLE QUERY:
```python
# Query logs for specific agent in last hour
GET /logs?agent_id=agent_123&start_time=2025-01-10T09:00:00Z&end_time=2025-01-10T10:00:00Z&limit=100

# Query error logs for specific component
GET /logs?component=sandbox&level=ERROR&limit=50

# Query logs for distributed trace
GET /logs?trace_id=trace_abc123
```

OUTPUT:
Provide complete, production-ready code for all files listed in "Files to Create".
Include:
1. SQLAlchemy models (app/services/logging/models.py)
2. Pydantic schemas (app/services/logging/schemas.py)
3. Structured logger (app/services/logging/logger.py)
4. Query service (app/services/logging/query_service.py)
5. FastAPI router (app/api/v1/endpoints/logging.py)
6. Alembic migration (alembic/versions/xxx_create_logging_tables.py)
7. Comprehensive tests (tests/services/logging/)
```

---

## Acceptance Criteria

- [ ] All files created as specified
- [ ] Database schema matches specification exactly
- [ ] API contract matches specification exactly
- [ ] Both endpoints functional (POST /logs, GET /logs)
- [ ] Python logging integration works
- [ ] Distributed tracing supported
- [ ] High-performance writes (>1000/sec)
- [ ] Query filtering works correctly
- [ ] Unit test coverage >90%
- [ ] Integration tests pass

---

## Validation Command

```bash
# Create database migration
alembic revision --autogenerate -m "Create logging tables"
alembic upgrade head

# Run tests
pytest tests/services/logging/ -v --cov=app/services/logging --cov-report=term-missing

# Performance test
python scripts/test_logging_performance.py  # Should achieve >1000 writes/sec

# Validate Level 0 component
python scripts/validate_component.py --component structured_logging

# Manual API testing
curl -X POST http://localhost:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "component": "test",
    "event_type": "test_event",
    "message": "Test log entry"
  }'

curl "http://localhost:8000/api/v1/logs?component=test&limit=10"
```

---

## Next Steps

After this component is complete and validated:
1. Proceed to other Level 0 components (Tool Registry, Memory Guild Database)
2. Once all Level 0 components pass validation, proceed to Level 1
3. All subsequent components will use this logging service
4. The Lyceum (Level 5) will analyze these logs for improvement opportunities

---

## Notes

- This is **critical for observability** - all components depend on it
- **Performance is key** - logs are high volume
- **Distributed tracing** enables request correlation across services
- **The Lyceum** will analyze these logs to identify performance bottlenecks
- Consider **log retention policies** (e.g., keep 30 days, archive older)
- Consider **log aggregation** for production (e.g., ship to ELK stack)

