# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Suppress deprecation warnings for cleaner output
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Load environment variables from .env file (optional)
load_dotenv()

import logging
import time
import os

# Initialize configuration with sensible defaults
from app.core.config import config

# Initialize structured logging first
from app.core.logging_config import setup_logging, get_logger, request_logger
from app.core.error_handling import error_handler, ErrorCategory, ErrorSeverity

# Setup logging system
setup_logging()
logger = get_logger(__name__)

# Basic mode configuration from config
BASIC_MODE = config.BASIC_MODE
# Silent mode - no startup messages

# Import endpoints with optional multi-agent/agent modules to avoid heavy deps during smoke tests
from app.api.v1.endpoints import documents, realtime, docs, developer_portal, multimodal, health, websocket as websocket_realtime, auth, chat_history, orchestrator, mcp
# Optional simple endpoints
try:
    from app.api.v1.endpoints import simple_chat as simple_chat_endpoints
except Exception:
    simple_chat_endpoints = None
try:
    from app.api.v1.endpoints import simple_docs as simple_docs_endpoints
except Exception:
    simple_docs_endpoints = None
try:
    from app.api.v1.endpoints import agent as agent_endpoints
except Exception as e:
    agent_endpoints = None
    logging.getLogger(__name__).warning(f"Agent endpoints not loaded (optional): {e}")
try:
    from app.api.v1.endpoints import multi_agent as multi_agent_endpoints
except Exception as e:
    multi_agent_endpoints = None
    logging.getLogger(__name__).warning(f"Multi-Agent endpoints not loaded (optional): {e}")

# Deprecated WS endpoints (consolidated into /api/v1/realtime-ws)
# from app.api.v1.websocket import endpoints as websocket_endpoints
from app.database.database import ensure_data_directory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    ensure_data_directory()

    # Security sanity check: in production, require a stable JWT secret
    try:
        from app.core.security import ENVIRONMENT, JWT_SECRET_KEY
        if (ENVIRONMENT or "").lower() in {"prod", "production"}:
            if not os.getenv("JWT_SECRET_KEY"):
                raise RuntimeError("JWT_SECRET_KEY is required in production environment. Set it in your environment or .env")
            if not JWT_SECRET_KEY or len(str(JWT_SECRET_KEY)) < 32:
                raise RuntimeError("JWT_SECRET_KEY appears too short for production. Use secrets.token_urlsafe(48)")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Startup security check failed: {e}")
        raise

    # Initialize service monitoring
    from app.core.service_monitor import initialize_service_monitoring
    initialize_service_monitoring()

    # Start Self-Healing System (if enabled)
    guardian_task = None
    worker_task = None
    if os.getenv("ENABLE_SELF_HEALING", "false").lower() == "true":
        try:
            import asyncio
            from app.core.guardian import start_guardian
            from app.workers.self_healing_worker import start_worker

            logger.info("🛡️ Starting Self-Healing System...")
            guardian_task = asyncio.create_task(start_guardian())
            worker_task = asyncio.create_task(start_worker())
            logger.info("✅ Self-Healing System started")
        except Exception as e:
            logger.error(f"Failed to start Self-Healing System: {e}", exc_info=True)

    # Initialize feature flags and basic mode
    from app.core.feature_flags import feature_flags
    from app.core.basic_mode import basic_mode

    # Check if basic mode should be activated
    try:
        # Get initial service health (skip async health check during startup)
        from app.core.service_monitor import service_monitor

        # Use synchronous health check instead of async
        service_health = {
            'status': 'degraded',  # Assume degraded until proven otherwise
            'services': {},
            'overall_health': 0.5
        }

        # Activate basic mode if needed
        if basic_mode.should_use_basic_mode(service_health):
            basic_mode.activate_basic_mode("Critical services unavailable at startup")

        # Log system capabilities
        capabilities = feature_flags.get_system_capabilities()
        logger.info(f"System capabilities: {capabilities['capability_score']:.1f}% "
                   f"({len(capabilities['enabled'])} enabled, "
                   f"{len(capabilities['degraded'])} degraded, "
                   f"{len(capabilities['unavailable'])} unavailable)")

        # Silent mode - only log if there are issues
        if basic_mode.is_active:
            pass  # Silent - basic mode active

    except Exception as e:
        logger.error(f"Failed to initialize system health checks: {e}")
        basic_mode.activate_basic_mode(f"Health check initialization failed: {e}")

    # Check LLM status on startup - only log errors
    try:
        from app.core.llm_config import get_llm_info, get_llm_health_status

        llm_info = get_llm_info()
        health_status = get_llm_health_status()

        # Only log if there are problems
        if not llm_info['available']:
            logger.error("[CRITICAL] Local LLM system not available!")
            logger.error("[ERROR] DRYAD.AI requires local LLM for self-contained AI operation")
            logger.error("[FIX] To fix this issue:")
            logger.error("   1. Install llama-cpp-python: pip install llama-cpp-python")
            logger.error("   2. Ensure models directory exists: mkdir -p ./models")
            logger.error("   3. Set LLM_PROVIDER=llamacpp in your .env file")
            logger.error("   4. The system will auto-download models on first use")
            logger.error("[WARNING] System will fail explicitly rather than degrade to mock responses")
        elif health_status['status'] == 'unhealthy':
            logger.warning("[WARNING] LLM health issues detected")
            for issue in health_status.get('issues', []):
                logger.warning(f"   - {issue}")
        # Silent if everything is OK

    except Exception as e:
        logger.error(f"Failed to check LLM status on startup: {e}")

    # Warm up Ollama models to reduce first-request latency
    try:
        from langchain_ollama import ChatOllama

        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")  # Optional: e.g., "10m", "1h"
        # Warm up both models used by providers (llamacpp uses llama3.2:3b, ollama uses mistral:latest)
        models_to_warmup = ["llama3.2:3b", "mistral:latest"]

        logger.info("🔥 Warming up Ollama models...")

        for model in models_to_warmup:
            try:
                # Build kwargs for ChatOllama
                ollama_kwargs = {
                    "model": model,
                    "base_url": ollama_base_url,
                    "timeout": 120.0,
                }

                # Only add keep_alive if specified
                if ollama_keep_alive:
                    ollama_kwargs["keep_alive"] = ollama_keep_alive

                llm = ChatOllama(**ollama_kwargs)

                # Send dummy request to load model into memory
                await llm.ainvoke("Hello")
                logger.info(f"✅ Pre-loaded Ollama model: {model}")
            except Exception as model_error:
                logger.warning(f"⚠️ Failed to pre-load {model}: {model_error}")

        logger.info("✅ Ollama model warm-up complete")

    except Exception as e:
        logger.warning(f"⚠️ Ollama warm-up failed (non-critical): {e}")

    # Start comprehensive monitoring system
    try:
        from app.core.monitoring import start_monitoring
        start_monitoring()
        # Silent startup - only log errors
    except Exception as e:
        logger.error(f"Failed to start monitoring system: {e}")

    # Silent startup - backend is ready

    yield
    # Shutdown
    # Silent shutdown

    # Stop Self-Healing System
    if guardian_task or worker_task:
        try:
            from app.core.guardian import stop_guardian
            from app.workers.self_healing_worker import stop_worker

            logger.info("🛡️ Stopping Self-Healing System...")
            await stop_guardian()
            await stop_worker()

            # Cancel tasks
            if guardian_task:
                guardian_task.cancel()
            if worker_task:
                worker_task.cancel()

            logger.info("✅ Self-Healing System stopped")
        except Exception as e:
            logger.error(f"Error stopping Self-Healing System: {e}")

    # Shutdown audit logging system
    try:
        from app.core.audit_logging import shutdown_audit_logging
        shutdown_audit_logging()
        # Silent shutdown
    except Exception as e:
        logger.error(f"Error shutting down audit logging: {e}")

    # Silent shutdown complete


# Create the main FastAPI application instance with enhanced documentation
app = FastAPI(
    title="DRYAD.AI Backend API",
    description="""
    ## DRYAD.AI Multi-Modal AI Agent Platform

    A comprehensive backend API for multi-modal AI agent interactions, document processing,
    and real-time communication. Features include:

    * **AI Agent Chat** - Intelligent conversational AI with context awareness
    * **Document Processing** - Upload, analyze, and extract insights from documents
    * **Multi-Modal AI** - Process text, images, audio, and video content
    * **Multi-Agent Orchestration** - Coordinate specialized AI agents for complex tasks
    * **Real-Time Communication** - WebSocket-based live interactions
    * **Secure Authentication** - OAuth2 and API key authentication
    * **Performance Monitoring** - Built-in metrics and health monitoring

    ### Quick Start

    1. **Basic Mode (2-minute setup)**: `python setup.py --mode basic && python start.py --mode basic`
    2. **Get API Token**: POST to `/api/v1/auth/register` then `/api/v1/auth/login`
    3. **Start Chatting**: POST to `/api/v1/agent/chat` with your message

    ### Documentation

    * **Interactive API Docs**: Available at `/docs` (this page)
    * **Alternative UI**: Available at `/redoc`
    * **Complete Guide**: See `API_DOCUMENTATION.md` in the repository

    ### Support

    * **Health Status**: Check `/api/v1/health` for system status
    * **Performance**: Monitor `/api/v1/health/performance` for metrics
    * **Errors**: View `/api/v1/health/errors` for error statistics
    """,
    version="9.0.0",
    lifespan=lifespan,
    contact={
        "name": "DRYAD.AI Support",
        "email": "support@DRYAD.AI.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.DRYAD.AI.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "Health & Monitoring",
            "description": "System health, performance metrics, and monitoring endpoints"
        },
        {
            "name": "Authentication",
            "description": "User authentication, OAuth2, and API key management"
        },
        {
            "name": "Agent Interactions",
            "description": "Chat with AI agents and manage conversations"
        },
        {
            "name": "Document Management",
            "description": "Upload, process, and analyze documents with AI"
        },
        {
            "name": "Multi-Modal Processing",
            "description": "Process images, audio, video, and mixed content"
        },
        {
            "name": "Multi-Agent Orchestration",
            "description": "Coordinate multiple specialized AI agents"
        },
        {
            "name": "Real-Time Communication",
            "description": "WebSocket-based real-time interactions"
        }
    ]
)

# Add CORS middleware with secure configuration
def get_cors_origins(environment: str = None) -> list[str]:
    """Get CORS origins from environment with secure defaults.

    Args:
        environment: Override environment for testing purposes
    """
    # Use provided environment or get from config
    env = environment or config.ENVIRONMENT
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")

    if not cors_origins:
        # Development default - restrict to localhost only
        if env == "development":
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]
        else:
            # Production requires explicit configuration
            raise ValueError(
                "CORS_ALLOWED_ORIGINS must be explicitly configured in production. "
                "Set environment variable with comma-separated list of allowed origins."
            )

    # Parse comma-separated origins and validate
    origins = [origin.strip() for origin in cors_origins.split(",")]

    # Validate origins format
    for origin in origins:
        if origin == "*":
            if env != "development":
                raise ValueError("Wildcard CORS origins not allowed in production")
        elif not origin.startswith(("http://", "https://")):
            raise ValueError(f"Invalid CORS origin format: {origin}")

    return origins

# Configure CORS with security validation
cors_origins = get_cors_origins()
logger.info(f"Configuring CORS for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Required for HttpOnly refresh token cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Request-ID"
    ],
)

# Add input validation middleware
@app.middleware("http")
async def input_validation_middleware_handler(request: Request, call_next):
    """Input validation middleware for comprehensive input sanitization."""
    from app.core.input_validation_middleware import get_input_validation_middleware

    validation_middleware = get_input_validation_middleware()
    return await validation_middleware(request, call_next)

# Add session management middleware
@app.middleware("http")
async def session_middleware_handler(request: Request, call_next):
    """Session management middleware for secure session handling."""
    from app.core.session_middleware import get_session_middleware

    session_middleware = get_session_middleware()
    return await session_middleware(request, call_next)

# Add audit logging middleware
@app.middleware("http")
async def audit_middleware_handler(request: Request, call_next):
    """Audit logging middleware for security events and compliance."""
    from app.core.audit_middleware import get_audit_middleware

    audit_middleware = get_audit_middleware()
    return await audit_middleware(request, call_next)

# Add data protection middleware
@app.middleware("http")
async def data_protection_middleware_handler(request: Request, call_next):
    """Data protection middleware for PII detection and encryption."""
    from app.core.data_protection_middleware import get_data_protection_middleware

    data_protection = get_data_protection_middleware()
    return await data_protection(request, call_next)

# Add advanced rate limiting middleware
from app.core.advanced_rate_limiting_middleware import AdvancedRateLimitingMiddleware, DDoSProtectionMiddleware

# Add DDoS protection (outermost layer)
app.add_middleware(DDoSProtectionMiddleware)

