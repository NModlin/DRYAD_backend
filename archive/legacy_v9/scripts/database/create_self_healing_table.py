"""
Create self_healing_tasks table manually
"""

import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal, Base
from app.database.self_healing_models import SelfHealingTask


async def create_table():
    """Create the self_healing_tasks table."""
    # Import the async engine
    from app.database.database import async_engine

    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ self_healing_tasks table created successfully")


if __name__ == "__main__":
    asyncio.run(create_table())

