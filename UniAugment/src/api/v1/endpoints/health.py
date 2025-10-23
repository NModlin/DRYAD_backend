# app/api/v1/endpoints/health.py
"""
Enhanced health check endpoints for comprehensive system monitoring.
Includes circuit breaker status, service health, and graceful degradation info.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

from app.core.llm_config import (
    get_llm_health_status,
    get_llm_metrics,
    get_llm_info,
    get_pool_stats,
    reset_llm_metrics
)
from app.core.circuit_breaker import circuit_breaker_manager
from app.core.service_monitor import service_monitor
from app.core.feature_flags import feature_flags
from app.core.basic_mode import basic_mode
from app.core.security import get_current_user_optional
from app.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_health_status():
    """
    Get comprehensive health status of the LLM system with setup guidance.

    Returns:
        Dict containing overall system health status
    """
    try:
        health_status = get_llm_health_status()
        llm_info = get_llm_info()

        # Add setup guidance based on current status
        setup_guidance = []

        if not llm_info.get("available", False):
            setup_guidance.extend([
                "🚨 No real LLM configured - currently using mock responses",
                "💡 Quick setup options:",
                "   1. Ollama: Run 'python scripts/setup_local_llm.py'",
                "   2. OpenAI: Set OPENAI_API_KEY environment variable",
                "   3. HuggingFace: Set USE_HUGGINGFACE=true and install dependencies"
            ])

        if health_status["status"] == "unhealthy":
            setup_guidance.extend([
                "🔧 Troubleshooting steps:",
                "   - Check if Ollama service is running: ollama serve",
                "   - Verify model is installed: ollama list",
                "   - Check environment variables in .env file"
            ])

        # Add guidance to the health status response
        health_status["setup_guidance"] = setup_guidance
        health_status["llm_info"] = llm_info

        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "llm_status": {"available": False, "status": "unknown", "health_score": 0},
            "system_status": {"overall_status": "unknown", "services_monitored": 0, "capabilities_score": 0},
            "basic_mode": {"active": True, "reason": "Health check failed"}
        }

async def _get_ai_system_status() -> Dict[str, Any]:
    """Get comprehensive AI system status."""
    ai_status = {
        "model_manager": {"status": "unknown"},
        "performance_optimizer": {"status": "unknown"},
        "multi_agent": {"status": "unknown"},
        "overall_status": "unknown"
    }

    try:
        # Model manager status
        from app.core.model_manager import model_manager
        model_status = model_manager.get_system_status()
        ai_status["model_manager"] = {
            "status": "healthy" if model_status["downloaded_models"] > 0 else "degraded",
            "downloaded_models": model_status["downloaded_models"],
            "recommended_model": model_status["recommended_model"],
            "total_size_gb": model_status["total_size_gb"]
        }
    except Exception as e:
        ai_status["model_manager"] = {"status": "error", "error": str(e)}

    try:
        # Performance optimizer status
        from app.core.performance_optimizer import performance_optimizer
        if performance_optimizer.is_initialized:
            perf_report = performance_optimizer.get_performance_report()
            ai_status["performance_optimizer"] = {
                "status": perf_report["status"],
                "optimization_enabled": perf_report["optimization_enabled"],
                "active_requests": perf_report.get("request_queue", {}).get("active_requests", 0)
            }
        else:
            ai_status["performance_optimizer"] = {"status": "not_initialized"}
    except Exception as e:
        ai_status["performance_optimizer"] = {"status": "error", "error": str(e)}

    try:
        # Multi-agent system status
        from app.core.multi_agent import multi_agent_orchestrator
        ai_status["multi_agent"] = {
            "status": "healthy" if len(multi_agent_orchestrator.agents) > 0 else "degraded",
            "agents_available": len(multi_agent_orchestrator.agents),
            "crewai_enabled": multi_agent_orchestrator.use_crewai,
            "task_history_count": len(multi_agent_orchestrator.task_history)
        }
    except Exception as e:
        ai_status["multi_agent"] = {"status": "error", "error": str(e)}

    # Determine overall AI system status
    statuses = [ai_status["model_manager"]["status"],
                ai_status["performance_optimizer"]["status"],
                ai_status["multi_agent"]["status"]]

    if all(s == "healthy" for s in statuses):
        ai_status["overall_status"] = "healthy"
    elif any(s == "error" for s in statuses):
        ai_status["overall_status"] = "error"
    else:
        ai_status["overall_status"] = "degraded"

    return ai_status

@router.get("/status", response_model=Dict[str, Any])
async def get_comprehensive_health_status():
    """
    Get comprehensive health status including all services and circuit breakers.

    Returns:
        Dictionary with complete system health information
    """
    try:
        # Get LLM health
        llm_health = get_llm_health_status()

        # Get circuit breaker status
        circuit_breaker_health = circuit_breaker_manager.get_health_summary()

        # Get service monitor status
        service_status = await service_monitor.get_system_status()

        # Get AI system status
        ai_system_status = await _get_ai_system_status()

        # Determine overall system health
        overall_status = _determine_overall_status(llm_health, circuit_breaker_health, service_status, ai_system_status)

        return {
            "status": overall_status["status"],
            "timestamp": datetime.now().isoformat(),
            "health_score": overall_status["health_score"],
            "services": {
                "llm": {
                    "status": llm_health["status"],
                    "provider": llm_health.get("provider", "unknown"),
                    "model": llm_health.get("model", "unknown"),
                    "available": llm_health.get("llm_available", False),
                    "health_score": llm_health.get("health_score", 0)
                },
                "database": service_status.get("database", {"status": "unknown"}),
                "vector_store": service_status.get("vector_store", {"status": "unknown"}),
                "task_queue": service_status.get("task_queue", {"status": "unknown"}),
                "multimodal": service_status.get("multimodal", {"status": "unknown"})
            },
            "ai_system": ai_system_status,
            "circuit_breakers": circuit_breaker_health,
            "degraded_features": _get_degraded_features(service_status),
            "available_features": _get_available_features(service_status),
            "recommendations": _get_health_recommendations(overall_status, service_status)
        }

    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "health_score": 0,
            "error": str(e),
            "services": {},
            "circuit_breakers": {"status": "unknown"},
            "degraded_features": [],
            "available_features": ["basic_api"],
            "recommendations": ["Check system logs", "Restart services if needed"]
        }

@router.get("/health/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """
    Get detailed LLM usage metrics.
    
    Returns:
        Dictionary with usage statistics and performance metrics
    """
    try:
        metrics = get_llm_metrics()
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.post("/health/metrics/reset")
async def reset_metrics():
    """
    Reset LLM usage metrics.
    
    Returns:
        Confirmation of metrics reset
    """
    try:
        reset_llm_metrics()
        return {
            "status": "success",
            "message": "LLM metrics have been reset"
        }
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")

@router.get("/health/llm", response_model=Dict[str, Any])
async def get_llm_status():
    """
    Get detailed LLM configuration and status information.
    
    Returns:
        Dictionary with LLM configuration, cache status, and pool information
    """
    try:
        llm_info = get_llm_info()
        return {
            "status": "success",
            "llm_info": llm_info
        }
    except Exception as e:
        logger.error(f"Failed to get LLM status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM status: {str(e)}")

@router.get("/health/pools", response_model=Dict[str, Any])
async def get_pool_status():
    """
    Get connection pool status and statistics.
    
    Returns:
        Dictionary with pool statistics for all active pools
    """
    try:
        pool_stats = get_pool_stats()
        return {
            "status": "success",
            "pools": pool_stats
        }
    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pool status: {str(e)}")

@router.get("/health/detailed", response_model=Dict[str, Any])
async def get_detailed_health():
    """
    Get comprehensive system health information including all subsystems.
    
    Returns:
        Dictionary with complete health status, metrics, LLM info, and pool stats
    """
    try:
        health_status = get_llm_health_status()
        metrics = get_llm_metrics()
        llm_info = get_llm_info()
        pool_stats = get_pool_stats()
        
        return {
            "status": health_status["status"],
            "health_score": health_status["health_score"],
            "timestamp": health_status["timestamp"],
            "health_details": health_status,
            "metrics": metrics,
            "llm_info": llm_info,
            "pool_stats": pool_stats
        }
    except Exception as e:
        logger.error(f"Failed to get detailed health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get detailed health: {str(e)}")

@router.get("/health/quick", response_model=Dict[str, Any])
async def get_quick_health():
    """
    Get quick health check for monitoring systems.
    
    Returns:
        Simple health status for monitoring and alerting
    """
    try:
        health_status = get_llm_health_status()
        
        return {
            "status": health_status["status"],
            "health_score": health_status["health_score"],
            "llm_available": health_status["llm_available"],
            "provider": health_status["provider"],
            "model": health_status["model"],
            "timestamp": health_status["timestamp"],
            "issues": health_status.get("issues", [])
        }
    except Exception as e:
        logger.error(f"Quick health check failed: {e}")
        return {
            "status": "error",
            "health_score": 0,
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/services", response_model=Dict[str, Any])
async def get_services_health():
    """
    Get detailed health status of all services.

    Returns:
        Dictionary with individual service health information
    """
    try:
        service_status = await service_monitor.get_system_status()

        # Test each service individually
        detailed_status = {}

        # Database health
        try:
            from app.database.database import get_db
            async for db in get_db():
                from sqlalchemy import text
                await db.execute(text("SELECT 1"))
                detailed_status["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "response_time_ms": 0  # Could measure actual response time
                }
                break
        except Exception as e:
            detailed_status["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "error": str(e)
            }

        # Vector store health
        try:
            from app.core.vector_store import get_vector_store
            vector_store = get_vector_store()
            if vector_store and vector_store.is_connected:
                detailed_status["vector_store"] = {
                    "status": "healthy",
                    "message": "Vector store connection successful",
                    "provider": "weaviate"
                }
            else:
                detailed_status["vector_store"] = {
                    "status": "degraded",
                    "message": "Vector store not available, using fallback",
                    "fallback_active": True
                }
        except Exception as e:
            detailed_status["vector_store"] = {
                "status": "unhealthy",
                "message": f"Vector store connection failed: {str(e)}",
                "error": str(e)
            }

        # Task queue health
        try:
            import redis
            import os
            redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            detailed_status["task_queue"] = {
                "status": "healthy",
                "message": "Task queue connection successful",
                "provider": "redis"
            }
        except Exception as e:
            detailed_status["task_queue"] = {
                "status": "unhealthy",
                "message": f"Task queue connection failed: {str(e)}",
                "error": str(e)
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "services": detailed_status,
            "overall_status": _determine_services_overall_status(detailed_status)
        }

    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "error",
            "error": str(e)
        }


@router.get("/circuit-breakers", response_model=Dict[str, Any])
async def get_circuit_breakers_status():
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary with circuit breaker states and statistics
    """
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": circuit_breaker_manager.get_health_summary(),
            "details": circuit_breaker_manager.get_all_stats()
        }
    except Exception as e:
        logger.error(f"Circuit breaker status check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {"status": "error", "error": str(e)},
            "details": {}
        }


