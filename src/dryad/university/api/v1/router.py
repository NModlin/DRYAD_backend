"""
API router for Uni0 version 1 endpoints
"""

from fastapi import APIRouter

from .endpoints import (
    enhanced_university,
    health,
    universities,
    curriculum,
    competitions,
    websocket,
    auth
)

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    enhanced_university.router,
    prefix="/enhanced-university",
    tags=["Enhanced University"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health & Monitoring"]
)

api_router.include_router(
    universities.router,
    prefix="/universities",
    tags=["Universities"]
)

api_router.include_router(
    curriculum.router,
    prefix="/curriculum",
    tags=["Curriculum"]
)

api_router.include_router(
    competitions.router,
    prefix="/competitions",
    tags=["Competitions"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Additional endpoints that might be added later
# api_router.include_router(
#     agents.router,
#     prefix="/agents",
#     tags=["Agents"]
# )

# api_router.include_router(
#     skills.router,
#     prefix="/skills",
#     tags=["Skills"]
# )

# api_router.include_router(
#     analytics.router,
#     prefix="/analytics",
#     tags=["Analytics"]
# )

# Export the router for use in main application
__all__ = ["api_router"]