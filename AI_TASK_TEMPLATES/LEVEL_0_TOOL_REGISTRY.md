# AI Task: Tool Registry Service
## Level 0 - Foundation Service

---

## Context

**Dependency Level:** 0 (No dependencies - can build immediately)  
**Prerequisites:** None  
**Integration Points:** Will be consumed by Sandboxed Execution (Level 1) and Orchestration (Level 3)  
**Parallel Work:** Can be built simultaneously with Memory Guild Database and Structured Logging

---

## Specification Reference

See `docs/FInalRoadmap/COMPONENT_SPECIFICATIONS.md` Section 1.1 for complete details.

---

## What to Build

### Purpose

Centralized, version-controlled repository for all available tools. Acts as single source of truth for tool definitions, eliminating ambiguity and providing robust governance.

### Files to Create

```
app/services/tool_registry/
├── __init__.py
├── models.py          # SQLAlchemy models for tools, tool_permissions
├── schemas.py         # Pydantic models for API validation
├── service.py         # Business logic (CRUD operations, validation)
└── exceptions.py      # Custom exceptions (ToolNotFoundError, etc.)

app/api/v1/endpoints/
└── tool_registry.py   # FastAPI router with all endpoints

alembic/versions/
└── xxx_create_tool_registry_tables.py  # Database migration

tests/services/tool_registry/
├── test_models.py     # SQLAlchemy model tests
├── test_service.py    # Service layer tests
└── test_api.py        # API endpoint tests
```

### Database Schema

```sql
-- Tools table: Primary tool definitions
CREATE TABLE tools (
    tool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    schema_json JSONB NOT NULL,  -- OpenAPI 3.0 specification
    docker_image_uri VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT unique_tool_version UNIQUE(name, version)
);

CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_version ON tools(version);
CREATE INDEX idx_tools_active ON tools(is_active);
CREATE INDEX idx_tools_created ON tools(created_at DESC);

-- Tool permissions: Access control linking agents/roles to tools
CREATE TABLE tool_permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id VARCHAR(255) NOT NULL,
    principal_type VARCHAR(20) NOT NULL CHECK (principal_type IN ('agent', 'role')),
    tool_id UUID NOT NULL REFERENCES tools(tool_id) ON DELETE CASCADE,
    allow_stateful_execution BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    CONSTRAINT unique_principal_tool UNIQUE(principal_id, principal_type, tool_id)
);

CREATE INDEX idx_tool_permissions_principal ON tool_permissions(principal_id, principal_type);
CREATE INDEX idx_tool_permissions_tool ON tool_permissions(tool_id);
```

### API Contract

**Endpoints to implement:**

1. `POST /tools` - Register new tool
2. `GET /tools` - List all tools (with pagination)
3. `GET /tools/{name}` - Get all versions of a tool
4. `GET /tools/{name}/{version}` - Get specific tool version
5. `PUT /tools/{name}/{version}` - Update tool metadata (not schema/version)
6. `POST /tools/{name}/{version}/permissions` - Grant permission
7. `GET /tools/{name}/{version}/permissions` - List permissions

See `COMPONENT_SPECIFICATIONS.md` Section 1.1 for complete OpenAPI 3.0 specification.

### Integration Requirements

**Consumers (will integrate later):**
- Sandboxed Execution Environment (Level 1) - fetches tool definitions
- Orchestrator (Level 3) - discovers available tools
- Permission system - validates tool access

**No dependencies** - This is a Level 0 component.

---

## AI Prompt

```
You are implementing the Tool Registry Service for the DRYAD.AI agentic system.

CONTEXT:
- This is dependency level 0 (no dependencies)
- Prerequisites: None
- Will be consumed by: Sandboxed Execution (Level 1), Orchestration (Level 3)

SPECIFICATION:
The Tool Registry is a centralized, version-controlled repository for all available tools.
It provides:
1. Tool registration with OpenAPI 3.0 schema validation
2. Version management (semantic versioning)
3. Permission management (agent/role-based access control)
4. Tool discovery and retrieval

DATABASE SCHEMA:
Implement exactly as specified above:
- tools table (tool_id, name, version, schema_json, docker_image_uri, etc.)
- tool_permissions table (permission_id, principal_id, tool_id, etc.)

API ENDPOINTS:
Implement all 7 endpoints as specified in COMPONENT_SPECIFICATIONS.md Section 1.1:
1. POST /tools - Register new tool
   - Validate OpenAPI 3.0 schema in schema_json field
   - Enforce unique (name, version) constraint
   - Return 201 with tool_id on success
   - Return 400 if schema invalid
   - Return 409 if duplicate name/version

2. GET /tools - List all tools
   - Support pagination (limit, offset)
   - Support filtering (active_only)
   - Return array of tools with total count

3. GET /tools/{name} - Get all versions of a tool
   - Return array of all versions for given name
   - Return 404 if tool name not found

4. GET /tools/{name}/{version} - Get specific version
   - Return complete tool definition
   - Return 404 if not found

5. PUT /tools/{name}/{version} - Update metadata
   - Allow updating: description, is_active, docker_image_uri
   - Do NOT allow updating: name, version, schema_json (immutable)
   - Return 400 if attempting to update immutable fields

6. POST /tools/{name}/{version}/permissions - Grant permission
   - Create permission for agent or role
   - Enforce unique (principal_id, principal_type, tool_id)
   - Return 409 if permission already exists

7. GET /tools/{name}/{version}/permissions - List permissions
   - Return array of all permissions for tool

REQUIREMENTS:
1. Use SQLAlchemy for database models
2. Use Pydantic v2 for request/response schemas
3. Use FastAPI for API endpoints
4. Follow existing codebase patterns in app/services/
5. All database operations should be async (use async SQLAlchemy)
6. Include comprehensive error handling
7. Validate OpenAPI 3.0 schemas using jsonschema library
8. Include docstrings (Google style)
9. Type hints on all functions

VALIDATION:
Your implementation must pass these tests:
- [ ] Can register a tool with valid OpenAPI 3.0 schema
- [ ] Can retrieve tool by name and version
- [ ] Can list all versions of a tool
- [ ] Can update tool metadata (description, active status)
- [ ] Cannot update tool schema or version (immutable)
- [ ] Can grant permissions to agents and roles
- [ ] Can list permissions for a tool
- [ ] Invalid schemas are rejected with clear error messages
- [ ] Duplicate tool name/version combinations are rejected (409)
- [ ] Database constraints are enforced (foreign keys, unique constraints)

CONSTRAINTS:
- Use async/await patterns throughout
- Follow Python 3.11+ best practices
- Use Pydantic v2 models (not v1)
- Use built-in generics (list[str] not List[str])
- Use | for unions (str | None not Optional[str])
- Use pathlib.Path for file paths
- Include comprehensive logging

EXAMPLE TOOL REGISTRATION:
```python
# Example tool schema (OpenAPI 3.0)
{
    "name": "code_executor",
    "version": "1.0.0",
    "description": "Executes Python code in isolated environment",
    "schema_json": {
        "openapi": "3.0.0",
        "info": {
            "title": "Code Executor",
            "version": "1.0.0"
        },
        "paths": {
            "/execute": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "code": {"type": "string"},
                                        "language": {"type": "string", "enum": ["python", "javascript"]}
                                    },
                                    "required": ["code"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "output": {"type": "string"},
                                            "exit_code": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "docker_image_uri": "registry.example.com/tools/code-executor:1.0.0"
}
```

OUTPUT:
Provide complete, production-ready code for all files listed in "Files to Create".
Include:
1. SQLAlchemy models (app/services/tool_registry/models.py)
2. Pydantic schemas (app/services/tool_registry/schemas.py)
3. Service layer (app/services/tool_registry/service.py)
4. Custom exceptions (app/services/tool_registry/exceptions.py)
5. FastAPI router (app/api/v1/endpoints/tool_registry.py)
6. Alembic migration (alembic/versions/xxx_create_tool_registry_tables.py)
7. Comprehensive tests (tests/services/tool_registry/)
```

---

## Acceptance Criteria

- [ ] All files created as specified
- [ ] Database schema matches specification exactly
- [ ] API contract matches specification exactly
- [ ] All 7 endpoints functional
- [ ] OpenAPI 3.0 schema validation works
- [ ] Permission system functional
- [ ] Unit test coverage >90%
- [ ] Integration tests pass
- [ ] All validation criteria met

---

## Validation Command

```bash
# Create database migration
alembic revision --autogenerate -m "Create tool registry tables"
alembic upgrade head

# Run tests
pytest tests/services/tool_registry/ -v --cov=app/services/tool_registry --cov-report=term-missing

# Validate Level 0 component
python scripts/validate_component.py --component tool_registry

# Manual API testing
# Start server: uvicorn app.main:app --reload
# Test endpoints with curl or Postman
```

---

## Next Steps

After this component is complete and validated:
1. Proceed to other Level 0 components (Memory Guild Database, Structured Logging)
2. Once all Level 0 components pass validation, proceed to Level 1
3. Sandboxed Execution (Level 1) will integrate with this Tool Registry

---

## Notes

- This is a **critical path component** - Sandbox and Orchestration depend on it
- Focus on **correctness** over speed - AI can code fast, but bugs are costly
- **Exact schema compliance** is essential for integration
- **Comprehensive tests** prevent rework later

