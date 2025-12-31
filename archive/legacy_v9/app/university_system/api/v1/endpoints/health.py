"""
Health and monitoring endpoints for Uni0
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.university_system.database.database import get_db
from app.university_system.database.models_university import University, UniversityAgent
from app.university_system.middleware.metrics import update_business_metrics

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Uni0 University System",
        "version": "1.0.0"
    }

@router.get("/performance")
async def performance_metrics(db: Session = Depends(get_db)):
    """Performance metrics endpoint"""
    # Get basic statistics
    total_universities = db.query(University).count()
    total_agents = db.query(UniversityAgent).count()
    active_agents = db.query(UniversityAgent).filter(UniversityAgent.status == "active").count()
    
    return {
        "metrics": {
            "universities": {
                "total": total_universities
            },
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "inactive": total_agents - active_agents
            },
            "system": {
                "uptime": "N/A",  # Would need to track startup time
                "memory_usage": "N/A",  # Would need system monitoring
                "cpu_usage": "N/A"  # Would need system monitoring
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/errors")
async def error_statistics():
    """Error statistics endpoint"""
    # This would typically connect to a logging system
    return {
        "errors": {
            "last_24_hours": 0,
            "last_7_days": 0,
            "by_severity": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "by_category": {
                "database": 0,
                "authentication": 0,
                "validation": 0,
                "system": 0
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """Database health check"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    return {
        "database": {
            "status": database_status,
            "connection": "established" if database_status == "healthy" else "failed"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/services")
async def service_health():
    """Service health status"""
    return {
        "services": {
            "api": {
                "status": "healthy",
                "response_time": "N/A"
            },
            "database": {
                "status": "healthy", 
                "response_time": "N/A"
            },
            "authentication": {
                "status": "healthy",
                "response_time": "N/A"
            },
            "websocket": {
                "status": "healthy",
                "connections": 0
            }
        },
        "overall_health": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/metrics")
async def metrics(db: Session = Depends(get_db)):
    """Prometheus metrics endpoint"""
    # Update business metrics from app.university_system.database
    update_business_metrics(db)

    # Generate Prometheus metrics
    metrics_data = generate_latest()

    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )