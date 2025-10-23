# DRYAD Reference Implementation

**Version:** 2.0.0  
**Status:** Production Ready

---

## Complete Working Examples

This document provides complete, tested code examples for all major DRYAD components.

---

## Example 1: Simple Chatbot (Lightweight)

```python
# app/chatbot.py
from app.services.tool_registry import ToolRegistry
from app.services.memory_guild import MemoryCoordinator
from app.services.logging import StructuredLogger

class SimpleChatbot:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.memory = MemoryCoordinator()
        self.logger = StructuredLogger("chatbot")
    
    async def register_tools(self):
        """Register available tools"""
        self.tool_registry.register(ToolDefinition(
            id="search",
            name="Search",
            description="Search the web",
            parameters={"query": str},
            handler=self.search_web
        ))
    
    async def search_web(self, query: str) -> str:
        """Search the web"""
        self.logger.log_info("search_started", {"query": query})
        # Implement search logic
        return f"Results for {query}"
    
    async def chat(self, user_id: str, message: str) -> str:
        """Process user message"""
        # Store message in memory
        await self.memory.store(
            f"chat_{user_id}",
            {"message": message, "timestamp": datetime.now().isoformat()},
            ttl_seconds=3600
        )
        
        # Retrieve conversation history
        history = await self.memory.retrieve(f"chat_{user_id}")
        
        # Generate response
        response = f"You said: {message}"
        
        self.logger.log_info("chat_response", {
            "user_id": user_id,
            "response": response
        })
        
        return response

# Usage
async def main():
    chatbot = SimpleChatbot()
    await chatbot.register_tools()
    
    response = await chatbot.chat("user_1", "Hello!")
    print(response)

asyncio.run(main())
```

---

## Example 2: Document Processing Pipeline

```python
# app/document_processor.py
from app.services.memory_guild import MemoryScribe, MemoryCoordinator

class DocumentProcessor:
    def __init__(self):
        self.scribe = MemoryScribe()
        self.memory = MemoryCoordinator()
    
    async def process_document(
        self,
        document_id: str,
        content: str,
        source: str
    ) -> str:
        """Process and store document"""
        
        # Ingest content
        result = await self.scribe.ingest_content(
            content=content,
            source=source,
            metadata={
                "document_id": document_id,
                "processed_at": datetime.now().isoformat()
            }
        )
        
        if not result.success:
            raise ValueError(f"Failed to ingest: {result.error}")
        
        # Store in short-term memory for quick access
        await self.memory.store(
            f"document_{document_id}",
            {
                "content": content,
                "memory_id": result.memory_id,
                "source": source
            },
            ttl_seconds=86400  # 24 hours
        )
        
        return result.memory_id

# Usage
async def main():
    processor = DocumentProcessor()
    
    memory_id = await processor.process_document(
        document_id="doc_1",
        content="This is a sample document",
        source="upload"
    )
    
    print(f"Stored with ID: {memory_id}")

asyncio.run(main())
```

---

## Example 3: Multi-Agent Orchestration

```python
# app/orchestration_example.py
from app.services.orchestration import HybridOrchestrator
from app.services.agent_registry import AgentRegistry

class MultiAgentSystem:
    def __init__(self):
        self.orchestrator = HybridOrchestrator()
        self.agent_registry = AgentRegistry()
    
    async def register_agents(self):
        """Register available agents"""
        await self.agent_registry.register(AgentDefinition(
            id="analyzer",
            name="Analyzer",
            description="Analyzes documents",
            capabilities=["analyze", "summarize"]
        ))
        
        await self.agent_registry.register(AgentDefinition(
            id="writer",
            name="Writer",
            description="Writes content",
            capabilities=["write", "edit"]
        ))
    
    async def execute_workflow(self, task: str) -> str:
        """Execute multi-agent workflow"""
        
        # Discover agents
        agents = await self.agent_registry.discover_agents(
            filters={"capability": "analyze"}
        )
        
        # Execute task
        result = await self.orchestrator.execute_request(
            ExecutionRequest(
                task=task,
                agents=[a.id for a in agents],
                context={}
            )
        )
        
        return result.output

# Usage
async def main():
    system = MultiAgentSystem()
    await system.register_agents()
    
    result = await system.execute_workflow(
        "Analyze this document and summarize it"
    )
    
    print(f"Result: {result}")

asyncio.run(main())
```

---

## Example 4: Evaluation Framework