@router.post("/circuit-breakers/reset")
async def reset_circuit_breakers(current_user = Depends(get_current_user_optional)):
    """
    Reset all circuit breakers (admin operation).

    Returns:
        Confirmation of reset operation
    """
    try:
        circuit_breaker_manager.reset_all()
        logger.info("All circuit breakers reset by user")
        return {
            "message": "All circuit breakers have been reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Circuit breaker reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


def _determine_overall_status(llm_health: Dict, circuit_health: Dict, service_status: Dict, ai_system_status: Dict = None) -> Dict[str, Any]:
    """Determine overall system health status."""
    # Calculate health score (0-100)
    llm_score = llm_health.get("health_score", 0)

    # Circuit breaker penalty
    cb_penalty = 0
    if circuit_health["status"] == "failed":
        cb_penalty = 30
    elif circuit_health["status"] == "degraded":
        cb_penalty = 15

    # Service availability bonus/penalty
    service_penalty = 0
    total_services = len(service_status)
    if total_services > 0:
        unhealthy_services = sum(1 for s in service_status.values()
                               if s.get("status") == "unhealthy")
        service_penalty = (unhealthy_services / total_services) * 20

    # AI system penalty
    ai_penalty = 0
    if ai_system_status:
        ai_status = ai_system_status.get("overall_status", "unknown")
        if ai_status == "error":
            ai_penalty = 25
        elif ai_status == "degraded":
            ai_penalty = 10

    health_score = max(0, min(100, llm_score - cb_penalty - service_penalty - ai_penalty))

    # Determine status
    if health_score >= 80:
        status = "healthy"
    elif health_score >= 50:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "status": status,
        "health_score": round(health_score, 1)
    }


