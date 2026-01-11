from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from dryad.infrastructure.database import init_db
from dryad.api.v1 import auth, tools, knowledge, agents


# Include Restored Legacy Routers
from dryad.api.v1 import dryad, orchestrator
# TODO: Created corresponding routers for these services
# from dryad.services.content import engine as content_engine
# from dryad.services.hitl import hitl_approval_service as hitl_service
# from dryad.services.multimodal import api as multimodal_api

# Initialize Enhanced Orchestrator
from dryad.core.orchestrator import enhanced_orchestrator
from dryad.core.guardian import Guardian
from dryad.services.memory_guild.coordinator import MemoryCoordinator

# Initialize Global Services
guardian = Guardian()
memory_guild = MemoryCoordinator()

from dryad.integrations.dryad_teams_notifier import teams_notifier
# teams_notifier.send_notification("DRYAD System Startup Initiated")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    await init_db()
    
    # Start Guardian
    await guardian.start()
    
    # Initialize Memory Guild
    await memory_guild.initialize()
    
    yield
    # Shutdown: Clean resources if needed
    await guardian.stop()
    await memory_guild.shutdown()

app = FastAPI(
    title="DRYAD.AI Backend",
    version="10.0.0",
    description="Refactored Clean Architecture Backend for DRYAD.AI",
    lifespan=lifespan
)

# CORS (Configured for development, tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])

# Include Legacy Routers
app.include_router(dryad.router, prefix="/api/v1/dryad", tags=["dryad"])
app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
# app.include_router(multimodal_api.router, prefix="/api/v1/multimodal", tags=["multimodal"])


def start():
    """Entry point for script execution."""
    uvicorn.run("dryad.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
