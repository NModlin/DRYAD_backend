# Task 2-28: Database Transaction Management

**Phase:** 2 - Performance & Production Readiness  
**Week:** 5 - Performance Optimization  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement comprehensive database transaction management patterns with proper isolation levels, rollback handling, and transaction middleware to ensure data consistency.

---

## 🎯 OBJECTIVES

1. Document transaction patterns and best practices
2. Implement transaction middleware
3. Add transaction decorators for services
4. Configure isolation levels
5. Implement savepoints for nested transactions
6. Test transaction rollback scenarios

---

## 📊 CURRENT STATE

**Existing:**
- SQLAlchemy async sessions
- Basic transaction support
- Some manual transaction handling

**Gaps:**
- No standardized transaction patterns
- No transaction middleware
- No isolation level configuration
- No nested transaction support

---

## 🔧 IMPLEMENTATION

### 1. Transaction Patterns

Create `app/core/transactions.py`:

```python
"""
Database Transaction Management

Patterns and utilities for transaction handling.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, TypeVar
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from app.database.database import get_db

logger = logging.getLogger(__name__)

T = TypeVar("T")


@asynccontextmanager
async def transaction(
    db: AsyncSession,
    isolation_level: str | None = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Transaction context manager.
    
    Args:
        db: Database session
        isolation_level: Transaction isolation level
    
    Yields:
        Database session within transaction
    
    Example:
        async with transaction(db) as tx:
            await tx.execute(...)
            await tx.commit()
    """
    if isolation_level:
        await db.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")
    
    try:
        yield db
        await db.commit()
        logger.debug("Transaction committed")
    except Exception as e:
        await db.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise


@asynccontextmanager
async def savepoint(db: AsyncSession, name: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Savepoint context manager for nested transactions.
    
    Args:
        db: Database session
        name: Savepoint name
    
    Yields:
        Database session with savepoint
    
    Example:
        async with savepoint(db, "sp1") as sp:
            await sp.execute(...)
    """
    await db.execute(f"SAVEPOINT {name}")
    
    try:
        yield db
        logger.debug(f"Savepoint {name} released")
    except Exception as e:
        await db.execute(f"ROLLBACK TO SAVEPOINT {name}")
        logger.error(f"Rolled back to savepoint {name}: {e}")
        raise
    finally:
        await db.execute(f"RELEASE SAVEPOINT {name}")


def transactional(isolation_level: str | None = None):
    """
    Decorator for transactional service methods.
    
    Args:
        isolation_level: Transaction isolation level
    
    Example:
        @transactional(isolation_level="SERIALIZABLE")
        async def create_user(self, db: AsyncSession, data: UserCreate):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract db session from kwargs
            db = kwargs.get("db")
            if not db:
                raise ValueError("Database session required in kwargs")
            
            async with transaction(db, isolation_level):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class TransactionManager:
    """Manages database transactions."""
    
    def __init__(self):
        self.active_transactions: dict[str, AsyncSession] = {}
    
    async def begin_transaction(
        self,
        transaction_id: str,
        isolation_level: str | None = None
    ) -> AsyncSession:
        """
        Begin a new transaction.
        
        Args:
            transaction_id: Unique transaction identifier
            isolation_level: Transaction isolation level
        
        Returns:
            Database session
        """
        async for db in get_db():
            if isolation_level:
                await db.execute(
                    f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
                )
            
            self.active_transactions[transaction_id] = db
            logger.info(f"Transaction {transaction_id} started")
            return db
    
    async def commit_transaction(self, transaction_id: str) -> None:
        """
        Commit transaction.
        
        Args:
            transaction_id: Transaction identifier
        """
        db = self.active_transactions.get(transaction_id)
        if not db:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        await db.commit()
        del self.active_transactions[transaction_id]
        logger.info(f"Transaction {transaction_id} committed")
    
    async def rollback_transaction(self, transaction_id: str) -> None:
        """
        Rollback transaction.
        
        Args:
            transaction_id: Transaction identifier
        """
        db = self.active_transactions.get(transaction_id)
        if not db:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        await db.rollback()
        del self.active_transactions[transaction_id]
        logger.info(f"Transaction {transaction_id} rolled back")


# Global transaction manager
transaction_manager = TransactionManager()
```

---

### 2. Transaction Middleware

Create `app/middleware/transaction.py`:

```python
"""
Transaction Middleware

Automatic transaction management for API requests.
"""
from __future__ import annotations

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.database.database import get_db

logger = logging.getLogger(__name__)


class TransactionMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic transaction management."""
    
    # Methods that should use transactions
    TRANSACTIONAL_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with transaction management."""
        
        # Only use transactions for write operations
        if request.method not in self.TRANSACTIONAL_METHODS:
            return await call_next(request)
        
        # Create database session
        async for db in get_db():
            request.state.db = db
            
            try:
                # Process request
                response = await call_next(request)
                
                # Commit on success (2xx status codes)
                if 200 <= response.status_code < 300:
                    await db.commit()
                    logger.debug(
                        f"Transaction committed for {request.method} {request.url.path}"
                    )
                else:
                    await db.rollback()
                    logger.warning(
                        f"Transaction rolled back for {request.method} {request.url.path} "
                        f"(status: {response.status_code})"
                    )
                
                return response
                
            except Exception as e:
                await db.rollback()
                logger.error(
                    f"Transaction rolled back due to error: {e}",
                    exc_info=True
                )
                raise
```

---

### 3. Service Layer Example

Create `app/services/user_service.py`:

```python
"""
User Service with Transaction Management

Example service using transaction patterns.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import User
from app.core.transactions import transactional, savepoint


class UserService:
    """User service with transaction management."""
    
    @transactional(isolation_level="READ COMMITTED")
    async def create_user_with_profile(
        self,
        db: AsyncSession,
        user_data: dict,
        profile_data: dict
    ) -> User:
        """
        Create user with profile in a transaction.
        
        Args:
            db: Database session
            user_data: User data
            profile_data: Profile data
        
        Returns:
            Created user
        """
        # Create user
        user = User(**user_data)
        db.add(user)
        await db.flush()  # Get user ID
        
        # Create profile with savepoint
        async with savepoint(db, "create_profile"):
            profile = UserProfile(user_id=user.id, **profile_data)
            db.add(profile)
            await db.flush()
        
        return user
    
    async def update_user_balance(
        self,
        db: AsyncSession,
        user_id: str,
        amount: float
    ) -> User:
        """
        Update user balance with serializable isolation.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to add/subtract
        
        Returns:
            Updated user
        """
        # Use SERIALIZABLE for financial operations
        await db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        
        # Lock row for update
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one()
        
        # Update balance
        user.balance += amount
        await db.flush()
        
        return user
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Transaction patterns documented
- [ ] Transaction middleware implemented
- [ ] Transactional decorator working
- [ ] Savepoint support implemented
- [ ] Isolation levels configurable
- [ ] Rollback scenarios tested
- [ ] Service layer examples created

---

## 🧪 TESTING

```python
# tests/test_transactions.py
"""Tests for transaction management."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.transactions import transaction, savepoint


@pytest.mark.asyncio
async def test_transaction_commit(db: AsyncSession):
    """Test transaction commits on success."""
    async with transaction(db):
        # Perform operations
        pass
    # Transaction should be committed


@pytest.mark.asyncio
async def test_transaction_rollback(db: AsyncSession):
    """Test transaction rolls back on error."""
    with pytest.raises(ValueError):
        async with transaction(db):
            raise ValueError("Test error")
    # Transaction should be rolled back


@pytest.mark.asyncio
async def test_savepoint(db: AsyncSession):
    """Test savepoint functionality."""
    async with transaction(db):
        # Create savepoint
        async with savepoint(db, "sp1"):
            # Operations within savepoint
            pass
```

---

## 📝 NOTES

- Use appropriate isolation levels
- Always handle rollbacks
- Test concurrent transactions
- Monitor transaction duration
- Use savepoints for nested operations