# Add advanced rate limiting
app.add_middleware(AdvancedRateLimitingMiddleware, enable_ddos_protection=True)

# Add enhanced security middleware
@app.middleware("http")
async def enhanced_security_middleware(request: Request, call_next):
    """Enhanced security middleware with hardening features."""
    from app.core.security_hardening import (
        rate_limiter, security_monitor, rate_limit_middleware,
        security_monitoring_middleware
    )
    from app.core.advanced_security_monitoring import get_advanced_security_monitor

    client_ip = request.client.host if request.client else "unknown"
    advanced_monitor = get_advanced_security_monitor()

    try:
        # Rate limiting check
        rate_limit_middleware(request)

        # Security monitoring
        security_monitoring_middleware(request)

        # Record request in advanced monitoring
        advanced_monitor.record_security_event(
            "api_request",
            {
                "endpoint": str(request.url.path),
                "method": request.method,
                "user_agent": request.headers.get("user-agent", "unknown")
            },
            client_ip
        )

        # Process request
        response = await call_next(request)

        # Check for PII detection in response
        if hasattr(request.state, 'pii_detected') and request.state.pii_detected:
            advanced_monitor.record_security_event(
                "pii_detected_in_request",
                {"endpoint": str(request.url.path), "method": request.method},
                client_ip
            )

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp

        # Add rate limit headers
        rate_info = rate_limiter.get_rate_limit_info(f"ip_hour_{client_ip}")
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response

    except HTTPException:
        # Re-raise HTTP exceptions (like rate limiting)
        raise
    except Exception as e:
        # Log security-related errors
        logger.error(f"Security middleware error: {e}")
        raise

# Add request logging and error handling middleware
@app.middleware("http")
async def logging_and_error_middleware(request: Request, call_next):
    """Enhanced middleware for request logging and error handling."""
    start_time = time.time()

    try:
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request completion
        await request_logger.log_request(request, response, process_time)

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        # Handle unexpected errors
        process_time = time.time() - start_time

        # Create structured error
        error = error_handler.create_structured_error(
            message=f"Unhandled error in request processing: {str(e)}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            context={
                "method": request.method,
                "path": request.url.path,
                "process_time": process_time
            }
        )

        # Log error
        error_handler.log_error(error, logger)

        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error_id": error.error_id,
                "message": error.user_message,
                "recovery_suggestions": error.recovery_suggestions
            }
        )

# Enhanced Global Error Handling with Structured Errors
from app.core.enhanced_error_handlers import (
    enhanced_http_exception_handler,
    enhanced_validation_exception_handler,
    enhanced_sqlalchemy_exception_handler,
    enhanced_general_exception_handler,
    circuit_breaker_exception_handler,
    llm_provider_exception_handler,
    vector_store_exception_handler
)

# Add enhanced exception handlers
app.add_exception_handler(HTTPException, enhanced_http_exception_handler)
app.add_exception_handler(RequestValidationError, enhanced_validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, enhanced_sqlalchemy_exception_handler)
app.add_exception_handler(Exception, enhanced_general_exception_handler)

# Add specific service exception handlers
try:
    from app.core.circuit_breaker import CircuitBreakerOpenException
    app.add_exception_handler(CircuitBreakerOpenException, circuit_breaker_exception_handler)
except ImportError:
    logger.warning("Circuit breaker not available - skipping handler registration")

# Add LLM and vector store specific handlers
try:
    import openai
    app.add_exception_handler(openai.OpenAIError, llm_provider_exception_handler)
except ImportError:
    pass

try:
    import weaviate
    app.add_exception_handler(weaviate.exceptions.WeaviateBaseError, vector_store_exception_handler)
except ImportError:
    pass

# Include the API routers from different modules
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# API Key Management
try:
    from app.api.v1.endpoints import api_keys
    app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
    logger.info("API key management endpoints enabled")
except ImportError as e:
    logger.warning(f"API key management not available: {e}")

# Security Dashboard
try:
    from app.api.v1.endpoints import security_dashboard
    app.include_router(security_dashboard.router, prefix="/api/v1/security", tags=["Security Dashboard"])
    logger.info("Security dashboard endpoints enabled")
except ImportError as e:
    logger.warning(f"Security dashboard not available: {e}")