def _determine_services_overall_status(services: Dict[str, Dict]) -> str:
    """Determine overall status from individual service statuses."""
    if not services:
        return "unknown"

    statuses = [s.get("status", "unknown") for s in services.values()]

    if all(s == "healthy" for s in statuses):
        return "healthy"
    elif any(s == "unhealthy" for s in statuses):
        return "degraded"
    else:
        return "degraded"


def _get_degraded_features(service_status: Dict) -> list:
    """Get list of features that are degraded or unavailable."""
    degraded = []

    if service_status.get("vector_store", {}).get("status") != "healthy":
        degraded.extend(["semantic_search", "rag_queries", "document_similarity"])

    if service_status.get("task_queue", {}).get("status") != "healthy":
        degraded.extend(["background_processing", "multi_agent_tasks", "async_operations"])

    if service_status.get("multimodal", {}).get("status") != "healthy":
        degraded.extend(["audio_processing", "video_processing", "image_analysis"])

    return degraded


def _get_available_features(service_status: Dict) -> list:
    """Get list of features that are currently available."""
    available = ["basic_api", "authentication", "health_checks"]

    if service_status.get("database", {}).get("status") == "healthy":
        available.extend(["user_management", "data_persistence"])

    if service_status.get("vector_store", {}).get("status") == "healthy":
        available.extend(["semantic_search", "rag_queries", "document_similarity"])

    if service_status.get("task_queue", {}).get("status") == "healthy":
        available.extend(["background_processing", "multi_agent_tasks"])

    return available


