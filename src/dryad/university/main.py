"""
Main FastAPI application for Uni0 University System
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from dryad.university.core.config import settings
from dryad.university.core.logging import configure_logging, RequestIDMiddleware
from dryad.university.database.database import engine, Base, get_db
from dryad.university.api.v1.router import api_router
from dryad.university.middleware.security import SecurityHeadersMiddleware, InputValidationMiddleware, ErrorHandlingMiddleware
from dryad.university.middleware.metrics import PrometheusMiddleware
from dryad.university.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    # Initialize application state
    app.state.db = get_db
    app.state.settings = settings
    
    yield  # Application runs here
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Uni0 University System - AI Agent Training Platform",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add security middleware (order matters - add in reverse order)
# app.add_middleware(ErrorHandlingMiddleware)  # Temporarily disabled for debugging
app.add_middleware(PrometheusMiddleware)  # Add Prometheus metrics tracking
app.add_middleware(InputValidationMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)  # Add request ID tracking

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Mount static files (for future UI)
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": request.url.path
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

# Application metadata
def get_app_info():
    """Get application information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI Agent Training University System",
        "features": [
            "University Management",
            "Agent Training Curriculum",
            "Skill Tree Progression", 
            "Competition System",
            "Real-time WebSocket Communication",
            "RESTful API"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "health": "/health",
            "universities": "/api/v1/universities",
            "curriculum": "/api/v1/curriculum",
            "competitions": "/api/v1/competitions",
            "websocket": "/api/v1/ws",
            "authentication": "/api/v1/auth"
        }
    }

# Export application for use with uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )