# Full DRYAD 2.0 Framework Template

**Version:** 2.0.0  
**Use Case:** Complete agentic systems with full governance  
**Complexity:** High  
**Estimated Setup Time:** 1-2 weeks

---

## Overview

The **Full DRYAD 2.0 Framework** provides a complete, production-ready agentic system using all **6 levels**:

- **Level 0:** Tool Registry, Memory Database, Structured Logging
- **Level 1:** Sandbox, Memory Coordinator, Memory Scribe, Agent Registry
- **Level 2:** Archivist (short-term), Librarian (long-term)
- **Level 3:** Orchestration, HITL, Task Forces
- **Level 4:** The Dojo (Evaluation Framework)
- **Level 5:** The Lyceum (Self-Improvement)

**Perfect for:**
- Enterprise multi-agent systems
- Complex workflow automation
- Autonomous agent networks
- Self-improving AI systems

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│ Level 5: The Lyceum (Self-Improvement)              │
│ - Laboratory Sandbox                                 │
│ - Professor Agent                                    │
│ - Budget Manager                                     │
└──────────────────────────────────────────────────────┘
                         ↑
┌──────────────────────────────────────────────────────┐
│ Level 4: The Dojo (Evaluation)                       │
│ - Benchmark Registry                                 │
│ - Evaluation Harness                                 │
│ - RAG-Gym Benchmarks                                 │
└──────────────────────────────────────────────────────┘
                         ↑
┌──────────────────────────────────────────────────────┐
│ Level 3: Orchestration & HITL                        │
│ - Complexity Scorer                                  │
│ - Decision Engine                                    │
│ - Task Force Manager                                 │
│ - Hybrid Orchestrator                                │
│ - HITL System                                        │
└──────────────────────────────────────────────────────┘
                         ↑
┌──────────────────────────────────────────────────────┐
│ Level 2: Stateful Operations                         │
│ - Archivist (Short-term Memory)                      │
│ - Librarian (Long-term Memory)                       │
└──────────────────────────────────────────────────────┘
                         ↑
┌──────────────────────────────────────────────────────┐
│ Level 1: Execution & Memory Agents                   │
│ - Sandbox Service                                    │
│ - Memory Coordinator                                 │
│ - Memory Scribe                                      │
│ - Agent Registry                                     │
└──────────────────────────────────────────────────────┘
                         ↑
┌──────────────────────────────────────────────────────┐
│ Level 0: Foundation Services                         │
│ - Tool Registry                                      │
│ - Memory Database                                    │
│ - Structured Logging                                 │
└──────────────────────────────────────────────────────┘
```

---

## File Structure

```
your-project/
├── app/
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   └── security.py            # Security
│   ├── services/
│   │   ├── tool_registry/         # Level 0
│   │   ├── logging/               # Level 0
│   │   ├── memory_guild/          # Levels 1-2
│   │   │   ├── coordinator.py
│   │   │   ├── scribe.py
│   │   │   ├── archivist.py
│   │   │   └── librarian.py
│   │   ├── sandbox/               # Level 1
│   │   ├── agent_registry/        # Level 1
│   │   ├── orchestration/         # Level 3
│   │   │   ├── complexity_scorer.py
│   │   │   ├── decision_engine.py
│   │   │   ├── task_force_manager.py
│   │   │   └── orchestrator.py
│   │   ├── hitl/                  # Level 3
│   │   ├── dojo/                  # Level 4
│   │   │   ├── benchmark_registry.py
│   │   │   └── evaluation_harness.py
│   │   └── lyceum/                # Level 5
│   │       ├── professor_agent.py
│   │       └── budget_manager.py
│   ├── models/
│   │   ├── schemas.py
│   │   └── database.py
│   └── api/
│       ├── v1/
│       │   ├── endpoints/
│       │   │   ├── agents.py
│       │   │   ├── tools.py
│       │   │   ├── memory.py
│       │   │   ├── orchestration.py
│       │   │   └── evaluation.py
│       │   └── dependencies.py
│       └── health.py
├── database/
│   ├── models.py
│   ├── session.py
│   └── migrations/
├── tests/
│   ├── services/
│   ├── api/
│   └── integration/
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Core Components

### Level 0: Foundation Services

```python
# Tool Registry
class ToolRegistry:
    async def register_tool(self, tool: ToolDefinition) -> str
    async def get_tool(self, tool_id: str) -> ToolDefinition
    async def list_tools(self) -> List[ToolDefinition]
    async def validate_tool(self, tool: ToolDefinition) -> bool

# Structured Logging
class StructuredLogger:
    def log_info(self, event: str, data: Dict)
    def log_warning(self, event: str, data: Dict)
    def log_error(self, event: str, data: Dict)
```

### Level 1: Execution & Memory Agents

