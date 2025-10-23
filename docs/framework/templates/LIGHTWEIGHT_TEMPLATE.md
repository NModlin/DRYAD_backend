# Lightweight DRYAD Template

**Version:** 2.0.0  
**Use Case:** Simple agentic systems, single-agent automation  
**Complexity:** Low  
**Estimated Setup Time:** 2-4 hours

---

## Overview

The **Lightweight DRYAD Template** provides a minimal but functional agentic system using only **Levels 0-2**:

- **Level 0:** Tool Registry, Memory Database, Logging
- **Level 1:** Memory Coordinator, Memory Scribe, Agent Registry
- **Level 2:** Archivist (short-term memory only)

**Perfect for:**
- Single-agent task automation
- Simple chatbots
- Document processing pipelines
- Basic RAG systems

---

## Architecture

```
┌─────────────────────────────────────┐
│      Your Application               │
│  (Agent, Chatbot, Automation)       │
└────────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼────────┐
│ Tool Registry│  │ Memory Guild  │
│ (Level 0)    │  │ (Levels 1-2)  │
└───────┬──────┘  └──────┬────────┘
        │                │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │  PostgreSQL     │
        │  Redis (opt.)   │
        └─────────────────┘
```

---

## File Structure

```
your-project/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tool_registry.py       # Level 0
│   │   ├── memory_guild.py        # Levels 1-2
│   │   └── logging.py             # Level 0
│   └── api/
│       ├── __init__.py
│       └── endpoints.py           # API routes
├── database/
│   ├── __init__.py
│   ├── models.py                  # SQLAlchemy models
│   └── session.py                 # DB connection
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Core Components

### 1. Tool Registry (Level 0)

```python
# app/services/tool_registry.py
from typing import Dict, List, Optional
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    parameters: Dict
    handler: callable

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        """Register a tool"""
        self.tools[tool.id] = tool
    
    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get tool by ID"""
        return self.tools.get(tool_id)
    
    def list(self) -> List[ToolDefinition]:
        """List all tools"""
        return list(self.tools.values())
    
    async def execute(self, tool_id: str, params: Dict):
        """Execute a tool"""
        tool = self.get(tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        return await tool.handler(**params)
```

### 2. Memory Guild (Levels 1-2)

```python
# app/services/memory_guild.py
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
import json

class MemoryCoordinator:
    """Routes memory requests"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.mock_storage: Dict = {}
    
    async def store(
        self,
        key: str,
        value: Dict,
        ttl_seconds: int = 3600
    ) -> bool:
        """Store in short-term memory"""
        if self.redis:
            await self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(value)
            )
        else:
            # Mock mode
            expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            self.mock_storage[key] = (value, expiry)
        return True
    
    async def retrieve(self, key: str) -> Optional[Dict]:
        """Retrieve from short-term memory"""
        if self.redis:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        else:
            # Mock mode
            value, expiry = self.mock_storage.get(key, (None, None))
            if expiry and datetime.now(timezone.utc) > expiry:
                del self.mock_storage[key]
                return None
            return value
```

### 3. Logging (Level 0)

```python
# app/services/logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_info(self, event: str, data: Dict):
        """Log info event"""
        self.logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }))
    
    def log_error(self, event: str, data: Dict):
        """Log error event"""
        self.logger.error(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }))
```

---

## Database Setup

### PostgreSQL Schema

```sql
-- Memory records table
CREATE TABLE memory_records (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    ttl_seconds INT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_memory_key ON memory_records(key);
CREATE INDEX idx_memory_expires ON memory_records(expires_at);
```

---

## API Endpoints

```python
# app/api/endpoints.py
from fastapi import FastAPI, HTTPException
from app.services.tool_registry import ToolRegistry
from app.services.memory_guild import MemoryCoordinator

app = FastAPI()
tool_registry = ToolRegistry()
memory = MemoryCoordinator()

@app.post("/tools/register")
async def register_tool(tool: ToolDefinition):
    """Register a new tool"""
    tool_registry.register(tool)
    return {"id": tool.id, "status": "registered"}

@app.post("/tools/execute")
async def execute_tool(tool_id: str, params: Dict):
    """Execute a tool"""
    result = await tool_registry.execute(tool_id, params)
    return {"result": result}

@app.post("/memory/store")
async def store_memory(key: str, value: Dict, ttl: int = 3600):
    """Store in memory"""
    await memory.store(key, value, ttl)
    return {"status": "stored"}

@app.get("/memory/retrieve/{key}")
async def retrieve_memory(key: str):
    """Retrieve from memory"""
    value = await memory.retrieve(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"value": value}
```

---

## Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/dryad
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dryad
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## Deployment

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start services
docker-compose up

# 3. Run application
python -m uvicorn app.main:app --reload
```

### Production
```bash
# 1. Build image
docker build -t my-agent:latest .

# 2. Deploy
docker-compose -f docker-compose.yml up -d

# 3. Verify
curl http://localhost:8000/health
```

---

## Example: Simple Chatbot

```python
# Example usage
from app.services.tool_registry import ToolRegistry
from app.services.memory_guild import MemoryCoordinator

async def simple_chatbot():
    registry = ToolRegistry()
    memory = MemoryCoordinator()
    
    # Register tools
    registry.register(ToolDefinition(
        id="search",
        name="Search",
        description="Search the web",
        parameters={"query": str},
        handler=search_web
    ))
    
    # Store conversation context
    await memory.store(
        "conversation_1",
        {"messages": ["Hello", "Hi there!"]},
        ttl_seconds=3600
    )
    
    # Retrieve context
    context = await memory.retrieve("conversation_1")
    print(context)
```

---

## Next Steps

1. **Customize tools** - Add your specific tools
2. **Add authentication** - Secure your API
3. **Scale to full DRYAD** - Add Levels 3-5 as needed
4. **Deploy to production** - Use Kubernetes or cloud platform

---

## Limitations

- No multi-agent orchestration (Level 3)
- No evaluation framework (Level 4)
- No self-improvement (Level 5)
- Single-node only
- Limited to short-term memory

---

## When to Upgrade to Full DRYAD

- Need multi-agent collaboration
- Want agent evaluation and benchmarking
- Need autonomous improvement
- Require complex orchestration
- Need human-in-the-loop oversight

See **[Full Framework Template](FULL_FRAMEWORK_TEMPLATE.md)** for complete system.


