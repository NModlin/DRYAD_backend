# app/database/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import performance monitoring
from app.core.performance import setup_database_monitoring, pool_manager

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/DRYAD.AI.db")

# Convert SQLite URL to async version for aiosqlite
if DATABASE_URL.startswith("sqlite:///"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create sync engine for Alembic migrations
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create async engine for FastAPI with performance monitoring
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Set up database monitoring and connection pool optimization
setup_database_monitoring(engine)
setup_database_monitoring(async_engine.sync_engine)
pool_manager.configure_pool(engine)
pool_manager.configure_pool(async_engine.sync_engine)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
async def get_db():
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create data directory if it doesn't exist
def ensure_data_directory():
    """Ensure the data directory exists for SQLite database."""
    if "sqlite" in DATABASE_URL:
        data_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
        if data_dir and not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except PermissionError:
                # Directory might be mounted as volume, skip creation
                pass
