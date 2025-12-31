from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from dryad.infrastructure.database import init_db
from dryad.api.v1 import auth, tools, knowledge, agents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    await init_db()
    yield
    # Shutdown: Clean resources if needed

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

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service status."""
    return {
        "status": "healthy",
        "version": "10.0.0",
        "service": "DRYAD.AI Backend"
    }

def start():
    """Entry point for script execution."""
    uvicorn.run("dryad.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
