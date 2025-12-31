"""
Setup Test User in Database

Creates a test user in the database for automated testing.
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import AsyncSessionLocal
from app.database.models import User
from sqlalchemy import select


async def setup_test_user():
    """Create or update test user in database."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if test user exists
            result = await session.execute(
                select(User).where(User.id == "test-user-123")
            )
            user = result.scalar_one_or_none()
            
            if user:
                print("✅ Test user already exists")
                print(f"   ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Name: {user.name}")
                print(f"   Roles: {user.roles}")
                print(f"   Permissions: {user.permissions}")
            else:
                # Create test user
                user = User(
                    id="test-user-123",
                    email="test@example.com",
                    name="Test User",
                    provider="test",
                    provider_id="test_provider_id",
                    picture=None,
                    email_verified=True,
                    roles=["user", "admin"],
                    permissions=["read", "write", "delete", "admin"],
                    is_active=True,
                    is_verified=True
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                print("✅ Test user created successfully")
                print(f"   ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Name: {user.name}")
                print(f"   Roles: {user.roles}")
                print(f"   Permissions: {user.permissions}")
            
            return user
            
        except Exception as e:
            print(f"❌ Error setting up test user: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(setup_test_user())

