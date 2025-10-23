# DRYAD.AI API Endpoints Reference

**Version:** 1.0  
**Base URL:** `https://api.dryad.ai/v1`  
**Last Updated:** 2025-10-13

---

## Table of Contents

1. [Health & Status](#health--status)
2. [Agents](#agents)
3. [Workflows](#workflows)
4. [Memory](#memory)
5. [Tools](#tools)
6. [Execution](#execution)
7. [Evaluation](#evaluation)

---

## Health & Status

### GET /health

Check API health status.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-13T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "chromadb": "healthy"
  }
}
```

### GET /metrics

Prometheus metrics endpoint.

**Authentication:** None required (internal only)

---

## Agents

### GET /agents

List all registered agents.

**Authentication:** Required  
**Scopes:** `read`

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `capability` (string): Filter by capability
- `status` (string): Filter by status (active, inactive)

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_123",
      "name": "Code Analyzer",
      "description": "Analyzes code quality and suggests improvements",
      "capabilities": ["code_analysis", "refactoring"],
      "status": "active",
      "created_at": "2025-10-13T10:00:00Z",
      "updated_at": "2025-10-13T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

### GET /agents/{agent_id}

Get agent details.

**Authentication:** Required  
**Scopes:** `read`

**Path Parameters:**
- `agent_id` (string): Agent ID

**Response:**
```json
{
  "id": "agent_123",
  "name": "Code Analyzer",
  "description": "Analyzes code quality and suggests improvements",
  "capabilities": ["code_analysis", "refactoring"],
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "status": "active",
  "metrics": {
    "total_executions": 1234,
    "success_rate": 0.95,
    "avg_duration_ms": 1500
  },
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T10:00:00Z"
}
```

### POST /agents

Register a new agent.

**Authentication:** Required  
**Scopes:** `write`

**Request Body:**
```json
{
  "name": "Code Analyzer",
  "description": "Analyzes code quality and suggests improvements",
  "capabilities": ["code_analysis", "refactoring"],
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

**Response:** 201 Created
```json
{
  "id": "agent_123",
  "name": "Code Analyzer",
  "status": "active",
  "created_at": "2025-10-13T10:00:00Z"
}
```

### PUT /agents/{agent_id}

Update agent configuration.

**Authentication:** Required  
**Scopes:** `write`

**Request Body:**
```json
{
  "description": "Updated description",
  "configuration": {
    "temperature": 0.8
  }
}
```

**Response:** 200 OK

### DELETE /agents/{agent_id}

Delete an agent.

**Authentication:** Required  
**Scopes:** `delete`

**Response:** 204 No Content

---

## Workflows

### POST /workflows

Execute a workflow.

**Authentication:** Required  
**Scopes:** `write`

**Request Body:**
```json
{
  "task": "Analyze the codebase and suggest improvements",
  "context": {
    "repository": "https://github.com/user/repo",
    "branch": "main"
  },
  "agents": ["agent_123", "agent_456"],
  "options": {
    "max_iterations": 5,
    "timeout_seconds": 300
  }
}
```

**Response:** 202 Accepted
```json
{
  "workflow_id": "wf_789",
  "status": "running",
  "created_at": "2025-10-13T10:00:00Z",
  "estimated_completion": "2025-10-13T10:05:00Z"
}
```

### GET /workflows/{workflow_id}

Get workflow status and results.

**Authentication:** Required  
**Scopes:** `read`

**Response:**
```json
{
  "workflow_id": "wf_789",
  "status": "completed",
  "task": "Analyze the codebase and suggest improvements",
  "result": {
    "summary": "Found 15 issues and 8 improvement opportunities",
    "details": { ... },
    "recommendations": [ ... ]
  },
  "execution_time_ms": 4500,
  "created_at": "2025-10-13T10:00:00Z",
  "completed_at": "2025-10-13T10:04:30Z"
}
```

### GET /workflows

List workflows.

**Authentication:** Required  
**Scopes:** `read`

**Query Parameters:**
- `status` (string): Filter by status (running, completed, failed)
- `page` (integer): Page number
- `limit` (integer): Items per page

**Response:**
```json
{
  "workflows": [ ... ],
  "pagination": { ... }
}
```

---

## Memory

### POST /memory

Store content in memory.

**Authentication:** Required  
**Scopes:** `write`

**Request Body:**
```json
{
  "content": "Important information to remember",
  "metadata": {
    "source": "user_input",
    "category": "notes"
  },
  "memory_type": "long_term",
  "ttl_seconds": 86400
}
```

**Response:** 201 Created
```json
{
  "memory_id": "mem_abc123",
  "content_hash": "sha256:...",
  "stored_at": "2025-10-13T10:00:00Z",
  "expires_at": "2025-10-14T10:00:00Z"
}
```

### GET /memory/{memory_id}

Retrieve memory by ID.

**Authentication:** Required  
**Scopes:** `read`

**Response:**
```json
{
  "memory_id": "mem_abc123",
  "content": "Important information to remember",
  "metadata": {
    "source": "user_input",
    "category": "notes"
  },
  "created_at": "2025-10-13T10:00:00Z",
  "expires_at": "2025-10-14T10:00:00Z"
}
```

### POST /memory/search

Search memory with semantic search.

**Authentication:** Required  
**Scopes:** `read`

**Request Body:**
```json
{
  "query": "What did we discuss about code quality?",
  "limit": 10,
  "filters": {
    "category": "notes",
    "created_after": "2025-10-01T00:00:00Z"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "memory_id": "mem_abc123",
      "content": "Important information to remember",
      "score": 0.95,
      "metadata": { ... }
    }
  ],
  "total": 5
}
```

### DELETE /memory/{memory_id}

Delete memory.

**Authentication:** Required  
**Scopes:** `delete`

**Response:** 204 No Content

---

## Tools

### GET /tools

List available tools.

**Authentication:** Required  
**Scopes:** `read`

**Response:**
```json
{
  "tools": [
    {
      "id": "tool_123",
      "name": "code_executor",
      "description": "Execute code in a sandboxed environment",
      "parameters": {
        "language": "string",
        "code": "string",
        "timeout": "integer"
      },
      "permissions": ["execute"]
    }
  ]
}
```

### POST /tools/{tool_id}/execute

Execute a tool.

**Authentication:** Required  
**Scopes:** `write`, tool-specific permissions

**Request Body:**
```json
{
  "parameters": {
    "language": "python",
    "code": "print('Hello, World!')",
    "timeout": 30
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_456",
  "result": {
    "stdout": "Hello, World!\n",
    "stderr": "",
    "exit_code": 0
  },
  "execution_time_ms": 150
}
```

---

## Execution

### POST /execute

Execute code in sandbox.

**Authentication:** Required  
**Scopes:** `execute`

**Request Body:**
```json
{
  "language": "python",
  "code": "print('Hello, World!')",
  "timeout": 30,
  "environment": {
    "CUSTOM_VAR": "value"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_789",
  "stdout": "Hello, World!\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 150
}
```

---

## Evaluation

### POST /evaluate

Evaluate agent performance.

**Authentication:** Required  
**Scopes:** `write`

**Request Body:**
```json
{
  "agent_id": "agent_123",
  "benchmark": "code_quality",
  "test_cases": [ ... ]
}
```

**Response:**
```json
{
  "evaluation_id": "eval_999",
  "status": "running",
  "created_at": "2025-10-13T10:00:00Z"
}
```

### GET /evaluate/{evaluation_id}

Get evaluation results.

**Authentication:** Required  
**Scopes:** `read`

**Response:**
```json
{
  "evaluation_id": "eval_999",
  "status": "completed",
  "results": {
    "score": 0.92,
    "passed": 45,
    "failed": 5,
    "details": [ ... ]
  },
  "completed_at": "2025-10-13T10:10:00Z"
}
```

---

## Common Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 202 | Accepted | Request accepted, processing async |
| 204 | No Content | Request successful, no content to return |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Rate Limiting

All endpoints are rate limited:

- **Free tier:** 100 requests/minute
- **Pro tier:** 1000 requests/minute
- **Enterprise:** Custom limits

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699999999
```

---

**Last Updated:** 2025-10-13  
**API Version:** 1.0

