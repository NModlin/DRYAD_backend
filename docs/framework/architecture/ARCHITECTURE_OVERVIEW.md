# DRYAD Architecture Overview

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** 2025-10-19

---

## System Architecture

DRYAD is built on a **6-level dependency-driven architecture** where each level builds upon the previous one, creating a modular, scalable system.

### Core Principles

1. **Modularity** - Each level is independent and can be used separately
2. **Dependency-Driven** - Clear dependencies enable parallel development
3. **Extensibility** - Plugin architecture for custom components
4. **Observability** - Structured logging throughout
5. **Resilience** - Fallback mechanisms and graceful degradation
6. **Security** - Multi-tenant isolation and access control

---

## The 6 Levels

### Level 0: Foundation Services
**No dependencies - build first**

**Components:**
- **Tool Registry** - Centralized tool management
- **Memory Database** - PostgreSQL schema for memory storage
- **Structured Logging** - Comprehensive observability

**Responsibilities:**
- Provide core infrastructure
- Enable other levels to function
- Ensure data persistence
- Track all system events

**Key Files:**
- `app/services/tool_registry/` - Tool management
- `app/services/logging/` - Structured logging
- `alembic/versions/` - Database migrations

---

### Level 1: Execution & Memory Agents
**Depends on Level 0**

**Components:**
- **Sandbox Service** - Isolated code execution
- **Memory Coordinator** - Routes memory requests
- **Memory Scribe** - Data ingestion and processing
- **Agent Registry** - Tracks available agents

**Responsibilities:**
- Execute tools safely
- Manage agent lifecycle
- Ingest and process data
- Coordinate memory operations

**Key Files:**
- `app/services/sandbox_service.py` - Execution environment
- `app/services/memory_guild/coordinator.py` - Memory routing
- `app/services/memory_guild/scribe.py` - Data ingestion
- `app/services/agent_registry_service.py` - Agent tracking

---

### Level 2: Stateful Operations
**Depends on Levels 0-1**

**Components:**
- **Archivist Agent** - Short-term memory (Redis)
- **Librarian Agent** - Long-term memory (ChromaDB)

**Responsibilities:**
- Manage short-term context
- Perform semantic search
- Maintain knowledge graphs
- Handle memory expiration

**Key Files:**
- `app/services/memory_guild/archivist.py` - Short-term memory
- `app/services/memory_guild/librarian.py` - Long-term memory

---

### Level 3: Orchestration & HITL
**Depends on Levels 0-2**

**Components:**
- **Complexity Scorer** - Analyzes task complexity
- **Decision Engine** - Routes to execution mode
- **Task Force Manager** - Multi-agent collaboration
- **Hybrid Orchestrator** - Main orchestration
- **State Manager** - Workflow state tracking
- **Consultation Manager** - Human-in-the-loop

**Responsibilities:**
- Route tasks intelligently
- Manage multi-agent workflows
- Provide human oversight
- Track execution state

**Key Files:**
- `app/services/orchestration/` - Orchestration components
- `app/services/hitl/` - Human-in-the-loop system

---

### Level 4: The Dojo (Evaluation)
**Depends on Levels 0-3**

**Components:**
- **Benchmark Registry** - Standardized evaluation problems
- **Evaluation Harness** - Agent evaluation execution
- **RAG-Gym Benchmarks** - Memory Guild benchmarks

**Responsibilities:**
- Measure agent performance
- Track improvement over time
- Provide quantitative metrics
- Enable comparison

**Key Files:**
- `app/services/dojo/` - Evaluation framework

---

### Level 5: The Lyceum (Self-Improvement)
**Depends on Levels 0-4**

**Components:**
- **Laboratory Sandbox** - Isolated improvement environment
- **Professor Agent** - Analyzes performance and suggests improvements
- **Budget Manager** - Manages improvement resources

**Responsibilities:**
- Analyze agent performance
- Generate improvements
- Test improvements safely
- Deploy successful changes

**Key Files:**
- `app/services/lyceum/` - Self-improvement system

---

## Component Interactions

### Request Flow
```
User Request
    ↓
API Endpoint
    ↓
Orchestrator (Level 3)
    ↓
Complexity Scorer → Decision Engine
    ↓
Route to: Sandbox (Level 1) OR Multi-Agent (Level 3)
    ↓
Memory Coordinator (Level 1)
    ↓
Archivist (Level 2) OR Librarian (Level 2)
    ↓
Tool Registry (Level 0)
    ↓
Execute Tool
    ↓
Store Result in Memory
    ↓
Return Response
```

### Memory Flow
```
Data Ingestion
    ↓
Memory Scribe (Level 1)
    ↓
Deduplication & Embedding
    ↓
Memory Coordinator (Level 1)
    ↓
Archivist (Level 2) - Short-term
Librarian (Level 2) - Long-term
    ↓
Memory Database (Level 0)
```

### Evaluation Flow
```
Agent Execution
    ↓
Dojo Evaluation (Level 4)
    ↓
Benchmark Registry
    ↓
Evaluation Harness
    ↓
Generate Metrics
    ↓
Store Results
    ↓
Lyceum Analysis (Level 5)
    ↓
Generate Improvements
    ↓
Test & Deploy
```

---

## Technology Stack

### Core
- **Python 3.11+** - Primary language
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

### Data Storage
- **PostgreSQL** - Primary database
- **Redis** - Short-term memory cache
- **ChromaDB** - Vector database for semantic search

### Execution
- **Docker** - Container isolation
- **Asyncio** - Async execution

### Monitoring
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Structured Logging** - Event tracking

---

## Deployment Architecture

### Single-Node Deployment
```
Docker Container
├── FastAPI Application
├── PostgreSQL
├── Redis
└── ChromaDB
```

### Multi-Node Deployment
```
Load Balancer (Nginx)
├── API Server 1
├── API Server 2
└── API Server N

Shared Services
├── PostgreSQL (Primary + Replicas)
├── Redis Cluster
└── ChromaDB Cluster
```

---

## Security Architecture

### Multi-Tenant Isolation
- Tenant ID in all queries
- Row-level security policies
- Isolated execution environments

### Access Control
- Tool permission system
- Memory access policies
- API authentication

### Data Protection
- Encrypted connections
- Secure credential storage
- Audit logging

---

## Next Steps

1. **[Level-Based Architecture](LEVEL_BASED_ARCHITECTURE.md)** - Detailed level breakdown
2. **[Memory Guild Architecture](MEMORY_GUILD_ARCHITECTURE.md)** - Memory system design
3. **[Orchestration Architecture](ORCHESTRATION_ARCHITECTURE.md)** - Task routing
4. **[Implementation Templates](../templates/)** - Ready-to-use code


