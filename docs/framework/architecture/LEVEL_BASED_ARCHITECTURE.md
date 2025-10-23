# Level-Based Architecture Deep Dive

**Version:** 2.0.0  
**Status:** Production Ready

---

## Overview

DRYAD uses a **dependency-driven architecture** with 6 levels. Each level builds on previous levels, enabling:
- Parallel development
- Clear dependencies
- Modular deployment
- Progressive complexity

---

## Level 0: Foundation Services

### Purpose
Provide core infrastructure that all other levels depend on.

### Components

#### 1. Tool Registry
**File:** `app/services/tool_registry/service.py`

```python
class ToolRegistryService:
    """Centralized tool management"""
    
    async def register_tool(self, tool: ToolDefinition) -> str:
        """Register a new tool"""
        
    async def get_tool(self, tool_id: str) -> ToolDefinition:
        """Retrieve tool definition"""
        
    async def list_tools(self, filters: Dict) -> List[ToolDefinition]:
        """List available tools"""
        
    async def validate_tool(self, tool: ToolDefinition) -> bool:
        """Validate tool definition"""
```

**Responsibilities:**
- Store tool definitions
- Validate tool schemas
- Manage tool permissions
- Track tool versions

#### 2. Memory Database
**File:** `app/services/memory_guild/models.py`

**Tables:**
- `memory_records` - Core memory storage
- `memory_embeddings` - Vector embeddings
- `memory_relationships` - Knowledge graph
- `data_sources` - Data source tracking
- `memory_access_policies` - Access control

**Key Features:**
- Multi-tenant isolation
- Content deduplication (MD5 hash)
- Soft deletion support
- Timestamp tracking

#### 3. Structured Logging
**File:** `app/services/logging/logger.py`

```python
class StructuredLogger:
    """Comprehensive event logging"""
    
    def log_info(self, event: str, data: Dict):
        """Log info event"""
        
    def log_warning(self, event: str, data: Dict):
        """Log warning event"""
        
    def log_error(self, event: str, data: Dict):
        """Log error event"""
```

**Capabilities:**
- Structured JSON logging
- Event tracking
- Performance metrics
- Error tracking

---

## Level 1: Execution & Memory Agents

### Purpose
Enable safe code execution and memory management.

### Components

#### 1. Sandbox Service
**File:** `app/services/sandbox_service.py`

```python
class SandboxService:
    """Isolated code execution"""
    
    async def execute_tool(
        self,
        tool_id: str,
        params: Dict,
        timeout: int = 30
    ) -> ExecutionResult:
        """Execute tool in isolated environment"""
```

**Features:**
- Docker-based isolation
- Resource limits
- Timeout enforcement
- Error capture

#### 2. Memory Coordinator
**File:** `app/services/memory_guild/coordinator.py`

```python
class MemoryCoordinatorAgent:
    """Routes memory requests"""
    
    async def handle_memory_request(
        self,
        request: MemoryRequest
    ) -> MemoryResponse:
        """Route to Archivist or Librarian"""
```

**Responsibilities:**
- Route to short-term (Archivist)
- Route to long-term (Librarian)
- Enforce access policies
- Manage memory lifecycle

#### 3. Memory Scribe
**File:** `app/services/memory_guild/scribe.py`

```python
class MemoryScribeAgent:
    """Ingests and processes data"""
    
    async def ingest_content(
        self,
        content: str,
        source: str,
        metadata: Dict
    ) -> MemoryResponse:
        """Ingest new content"""
```

**Features:**
- Content deduplication
- Embedding generation
- Metadata extraction
- Source tracking

#### 4. Agent Registry
**File:** `app/services/agent_registry_service.py`

```python
class AgentRegistryService:
    """Tracks available agents"""
    
    async def register_agent(self, agent: AgentDefinition) -> str:
        """Register new agent"""
        
    async def discover_agents(self, filters: Dict) -> List[Agent]:
        """Discover agents by capability"""
```

---

## Level 2: Stateful Operations

### Purpose
Manage persistent memory with different retention strategies.

### Components

#### 1. Archivist Agent
**File:** `app/services/memory_guild/archivist.py`

```python
class ArchivistAgent:
    """Short-term memory management"""
    
    async def store(
        self,
        key: str,
        value: Dict,
        ttl: timedelta,
        tenant_id: str
    ) -> bool:
        """Store with TTL"""
        
    async def retrieve(
        self,
        key: str,
        tenant_id: str
    ) -> Optional[Dict]:
        """Retrieve before expiration"""
```

**Storage:** Redis (with mock fallback)  
**TTL:** Configurable (default 1 hour)  
**Use Cases:** Active workflows, recent context

#### 2. Librarian Agent
**File:** `app/services/memory_guild/librarian.py`

```python
class LibrarianAgent:
    """Long-term memory management"""
    
    async def store(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict,
        tenant_id: str
    ) -> str:
        """Store with semantic indexing"""
        
    async def search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 10
    ) -> List[SearchResult]:
        """Semantic search"""
```

**Storage:** ChromaDB (with mock fallback)  
**Retention:** Permanent (configurable)  
**Use Cases:** Knowledge base, historical context

---

## Level 3: Orchestration & HITL

### Purpose
Intelligently route tasks and provide human oversight.

### Components

#### 1. Complexity Scorer
**File:** `app/services/orchestration/complexity_scorer.py`

Analyzes task complexity to determine execution strategy.

#### 2. Decision Engine
**File:** `app/services/orchestration/decision_engine.py`

Routes tasks based on complexity and capabilities.

#### 3. Task Force Manager
**File:** `app/services/orchestration/task_force_manager.py`

Coordinates multi-agent collaboration.

#### 4. Hybrid Orchestrator
**File:** `app/services/orchestration/orchestrator.py`

Main orchestration engine.

#### 5. HITL System
**File:** `app/services/hitl/`

Provides human-in-the-loop oversight.

---

## Level 4: The Dojo (Evaluation)

### Purpose
Measure and track agent performance.

### Components

#### 1. Benchmark Registry
**File:** `app/services/dojo/benchmark_registry.py`

Stores standardized evaluation problems.

#### 2. Evaluation Harness
**File:** `app/services/dojo/evaluation_harness.py`

Executes evaluations and tracks results.

#### 3. RAG-Gym Benchmarks
Specialized benchmarks for Memory Guild.

---

## Level 5: The Lyceum (Self-Improvement)

### Purpose
Enable autonomous agent improvement.

### Components

#### 1. Laboratory Sandbox
**File:** `app/services/lyceum/environment_manager.py`

Isolated improvement environment.

#### 2. Professor Agent
**File:** `app/services/lyceum/professor_agent.py`

Analyzes performance and suggests improvements.

#### 3. Budget Manager
**File:** `app/services/lyceum/budget_manager.py`

Manages improvement resources.

---

## Dependency Graph

```
Level 5: Lyceum
    ↑
    └─ Depends on Level 4

Level 4: Dojo
    ↑
    └─ Depends on Level 3

Level 3: Orchestration
    ↑
    └─ Depends on Level 2

Level 2: Stateful Operations
    ↑
    └─ Depends on Level 1

Level 1: Execution & Memory
    ↑
    └─ Depends on Level 0

Level 0: Foundation
    ↑
    └─ No dependencies
```

---

## Validation Gates

Each level has validation scripts:

```bash
# Level 0
python scripts/validate_level_0.py

# Level 1
python scripts/validate_level_1.py

# Level 2
python scripts/validate_level_2.py

# Level 3
python scripts/validate_level_3.py

# Level 4
python scripts/validate_level_4.py

# Level 5
python scripts/validate_level_5.py
```

---

## Next Steps

1. **[Memory Guild Architecture](MEMORY_GUILD_ARCHITECTURE.md)** - Deep dive into memory system
2. **[Orchestration Architecture](ORCHESTRATION_ARCHITECTURE.md)** - Task routing details
3. **[Implementation Templates](../templates/)** - Ready-to-use code