```python
# Sandbox Service
class SandboxService:
    async def execute_tool(
        self,
        tool_id: str,
        params: Dict,
        timeout: int = 30
    ) -> ExecutionResult

# Memory Coordinator
class MemoryCoordinator:
    async def handle_memory_request(
        self,
        request: MemoryRequest
    ) -> MemoryResponse

# Memory Scribe
class MemoryScribe:
    async def ingest_content(
        self,
        content: str,
        source: str,
        metadata: Dict
    ) -> MemoryResponse

# Agent Registry
class AgentRegistry:
    async def register_agent(self, agent: AgentDefinition) -> str
    async def discover_agents(self, filters: Dict) -> List[Agent]
```

### Level 2: Stateful Operations

```python
# Archivist (Short-term Memory)
class Archivist:
    async def store(
        self,
        key: str,
        value: Dict,
        ttl: timedelta
    ) -> bool
    async def retrieve(self, key: str) -> Optional[Dict]

# Librarian (Long-term Memory)
class Librarian:
    async def store(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict
    ) -> str
    async def search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 10
    ) -> List[SearchResult]
```

### Level 3: Orchestration & HITL

```python
# Complexity Scorer
class ComplexityScorer:
    async def score_task(self, task: Task) -> float

# Decision Engine
class DecisionEngine:
    async def route_task(
        self,
        task: Task,
        complexity: float
    ) -> ExecutionMode

# Task Force Manager
class TaskForceManager:
    async def create_task_force(
        self,
        agents: List[Agent],
        task: Task
    ) -> TaskForce
    async def execute_collaboration(
        self,
        task_force: TaskForce
    ) -> Result

# Hybrid Orchestrator
class HybridOrchestrator:
    async def execute_request(
        self,
        request: ExecutionRequest
    ) -> ExecutionResult

# HITL System
class HITLSystem:
    async def request_approval(
        self,
        action: Action
    ) -> ApprovalResult
```

### Level 4: The Dojo (Evaluation)

```python
# Benchmark Registry
class BenchmarkRegistry:
    async def register_benchmark(
        self,
        benchmark: Benchmark
    ) -> str
    async def get_benchmark(self, benchmark_id: str) -> Benchmark

# Evaluation Harness
class EvaluationHarness:
    async def run_evaluation(
        self,
        agent_id: str,
        benchmark_id: str
    ) -> EvaluationResult
```

### Level 5: The Lyceum (Self-Improvement)

```python
# Professor Agent
class ProfessorAgent:
    async def analyze_performance(
        self,
        agent_id: str
    ) -> PerformanceAnalysis
    async def suggest_improvements(
        self,
        analysis: PerformanceAnalysis
    ) -> List[Improvement]

# Budget Manager
class BudgetManager:
    async def allocate_budget(
        self,
        agent_id: str,
        improvement: Improvement
    ) -> bool
```

---

## API Endpoints

```python
# Level 0: Foundation
POST   /api/v1/tools/register
GET    /api/v1/tools/{tool_id}
GET    /api/v1/tools
POST   /api/v1/tools/execute

# Level 1: Execution & Memory
POST   /api/v1/agents/register
GET    /api/v1/agents/discover
POST   /api/v1/memory/store
GET    /api/v1/memory/retrieve/{key}

# Level 2: Stateful Operations
POST   /api/v1/memory/search
GET    /api/v1/memory/history

# Level 3: Orchestration
POST   /api/v1/orchestration/execute
POST   /api/v1/orchestration/task-force
GET    /api/v1/orchestration/status/{execution_id}

# Level 4: Evaluation
POST   /api/v1/evaluation/run
GET    /api/v1/evaluation/results/{run_id}
GET    /api/v1/evaluation/leaderboard

# Level 5: Self-Improvement
POST   /api/v1/improvement/analyze
GET    /api/v1/improvement/suggestions/{agent_id}
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/dryad
      REDIS_URL: redis://redis:6379
      CHROMADB_URL: http://chromadb:8000
    depends_on:
      - db
      - redis
      - chromadb

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

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

volumes:
  postgres_data:
```

---

## Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

---

## Monitoring

### Prometheus Metrics
- Agent performance
- Memory usage
- Execution times
- Error rates

### Grafana Dashboards
- System overview
- Agent leaderboard
- Memory usage
- Improvement tracking

---

## Next Steps

1. **Customize agents** - Implement your specific agents
2. **Add benchmarks** - Define evaluation criteria
3. **Configure HITL** - Set approval workflows
4. **Deploy to production** - Use Kubernetes or cloud
5. **Monitor and optimize** - Use Prometheus/Grafana

---

## Production Checklist

- [ ] All tests passing (100%)
- [ ] Security audit complete
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan ready
- [ ] Documentation complete
- [ ] Team trained

See **[Operations Runbook](../../operations/RUNBOOK.md)** for production deployment guide.


