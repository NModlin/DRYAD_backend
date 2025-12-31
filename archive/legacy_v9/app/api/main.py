"""
DRYAD.AI Production API Server
FastAPI application with all endpoints including Agentic University System (Level 6)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
import uvicorn

from app.use_cases.code_review_assistant import CodeReviewAssistant, CodeReviewRequest
from app.services.monitoring import get_prometheus_metrics, get_metrics
from app.services.logging.logger import StructuredLogger
from app.database.database import SessionLocal
from app.api.v1.router import api_router

# Initialize FastAPI app
app = FastAPI(
    title="DRYAD.AI Agent Evolution Architecture",
    description="Production-ready multi-agent system with self-improvement including Agentic University System (Level 6)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with all endpoints including university system
app.include_router(api_router)

logger = StructuredLogger("api")


# Dependency for database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "DRYAD.AI Agent Evolution Architecture",
        "version": "1.0.0",
        "status": "operational",
        "levels": {
            "level_0": "Foundation Services",
            "level_1": "Execution & Memory Agents",
            "level_2": "Stateful Operations",
            "level_3": "Orchestration & HITL",
            "level_4": "Evaluation Framework",
            "level_5": "Self-Improvement"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-10-13T00:00:00Z"
    }


@app.get("/metrics")
async def metrics():
    """Get metrics in JSON format."""
    return get_metrics()


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Get metrics in Prometheus format."""
    return get_prometheus_metrics()


@app.post("/api/v1/code-review")
async def create_code_review(request: CodeReviewRequest, db = Depends(get_db)):
    """
    Create a code review.

    Demonstrates complete DRYAD.AI workflow across all 6 levels.
    """
    try:
        # Use Python logger for synchronous logging
        import logging
        api_logger = logging.getLogger("dryad.api")
        api_logger.info(f"Code review request received: {request.review_id}")

        assistant = CodeReviewAssistant(db=db, tenant_id=request.tenant_id)
        result = await assistant.review_code(request)

        api_logger.info(f"Code review completed: {request.review_id}")
        return result

    except Exception as e:
        import logging
        api_logger = logging.getLogger("dryad.api")
        api_logger.error(f"Code review failed: {request.review_id} - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/status")
async def system_status():
    """Get system status."""
    metrics = get_metrics()
    
    return {
        "status": "operational",
        "uptime_seconds": metrics.get("uptime_seconds", 0),
        "metrics": {
            "code_reviews_total": metrics.get("counters", {}).get("code_reviews_total", 0),
            "code_reviews_completed": metrics.get("counters", {}).get("code_review_completed", 0),
            "code_reviews_escalated": metrics.get("counters", {}).get("code_review_escalations", 0),
        },
        "levels": {
            "level_0": "operational",
            "level_1": "operational",
            "level_2": "operational",
            "level_3": "operational",
            "level_4": "operational",
            "level_5": "operational"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