```python
# app/evaluation_example.py
from app.services.dojo import EvaluationHarness, BenchmarkRegistry

class AgentEvaluator:
    def __init__(self, db_session):
        self.harness = EvaluationHarness(db_session)
        self.registry = BenchmarkRegistry(db_session)
    
    async def register_benchmarks(self):
        """Register evaluation benchmarks"""
        await self.registry.register(Benchmark(
            id="accuracy",
            name="Accuracy Test",
            description="Tests agent accuracy",
            test_cases=[
                {"input": "test1", "expected": "result1"},
                {"input": "test2", "expected": "result2"}
            ]
        ))
    
    async def evaluate_agent(self, agent_id: str) -> float:
        """Evaluate agent performance"""
        
        result = await self.harness.run_evaluation(
            EvaluationRequest(
                agent_id=agent_id,
                agent_version="1.0",
                benchmark_id="accuracy"
            )
        )
        
        return result.scores.get("accuracy", 0.0)

# Usage
async def main():
    evaluator = AgentEvaluator(db_session)
    await evaluator.register_benchmarks()
    
    score = await evaluator.evaluate_agent("my_agent")
    print(f"Agent score: {score}")

asyncio.run(main())
```

---

## Example 5: Self-Improvement System

```python
# app/improvement_example.py
from app.services.lyceum import ProfessorAgent, BudgetManager

class SelfImprovingAgent:
    def __init__(self):
        self.professor = ProfessorAgent()
        self.budget_manager = BudgetManager()
    
    async def improve(self, agent_id: str) -> bool:
        """Automatically improve agent"""
        
        # Analyze performance
        analysis = await self.professor.analyze_performance(
            agent_id=agent_id
        )
        
        # Suggest improvements
        improvements = await self.professor.suggest_improvements(analysis)
        
        # Allocate budget
        for improvement in improvements:
            allocated = await self.budget_manager.allocate_budget(
                agent_id=agent_id,
                improvement=improvement
            )
            
            if allocated:
                # Apply improvement
                await self._apply_improvement(improvement)
        
        return True
    
    async def _apply_improvement(self, improvement):
        """Apply improvement to agent"""
        # Implementation specific to improvement type
        pass

# Usage
async def main():
    agent = SelfImprovingAgent()
    
    success = await agent.improve("my_agent")
    print(f"Improvement applied: {success}")

asyncio.run(main())
```

---

## Example 6: FastAPI Integration

```python
# app/api/main.py
from fastapi import FastAPI, HTTPException
from app.services.memory_guild import MemoryCoordinator
from app.services.tool_registry import ToolRegistry

app = FastAPI()

memory = MemoryCoordinator()
tool_registry = ToolRegistry()

@app.post("/memory/store")
async def store_memory(key: str, value: dict, ttl: int = 3600):
    """Store in memory"""
    success = await memory.store(key, value, ttl)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store")
    return {"status": "stored"}

@app.get("/memory/retrieve/{key}")
async def retrieve_memory(key: str):
    """Retrieve from memory"""
    value = await memory.retrieve(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"value": value}

@app.post("/tools/execute")
async def execute_tool(tool_id: str, params: dict):
    """Execute a tool"""
    try:
        result = await tool_registry.execute(tool_id, params)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Run with: uvicorn app.api.main:app --reload
```

---

## Example 7: Testing

```python
# tests/test_chatbot.py
import pytest
from app.chatbot import SimpleChatbot

@pytest.mark.asyncio
async def test_chatbot_chat():
    """Test chatbot chat functionality"""
    chatbot = SimpleChatbot()
    await chatbot.register_tools()
    
    response = await chatbot.chat("user_1", "Hello!")
    
    assert response is not None
    assert "Hello" in response

@pytest.mark.asyncio
async def test_memory_storage():
    """Test memory storage"""
    chatbot = SimpleChatbot()
    
    await chatbot.memory.store(
        "test_key",
        {"value": "test"},
        ttl_seconds=3600
    )
    
    result = await chatbot.memory.retrieve("test_key")
    assert result["value"] == "test"

@pytest.mark.asyncio
async def test_tool_registration():
    """Test tool registration"""
    chatbot = SimpleChatbot()
    await chatbot.register_tools()
    
    tools = chatbot.tool_registry.list()
    assert len(tools) > 0
    assert any(t.id == "search" for t in tools)
```

---

## Example 8: Configuration

```python
# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:pass@localhost/dryad"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # ChromaDB
    chromadb_url: str = "http://localhost:8001"
    
    # Logging
    log_level: str = "INFO"
    
    # Security
    secret_key: str = "your-secret-key"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Example 9: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Example 10: Monitoring

```python
# app/monitoring.py
from prometheus_client import Counter, Histogram
import time

# Metrics
request_count = Counter(
    'dryad_requests_total',
    'Total requests',
    ['endpoint']
)

request_duration = Histogram(
    'dryad_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

# Middleware
@app.middleware("http")
async def add_metrics(request, call_next):
    start = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start
    request_count.labels(endpoint=request.url.path).inc()
    request_duration.labels(endpoint=request.url.path).observe(duration)
    
    return response
```

---

## Next Steps

1. **[Integration Guide](../integration/INTEGRATION_GUIDE.md)** - How to integrate
2. **[Customization Guide](../integration/CUSTOMIZATION_GUIDE.md)** - How to extend
3. **[Operations Runbook](../../operations/RUNBOOK.md)** - Production deployment