def _get_health_recommendations(overall_status: Dict, service_status: Dict) -> list:
    """Get recommendations based on current health status."""
    recommendations = []

    if overall_status["health_score"] < 50:
        recommendations.append("System health is critical - immediate attention required")

    if service_status.get("database", {}).get("status") != "healthy":
        recommendations.append("Check database connectivity and configuration")

    if service_status.get("vector_store", {}).get("status") != "healthy":
        recommendations.append("Verify Weaviate service is running and accessible")

    if service_status.get("task_queue", {}).get("status") != "healthy":
        recommendations.append("Check Redis service and Celery worker status")

    if not recommendations:
        recommendations.append("System is operating normally")

    return recommendations


@router.get("/features", response_model=Dict[str, Any])
async def get_feature_flags():
    """
    Get current feature flag status and system capabilities.

    Returns:
        Dictionary with feature flags and capabilities information
    """
    try:
        # Refresh feature statuses
        feature_flags.refresh_all_statuses()

        # Get system capabilities
        capabilities = feature_flags.get_system_capabilities()

        # Get all feature details
        all_features = feature_flags.get_all_features()

        # Get basic mode status
        basic_mode_status = basic_mode.get_status_info()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_capabilities": capabilities,
            "features": all_features,
            "basic_mode": basic_mode_status,
            "recommendations": _get_feature_recommendations(capabilities, all_features)
        }

    except Exception as e:
        logger.error(f"Feature flags check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "system_capabilities": {"capability_score": 0, "basic_mode": True},
            "features": {},
            "basic_mode": {"basic_mode_active": True},
            "error": str(e)
        }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_system_capabilities():
    """
    Get current system capabilities and operational mode.

    Returns:
        Dictionary with system capabilities and mode information
    """
    try:
        # Get feature capabilities
        capabilities = feature_flags.get_system_capabilities()

        # Get service health
        service_status = await service_monitor.get_system_status()

        # Get circuit breaker status
        circuit_status = circuit_breaker_manager.get_health_summary()

        # Determine operational mode
        operational_mode = _determine_operational_mode(capabilities, service_status, circuit_status)

        return {
            "timestamp": datetime.now().isoformat(),
            "operational_mode": operational_mode,
            "capability_score": capabilities["capability_score"],
            "available_features": capabilities["enabled"],
            "degraded_features": capabilities["degraded"],
            "unavailable_features": capabilities["unavailable"],
            "basic_mode_active": basic_mode.is_active,
            "service_health": {
                "healthy_services": sum(1 for s in service_status.values() if s.get("status") == "healthy"),
                "degraded_services": sum(1 for s in service_status.values() if s.get("status") == "degraded"),
                "unhealthy_services": sum(1 for s in service_status.values() if s.get("status") == "unhealthy")
            },
            "circuit_breakers": {
                "status": circuit_status["status"],
                "healthy_breakers": circuit_status.get("healthy_breakers", 0),
                "failed_breakers": circuit_status.get("failed_breakers", 0)
            }
        }

    except Exception as e:
        logger.error(f"Capabilities check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "operational_mode": "basic",
            "capability_score": 0,
            "available_features": ["basic_api"],
            "degraded_features": [],
            "unavailable_features": ["vector_search", "multi_agent", "multimodal"],
            "basic_mode_active": True,
            "error": str(e)
        }