# Self-Healing System
try:
    from app.api.v1.endpoints import self_healing
    app.include_router(self_healing.router, prefix="/api/v1/orchestrator", tags=["Self-Healing"])
    logger.info("Self-healing endpoints enabled")
except ImportError as e:
    logger.warning(f"Self-healing system not available: {e}")

# Self-Healing UI
try:
    from app.api.v1.endpoints import self_healing_ui
    app.include_router(self_healing_ui.router, prefix="/api/v1", tags=["Self-Healing-UI"])
    logger.info("Self-healing UI endpoints enabled")
except ImportError as e:
    logger.warning(f"Self-healing UI not available: {e}")
if agent_endpoints is not None:
    app.include_router(agent_endpoints.router, prefix="/api/v1/agent", tags=["Agent"])
if simple_chat_endpoints is not None:
    app.include_router(simple_chat_endpoints.router, prefix="/api/v1/agent", tags=["Simple Chat"])
if simple_docs_endpoints is not None:
    app.include_router(simple_docs_endpoints.router, prefix="/api/v1", tags=["Simple Documentation"])
if multi_agent_endpoints is not None:
    app.include_router(multi_agent_endpoints.router, prefix="/api/v1/multi-agent", tags=["Multi-Agent"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents & RAG"])
# document_upload endpoints are optional; real-time upload uses /api/v1/documents/upload/realtime

# Dryad Knowledge Tree System
try:
    from app.api.v1.endpoints import dryad
    app.include_router(dryad.router, prefix="/api/v1/dryad", tags=["Dryad"])
    logger.info("Dryad knowledge tree endpoints enabled")
except ImportError as e:
    logger.warning(f"Dryad endpoints not available: {e}")

# RADAR Integration System
try:
    from app.api.v1.endpoints import radar
    app.include_router(radar.router, prefix="/api/v1/radar", tags=["RADAR Integration"])
    logger.info("✅ RADAR integration endpoints enabled")
except ImportError as e:
    logger.warning(f"RADAR endpoints not available: {e}")

app.include_router(chat_history.router, prefix="/api/v1/history", tags=["Chat History"])
app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["Orchestrator"])
# Consolidated: use /api/v1/realtime-ws routes only
app.include_router(websocket_realtime.router, prefix="/api/v1/realtime-ws", tags=["Real-time WebSocket"])
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["Real-time API"])
app.include_router(docs.router, prefix="/docs", tags=["Documentation"])
app.include_router(developer_portal.router, prefix="/api/v1/developer-portal", tags=["Developer Portal"])
app.include_router(multimodal.router, prefix="/api/v1/multimodal", tags=["Multi-Modal"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health & Monitoring"])
app.include_router(mcp.router, prefix="/api/v1", tags=["MCP"])

# Agent Creation Studio Enhancements - Phase 1
try:
    from app.api.v1.endpoints import agent_enhancements
    app.include_router(agent_enhancements.router, prefix="/api/v1", tags=["Agent Enhancements"])
    logger.info("✅ Agent Creation Studio Enhancement endpoints enabled (Phase 1)")
except ImportError as e:
    logger.warning(f"Agent enhancement endpoints not available: {e}")

# Agent Creation Studio Enhancements - Phase 2 (Specialization & Skill Trees)
try:
    from app.api.v1.endpoints import specializations
    app.include_router(specializations.router, prefix="/api/v1", tags=["Specializations"])
    logger.info("✅ Specialization endpoints enabled (Phase 2)")
except ImportError as e:
    logger.warning(f"Specialization endpoints not available: {e}")

try:
    from app.api.v1.endpoints import skill_trees
    app.include_router(skill_trees.router, prefix="/api/v1", tags=["Skill Trees"])
    logger.info("✅ Skill Tree endpoints enabled (Phase 2)")
except ImportError as e:
    logger.warning(f"Skill Tree endpoints not available: {e}")

try:
    from app.api.v1.endpoints import skill_progress
    app.include_router(skill_progress.router, prefix="/api/v1", tags=["Skill Progress"])
    logger.info("✅ Skill Progress endpoints enabled (Phase 2)")
except ImportError as e:
    logger.warning(f"Skill Progress endpoints not available: {e}")

try:
    from app.api.v1.endpoints import progression_paths
    app.include_router(progression_paths.router, prefix="/api/v1", tags=["Progression Paths"])
    logger.info("✅ Progression Path endpoints enabled (Phase 2)")
except ImportError as e:
    logger.warning(f"Progression Path endpoints not available: {e}")

# Agentic University System (Integrated Standalone Module)
try:
    from app.university_system.main import app as university_app
    app.mount("/university", university_app)
    logger.info("✅ University System mounted at /university")
except ImportError as e:
    logger.warning(f"University System not available: {e}")

# Advanced workflows and agents
try:
    from app.api.v1.endpoints import workflows
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Advanced Workflows"])
except ImportError as e:
    logger.warning(f"Advanced workflows not available: {e}")

# Agent Registry for 20-agent swarm
try:
    from app.api.v1.endpoints import agent_registry
    app.include_router(agent_registry.router, prefix="/api/v1", tags=["Agent Registry"])
    logger.info("✅ Agent Registry endpoints enabled")
except ImportError as e:
    logger.warning(f"Agent Registry not available: {e}")

# Project Manager Agent
try:
    from app.api.v1.endpoints import project_manager
    app.include_router(project_manager.router, prefix="/api/v1", tags=["Project Manager"])
    logger.info("✅ Project Manager endpoints enabled")
except ImportError as e:
    logger.warning(f"Project Manager not available: {e}")

# Codebase Analyst Agent (Phase 2 - Tier 2 Specialist)
try:
    from app.api.v1.endpoints import codebase_analyst
    app.include_router(codebase_analyst.router, prefix="/api/v1", tags=["Codebase Analyst"])
    logger.info("✅ Codebase Analyst Agent endpoints enabled")
except ImportError as e:
    logger.warning(f"Codebase Analyst Agent not available: {e}")

# Code Editor Agent (Phase 2 - Tier 2 Specialist)
try:
    from app.api.v1.endpoints import code_editor
    app.include_router(code_editor.router, prefix="/api/v1", tags=["Code Editor"])
    logger.info("✅ Code Editor Agent endpoints enabled")
except ImportError as e:
    logger.warning(f"Code Editor Agent not available: {e}")

# Test Engineer Agent (Phase 2 - Tier 2 Specialist)
try:
    from app.api.v1.endpoints import test_engineer
    app.include_router(test_engineer.router, prefix="/api/v1", tags=["Test Engineer"])
    logger.info("✅ Test Engineer Agent endpoints enabled")
except ImportError as e:
    logger.warning(f"Test Engineer Agent not available: {e}")

# Production-ready AI workflows
try:
    from app.api.v1.endpoints import ai_workflows
    app.include_router(ai_workflows.router, prefix="/api/v1/ai-workflows", tags=["AI Workflows"])
except ImportError as e:
    logger.warning(f"AI workflows not available: {e}")

# Agent Creation Studio
try:
    from app.api.v1.endpoints import agent_studio
    app.include_router(agent_studio.router, prefix="/api/v1/agent-studio", tags=["Agent Studio"])
    logger.info("✅ Agent Creation Studio endpoints enabled")
except ImportError as e:
    logger.warning(f"Agent Creation Studio not available: {e}")

# Agent Studio Webhooks
try:
    from app.api.v1.endpoints import agent_studio_webhooks
    app.include_router(agent_studio_webhooks.router, prefix="/api/v1/agent-studio", tags=["Agent Studio Webhooks"])
    logger.info("✅ Agent Studio Webhook endpoints enabled")
except ImportError as e:
    logger.warning(f"Agent Studio Webhooks not available: {e}")

# Deployment Integration
try:
    from app.api.v1.endpoints import deployment_integration
    app.include_router(deployment_integration.router, prefix="/api/v1", tags=["Deployment Integration"])
    logger.info("✅ Deployment Integration endpoints enabled")
except ImportError as e:
    logger.warning(f"Deployment Integration not available: {e}")

# Tool Registry (Agent Enhancements - Phase 3)
try:
    from app.api.v1.endpoints import tool_registry
    app.include_router(tool_registry.router, prefix="/api/v1", tags=["Tool Registry"])
    logger.info("✅ Tool Registry endpoints enabled")
except ImportError as e:
    logger.warning(f"Tool Registry not available: {e}", exc_info=True)

# Memory Guild (Level 1 Component)
try:
    from app.api.v1.endpoints import memory
    app.include_router(memory.router, prefix="/api/v1", tags=["Memory Guild"])
    logger.info("✅ Memory Guild endpoints enabled")
except ImportError as e:
    logger.warning(f"Memory Guild not available: {e}", exc_info=True)

# HITL Approvals (Agent Enhancements - Phase 3)
try:
    from app.api.v1.endpoints import hitl_approvals
    app.include_router(hitl_approvals.router, prefix="/api/v1", tags=["HITL Approvals"])
    logger.info("✅ HITL Approval endpoints enabled")
except ImportError as e:
    logger.warning(f"HITL Approvals not available: {e}")

# Collaboration (Agent Enhancements - Phase 3)
try:
    from app.api.v1.endpoints import collaboration
    app.include_router(collaboration.router, prefix="/api/v1", tags=["Collaboration"])
    logger.info("✅ Collaboration endpoints enabled")
except ImportError as e:
    logger.warning(f"Collaboration not available: {e}")

# Guardrails (Agent Enhancements - Phase 3)
try:
    from app.api.v1.endpoints import guardrails
    app.include_router(guardrails.router, prefix="/api/v1", tags=["Guardrails"])
    logger.info("✅ Guardrail endpoints enabled")
except ImportError as e:
    logger.warning(f"Guardrails not available: {e}")

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    # Build dynamic feature list based on actual availability
    features = ["REST API", "Interactive Documentation", "Developer Portal"]
    endpoints = {"rest_api": "/docs"}

    # Add features based on configuration and availability
    if config.ENABLE_GRAPHQL:
        try:
            from app.api.v1.graphql.schema import GRAPHQL_AVAILABLE
            if GRAPHQL_AVAILABLE:
                features.append("GraphQL API")
                endpoints["graphql"] = "/graphql"
        except ImportError:
            pass

    if config.ENABLE_MULTI_AGENT:
        features.append("Multi-Agent Workflows")

    # Always available features
    features.extend([
        "WebSocket Real-time Communication",
        "Document Management",
        "Model Context Protocol (MCP)"
    ])

    endpoints.update({
        "websocket": "/api/v1/ws/ws",
        "mcp": "/api/v1/mcp",
        "mcp_capabilities": "/api/v1/mcp/capabilities"
    })

    # Add optional features based on configuration
    if config.ENABLE_VECTOR_SEARCH:
        features.append("Vector Search & RAG")

    if config.ENABLE_TASK_QUEUE:
        features.append("Asynchronous Task Orchestration")

    if config.ENABLE_MULTIMODAL:
        features.append("Multi-Modal Processing (Audio, Video, Image)")
        endpoints["multimodal"] = "/api/v1/multimodal"

    return {
        "message": "Welcome to the DRYAD.AI API!",
        "version": "9.0.0",
        "install_tier": config.INSTALL_TIER,
        "basic_mode": config.BASIC_MODE,
        "features": features,
        "endpoints": endpoints,
        "configuration": config.get_feature_status()
    }


# Add GraphQL endpoint with improved error handling
try:
    from app.api.v1.graphql.schema import graphql_schema, GRAPHQL_AVAILABLE

    if GRAPHQL_AVAILABLE:
        from strawberry.fastapi import GraphQLRouter
        graphql_app = GraphQLRouter(graphql_schema)
        app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])
        logger.info("GraphQL endpoints enabled")
    else:
        # GraphQL schema is placeholder - provide helpful endpoint
        @app.get("/graphql", tags=["GraphQL"])
        async def graphql_unavailable():
            return {
                "error": "GraphQL not available",
                "message": "Install strawberry-graphql[fastapi] to enable GraphQL endpoints",
                "install_command": "pip install strawberry-graphql[fastapi]"
            }
        logger.warning("GraphQL endpoints disabled - strawberry not available")

except ImportError as e:
    # Fallback if schema import fails completely
    logger.warning(f"GraphQL schema import failed: {e}")

    @app.get("/graphql", tags=["GraphQL"])
    async def graphql_unavailable():
        return {
            "error": "GraphQL not available",
            "message": "Install strawberry-graphql[fastapi] to enable GraphQL endpoints",
            "install_command": "pip install strawberry-graphql[fastapi]"
        }


@app.get("/api/v1/admin/traffic-dashboard", tags=["Admin"])
async def get_traffic_dashboard():
    """Get traffic statistics and rate limiting dashboard."""
    from app.core.advanced_rate_limiting_middleware import get_traffic_dashboard

    try:
        dashboard_data = await get_traffic_dashboard()
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get traffic dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve traffic statistics"
        )
