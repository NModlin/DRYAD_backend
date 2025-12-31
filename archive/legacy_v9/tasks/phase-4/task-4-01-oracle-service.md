# Task 4-01: Oracle Service Extraction

**Phase:** 4 - Forest Ecosystem Architecture  
**Week:** 17  
**Estimated Hours:** 20 hours  
**Priority:** CRITICAL  
**Dependencies:** Phase 3 complete

---

## 🎯 OBJECTIVE

Extract the Oracle (AI Provider Hub) into a standalone microservice. This service manages all LLM interactions, model selection, prompt engineering, and response handling. It becomes the central AI intelligence layer for the entire ecosystem.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Standalone FastAPI service for LLM interactions
- Support multiple LLM providers (OpenAI, Anthropic, local Ollama)
- Agent-specific model tier selection (Fast/Balanced/Reasoning)
- Prompt template management
- Response caching with Redis
- Rate limiting and cost tracking
- Health checks and monitoring

### Technical Requirements
- FastAPI with async/await
- gRPC for inter-service communication
- Redis for caching
- PostgreSQL for usage tracking
- Docker containerization
- Kubernetes deployment manifests

### Performance Requirements
- Response time: <2 seconds (Fast tier), <10 seconds (Reasoning tier)
- Throughput: 100+ requests/second
- Cache hit rate: >60%
- Uptime: >99.9%

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create Oracle Service (16 hours)

**File:** `services/oracle/app/main.py`

```python
"""
Oracle Service - AI Provider Hub Microservice
Centralized LLM interaction service for DRYAD ecosystem.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from structlog import get_logger

from .core.llm_manager import LLMManager
from .core.cache import CacheManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    logger.info("oracle_service_starting")
    
    # Initialize services
    app.state.llm_manager = LLMManager()
    app.state.cache_manager = CacheManager()
    
    yield
    
    # Cleanup
    logger.info("oracle_service_shutting_down")


app = FastAPI(
    title="Oracle Service",
    description="AI Provider Hub for DRYAD.AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConsultRequest(BaseModel):
    """Request to consult Oracle."""
    
    prompt: str = Field(..., min_length=1, max_length=50000)
    model_tier: str = Field(default="balanced")  # fast, balanced, reasoning
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    system_prompt: str | None = None
    use_cache: bool = True


class ConsultResponse(BaseModel):
    """Response from Oracle."""
    
    response: str
    model_used: str
    tokens_used: int
    cached: bool
    latency_ms: float


@app.post("/v1/consult", response_model=ConsultResponse)
async def consult_oracle(request: ConsultRequest) -> ConsultResponse:
    """
    Consult Oracle with prompt.
    
    Args:
        request: Consultation request
        
    Returns:
        LLM response
    """
    logger.info(
        "consult_request",
        model_tier=request.model_tier,
        prompt_length=len(request.prompt),
    )
    
    try:
        llm_manager: LLMManager = app.state.llm_manager
        cache_manager: CacheManager = app.state.cache_manager
        
        # Check cache
        if request.use_cache:
            cached_response = await cache_manager.get(request.prompt)
            if cached_response:
                logger.info("cache_hit")
                return ConsultResponse(
                    response=cached_response["response"],
                    model_used=cached_response["model"],
                    tokens_used=cached_response["tokens"],
                    cached=True,
                    latency_ms=0.0,
                )
        
        # Generate response
        import time
        start = time.time()
        
        response = await llm_manager.generate(
            prompt=request.prompt,
            model_tier=request.model_tier,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt,
        )
        
        latency_ms = (time.time() - start) * 1000
        
        # Cache response
        if request.use_cache:
            await cache_manager.set(
                key=request.prompt,
                value={
                    "response": response.text,
                    "model": response.model,
                    "tokens": response.tokens_used,
                },
                ttl=3600,  # 1 hour
            )
        
        return ConsultResponse(
            response=response.text,
            model_used=response.model,
            tokens_used=response.tokens_used,
            cached=False,
            latency_ms=latency_ms,
        )
        
    except Exception as e:
        logger.error("consult_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "oracle"}


@app.get("/metrics")
async def get_metrics() -> dict[str, any]:
    """Get service metrics."""
    llm_manager: LLMManager = app.state.llm_manager
    cache_manager: CacheManager = app.state.cache_manager
    
    return {
        "total_requests": llm_manager.total_requests,
        "cache_hit_rate": cache_manager.hit_rate,
        "average_latency_ms": llm_manager.average_latency,
    }
```

**File:** `services/oracle/app/core/llm_manager.py`

```python
"""LLM Manager for Oracle Service."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class ModelTier(str, Enum):
    """LLM model tiers."""
    
    FAST = "fast"  # Llama 3 8B, GPT-3.5-Turbo
    BALANCED = "balanced"  # Claude 3 Sonnet, GPT-4o-mini
    REASONING = "reasoning"  # Claude 3 Opus, GPT-4o


class LLMResponse(BaseModel):
    """Response from LLM."""
    
    text: str
    model: str
    tokens_used: int


class LLMManager:
    """Manages LLM interactions across providers."""
    
    MODEL_MAPPING = {
        ModelTier.FAST: "gpt-3.5-turbo",
        ModelTier.BALANCED: "gpt-4o-mini",
        ModelTier.REASONING: "gpt-4o",
    }
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="llm_manager")
        self.total_requests = 0
        self.total_latency = 0.0
    
    async def generate(
        self,
        prompt: str,
        model_tier: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate LLM response."""
        self.total_requests += 1
        
        tier = ModelTier(model_tier)
        model = self.MODEL_MAPPING[tier]
        
        self.logger.info("generating_response", model=model)
        
        # In production, call actual LLM API
        # For now, return mock response
        
        return LLMResponse(
            text="Mock LLM response",
            model=model,
            tokens_used=100,
        )
    
    @property
    def average_latency(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests
```

### Step 2: Create Deployment Manifests (4 hours)

**File:** `services/oracle/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File:** `services/oracle/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oracle-service
  labels:
    app: oracle
spec:
  replicas: 3
  selector:
    matchLabels:
      app: oracle
  template:
    metadata:
      labels:
        app: oracle
    spec:
      containers:
      - name: oracle
        image: dryad/oracle:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: oracle-service
spec:
  selector:
    app: oracle
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## ✅ DEFINITION OF DONE

- [ ] Oracle service extracted and standalone
- [ ] Multi-provider LLM support working
- [ ] Caching operational
- [ ] Docker image built
- [ ] Kubernetes manifests created
- [ ] All tests passing (>85% coverage)
- [ ] Documentation complete

---

## 📊 SUCCESS METRICS

- Response time: <2s (Fast), <10s (Reasoning)
- Throughput: >100 req/s
- Cache hit rate: >60%
- Uptime: >99.9%
- Test coverage: >85%

---

**Estimated Completion:** 20 hours  
**Assigned To:** Backend Developer + DevOps Engineer  
**Status:** NOT STARTED