@router.post("/basic-mode/activate")
async def activate_basic_mode_endpoint(
    reason: str = "Manual activation",
    current_user = Depends(get_current_user_optional)
):
    """
    Manually activate basic mode (admin operation).

    Args:
        reason: Reason for activating basic mode

    Returns:
        Confirmation of basic mode activation
    """
    try:
        basic_mode.activate_basic_mode(reason)
        logger.info(f"Basic mode manually activated: {reason}")

        return {
            "message": "Basic mode has been activated",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "status": basic_mode.get_status_info()
        }

    except Exception as e:
        logger.error(f"Basic mode activation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@router.post("/basic-mode/deactivate")
async def deactivate_basic_mode_endpoint(current_user = Depends(get_current_user_optional)):
    """
    Manually deactivate basic mode (admin operation).

    Returns:
        Confirmation of basic mode deactivation
    """
    try:
        basic_mode.deactivate_basic_mode()
        logger.info("Basic mode manually deactivated")

        return {
            "message": "Basic mode has been deactivated",
            "timestamp": datetime.now().isoformat(),
            "status": basic_mode.get_status_info()
        }

    except Exception as e:
        logger.error(f"Basic mode deactivation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deactivation failed: {str(e)}")


def _get_feature_recommendations(capabilities: Dict, features: Dict) -> List[str]:
    """Get recommendations based on feature status."""
    recommendations = []

    if capabilities["capability_score"] < 50:
        recommendations.append("System capability is low - check service health")

    unavailable_features = capabilities.get("unavailable", [])
    if "vector_search" in unavailable_features:
        recommendations.append("Vector search unavailable - check Weaviate service")

    if "multi_agent" in unavailable_features:
        recommendations.append("Multi-agent features unavailable - check task queue service")

    if "multimodal" in unavailable_features:
        recommendations.append("Multimodal processing unavailable - check ML dependencies")

    if capabilities.get("basic_mode", False):
        recommendations.append("System is running in basic mode - limited functionality available")

    if not recommendations:
        recommendations.append("All features are operating normally")

    return recommendations


def _determine_operational_mode(capabilities: Dict, service_status: Dict, circuit_status: Dict) -> str:
    """Determine current operational mode."""
    if basic_mode.is_active:
        return "basic"

    capability_score = capabilities.get("capability_score", 0)

    if capability_score >= 90:
        return "full"
    elif capability_score >= 70:
        return "standard"
    elif capability_score >= 40:
        return "degraded"
    else:
        return "minimal"


@router.get("/errors", response_model=Dict[str, Any])
async def get_error_statistics():
    """
    Get error statistics and monitoring information.

    Returns:
        Dict containing error statistics and health information
    """
    try:
        from app.core.enhanced_error_handlers import get_error_statistics, error_handling_health_check

        # Get error statistics
        error_stats = await get_error_statistics()

        # Get error handling health
        error_health = await error_handling_health_check()

        return {
            "error_statistics": error_stats,
            "error_handling_health": error_health,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get error statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error statistics")


@router.post("/errors/reset")
async def reset_error_statistics(current_user = Depends(get_current_user_optional)):
    """
    Reset error statistics (admin operation).

    Returns:
        Dict with reset confirmation
    """
    try:
        from app.core.error_handling import error_handler

        # Clear error history
        error_handler.error_history.clear()
        error_handler.error_count = 0

        logger.info("Error statistics reset by admin")

        return {
            "message": "Error statistics reset successfully",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to reset error statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset error statistics")


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """
    Get comprehensive performance metrics.

    Returns:
        Dict containing performance statistics and monitoring data
    """
    try:
        from app.core.performance import get_performance_stats
        from app.core.caching import get_cache_stats

        # Get performance statistics
        perf_stats = get_performance_stats()

        # Get cache statistics
        cache_stats = get_cache_stats()

        return {
            "performance": perf_stats,
            "caching": cache_stats,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.post("/performance/reset")
async def reset_performance_metrics(current_user = Depends(get_current_user_optional)):
    """
    Reset performance metrics (admin operation).

    Returns:
        Dict with reset confirmation
    """
    try:
        from app.core.performance import query_profiler
        from app.core.caching import cache

        # Reset query profiler
        query_profiler.query_metrics.clear()
        query_profiler.slow_queries.clear()
        query_profiler.total_queries = 0
        query_profiler.total_time = 0.0

        # Clear caches
        cache.memory_cache.clear()
        cache.redis_cache.clear_pattern("*")

        logger.info("Performance metrics reset by admin")

        return {
            "message": "Performance metrics reset successfully",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to reset performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset performance metrics")


@router.get("/security", response_model=Dict[str, Any])
async def get_security_status():
    """
    Get comprehensive security status and monitoring information.

    Returns:
        Dict containing security statistics and monitoring data
    """
    try:
        from app.core.security_hardening import get_security_status

        # Get security status
        security_status = get_security_status()

        return {
            "security": security_status,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get security status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security status")


@router.post("/security/reset")
async def reset_security_metrics(current_user = Depends(get_current_user_optional)):
    """
    Reset security metrics and unblock IPs (admin operation).

    Returns:
        Dict with reset confirmation
    """
    try:
        from app.core.security_hardening import security_monitor, rate_limiter

        # Reset security monitoring
        security_monitor.failed_attempts.clear()
        security_monitor.suspicious_activities.clear()
        security_monitor.security_events.clear()

        # Clear rate limiting
        rate_limiter.requests.clear()
        rate_limiter.blocked_ips.clear()
        rate_limiter.user_requests.clear()
        rate_limiter.api_key_requests.clear()

        logger.info("Security metrics reset by admin")

        return {
            "message": "Security metrics reset successfully",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to reset security metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset security metrics")


@router.post("/security/unblock-ip")
async def unblock_ip(
    ip_address: str,
    current_user = Depends(get_current_user_optional)
):
    """
    Unblock a specific IP address (admin operation).

    Args:
        ip_address: IP address to unblock

    Returns:
        Dict with unblock confirmation
    """
    try:
        from app.core.security_hardening import rate_limiter

        # Validate IP address format
        try:
            import ipaddress
            ipaddress.ip_address(ip_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid IP address format")

        # Unblock IP
        if ip_address in rate_limiter.blocked_ips:
            del rate_limiter.blocked_ips[ip_address]
            logger.info(f"IP {ip_address} unblocked by admin")
            return {
                "message": f"IP {ip_address} unblocked successfully",
                "timestamp": time.time()
            }
        else:
            return {
                "message": f"IP {ip_address} was not blocked",
                "timestamp": time.time()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unblock IP: {e}")
        raise HTTPException(status_code=500, detail="Failed to unblock IP")


@router.get("/monitoring", response_model=Dict[str, Any])
async def get_monitoring_dashboard():
    """
    Get comprehensive monitoring dashboard data.

    Returns:
        Dict containing metrics, health status, and alerts
    """
    try:
        from app.core.monitoring import get_monitoring_dashboard

        # Get monitoring dashboard data
        dashboard_data = get_monitoring_dashboard()

        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring dashboard")


@router.get("/monitoring/metrics", response_model=Dict[str, Any])
async def get_metrics_summary():
    """
    Get detailed metrics summary.

    Returns:
        Dict containing all collected metrics with statistics
    """
    try:
        from app.core.monitoring import metrics_collector

        # Get metrics summary
        metrics_summary = metrics_collector.get_all_metrics_summary()

        return metrics_summary

    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


@router.get("/monitoring/alerts", response_model=Dict[str, Any])
async def get_alerts_status():
    """
    Get current alerts and alert summary.

    Returns:
        Dict containing active alerts and alert statistics
    """
    try:
        from app.core.monitoring import alert_manager

        # Get alerts
        active_alerts = alert_manager.get_active_alerts()
        alert_summary = alert_manager.get_alert_summary()

        return {
            "active_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp
                }
                for alert in active_alerts
            ],
            "summary": alert_summary,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get alerts status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts status")


@router.post("/monitoring/health-check")
async def run_comprehensive_health_check():
    """
    Run comprehensive health checks on all system components.

    Returns:
        Dict containing detailed health check results
    """
    try:
        from app.core.monitoring import health_monitor

        # Run health checks
        health_report = await health_monitor.run_health_checks()

        return health_report

    except Exception as e:
        logger.error(f"Failed to run health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to run health checks")


@router.post("/monitoring/alerts/resolve/{alert_name}")
async def resolve_alert(
    alert_name: str,
    current_user = Depends(get_current_user_optional)
):
    """
    Manually resolve an active alert (admin operation).

    Args:
        alert_name: Name of the alert to resolve

    Returns:
        Dict with resolution confirmation
    """
    try:
        from app.core.monitoring import alert_manager

        # Resolve alert
        alert_manager.resolve_alert(alert_name)

        logger.info(f"Alert {alert_name} manually resolved by admin")

        return {
            "message": f"Alert {alert_name} resolved successfully",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format for monitoring integration.

    Returns:
        Prometheus-formatted metrics
    """
    try:
        # Get all metrics from the collector
        all_metrics = metrics_collector.get_all_metrics_summary()

        prometheus_output = []
        timestamp = int(time.time() * 1000)

        # Convert AI system metrics to Prometheus format
        ai_metrics = all_metrics.get("ai_system", {})

        # LLM metrics
        llm_metrics = ai_metrics.get("llm", {})
        for metric_name, value in llm_metrics.items():
            if isinstance(value, (int, float)):
                prometheus_output.append(f"DRYAD.AI_llm_{metric_name} {value} {timestamp}")

        # Agent metrics
        agent_metrics = ai_metrics.get("agents", {})
        for metric_name, value in agent_metrics.items():
            if isinstance(value, (int, float)):
                prometheus_output.append(f"DRYAD.AI_agent_{metric_name} {value} {timestamp}")

        # Model metrics
        model_metrics = ai_metrics.get("models", {})
        for metric_name, value in model_metrics.items():
            if isinstance(value, (int, float)):
                prometheus_output.append(f"DRYAD.AI_model_{metric_name} {value} {timestamp}")

        # System metrics (if available)
        try:
            import psutil
            prometheus_output.append(f"DRYAD.AI_system_cpu_usage_percent {psutil.cpu_percent()} {timestamp}")
            memory = psutil.virtual_memory()
            prometheus_output.append(f"DRYAD.AI_system_memory_usage_percent {memory.percent} {timestamp}")
            prometheus_output.append(f"DRYAD.AI_system_memory_available_gb {memory.available / (1024**3)} {timestamp}")
        except Exception:
            pass

        # Health score
        try:
            health_status = await get_comprehensive_health_status()
            health_score = health_status.get("health_score", 0)
            prometheus_output.append(f"DRYAD.AI_health_score {health_score} {timestamp}")
        except Exception:
            pass

        return "\n".join(prometheus_output)

    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


# PlainTextResponse already imported at the top
