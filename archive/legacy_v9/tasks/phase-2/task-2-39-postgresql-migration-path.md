# Task 2-39: PostgreSQL Migration Path

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** CRITICAL  
**Estimated Hours:** 6 hours

---

## 📋 OVERVIEW

Implement migration path from SQLite to PostgreSQL for production deployment, including data migration scripts, configuration updates, and testing procedures.

---

## 🎯 OBJECTIVES

1. Set up PostgreSQL database
2. Create migration scripts
3. Update database configuration
4. Migrate existing data
5. Test PostgreSQL integration
6. Document migration procedures

---

## 📊 CURRENT STATE

**Existing:**
- SQLite database for development
- SQLAlchemy models defined
- Alembic migrations configured

**Gaps:**
- No PostgreSQL configuration
- No migration scripts
- No data migration procedures
- No PostgreSQL testing

---

## 🔧 IMPLEMENTATION

### 1. PostgreSQL Docker Configuration

Update `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: dryad-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-dryad}
      POSTGRES_USER: ${POSTGRES_USER:-dryad_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "-E UTF8 --locale=en_US.UTF-8"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/database/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - gremlins-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-dryad_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
```

---

### 2. PostgreSQL Initialization Script

Create `scripts/database/init-postgres.sql`:

```sql
-- PostgreSQL Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For indexing

-- Create schemas
CREATE SCHEMA IF NOT EXISTS dryad;

-- Set default schema
SET search_path TO dryad, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA dryad TO dryad_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dryad TO dryad_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dryad TO dryad_user;

-- Configure settings
ALTER DATABASE dryad SET timezone TO 'UTC';
```

---

### 3. Data Migration Script

Create `scripts/database/migrate-to-postgres.py`:

```python
#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

Migrates data from SQLite to PostgreSQL.
"""
from __future__ import annotations

import asyncio
import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_data(
    sqlite_url: str,
    postgres_url: str
):
    """
    Migrate data from SQLite to PostgreSQL.
    
    Args:
        sqlite_url: SQLite database URL
        postgres_url: PostgreSQL database URL
    """
    logger.info("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_async_engine(postgres_url)
    
    # Reflect SQLite schema
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # Get table names in dependency order
    table_names = [
        "users",
        "conversations",
        "messages",
        "documents",
        "document_chunks",
        "groves",
        "branches",
        "vessels",
        "dialogues",
        "dialogue_messages",
    ]
    
    # Migrate each table
    for table_name in table_names:
        if table_name not in metadata.tables:
            logger.warning(f"⚠️  Table {table_name} not found, skipping")
            continue
        
        logger.info(f"📦 Migrating table: {table_name}")
        
        table = metadata.tables[table_name]
        
        # Read from SQLite
        with sqlite_engine.connect() as sqlite_conn:
            rows = sqlite_conn.execute(table.select()).fetchall()
            logger.info(f"  Found {len(rows)} rows")
        
        if not rows:
            logger.info(f"  No data to migrate")
            continue
        
        # Write to PostgreSQL
        async with postgres_engine.begin() as postgres_conn:
            # Convert rows to dicts
            data = [dict(row._mapping) for row in rows]
            
            # Insert data
            await postgres_conn.execute(table.insert(), data)
            logger.info(f"  ✅ Migrated {len(data)} rows")
    
    logger.info("✅ Migration complete!")
    
    # Close engines
    await postgres_engine.dispose()
    sqlite_engine.dispose()


async def verify_migration(
    sqlite_url: str,
    postgres_url: str
):
    """
    Verify migration by comparing row counts.
    
    Args:
        sqlite_url: SQLite database URL
        postgres_url: PostgreSQL database URL
    """
    logger.info("🔍 Verifying migration...")
    
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_async_engine(postgres_url)
    
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    mismatches = []
    
    for table_name, table in metadata.tables.items():
        # Count SQLite rows
        with sqlite_engine.connect() as conn:
            sqlite_count = conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).scalar()
        
        # Count PostgreSQL rows
        async with postgres_engine.begin() as conn:
            result = await conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            )
            postgres_count = result.scalar()
        
        if sqlite_count != postgres_count:
            mismatches.append({
                "table": table_name,
                "sqlite": sqlite_count,
                "postgres": postgres_count
            })
            logger.error(
                f"❌ Mismatch in {table_name}: "
                f"SQLite={sqlite_count}, PostgreSQL={postgres_count}"
            )
        else:
            logger.info(
                f"✅ {table_name}: {sqlite_count} rows match"
            )
    
    await postgres_engine.dispose()
    sqlite_engine.dispose()
    
    if mismatches:
        logger.error(f"❌ Migration verification failed: {len(mismatches)} mismatches")
        return False
    else:
        logger.info("✅ Migration verification successful!")
        return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python migrate-to-postgres.py <sqlite_url> <postgres_url>")
        print("Example: python migrate-to-postgres.py sqlite:///./dryad.db postgresql+asyncpg://user:pass@localhost/dryad")
        sys.exit(1)
    
    sqlite_url = sys.argv[1]
    postgres_url = sys.argv[2]
    
    # Run migration
    asyncio.run(migrate_data(sqlite_url, postgres_url))
    
    # Verify migration
    success = asyncio.run(verify_migration(sqlite_url, postgres_url))
    
    sys.exit(0 if success else 1)
```

---

### 4. Database Configuration Update

Update `app/core/config.py`:

```python
"""
Database Configuration

Support for both SQLite and PostgreSQL.
"""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./dryad.db"
    )
    
    # PostgreSQL specific settings
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_POOL_RECYCLE: int = 3600
    
    def get_database_url(self) -> str:
        """Get database URL with proper driver."""
        if self.DATABASE_URL.startswith("postgresql://"):
            # Convert to asyncpg driver
            return self.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+asyncpg://"
            )
        return self.DATABASE_URL


settings = Settings()
```

---

### 5. Migration Procedure Documentation

Create `docs/deployment/POSTGRESQL_MIGRATION.md`:

```markdown
# PostgreSQL Migration Guide

## Prerequisites

1. PostgreSQL 15+ installed
2. Database backup created
3. Downtime window scheduled

## Migration Steps

### 1. Backup SQLite Database

```bash
# Create backup
cp dryad.db dryad.db.backup

# Verify backup
sqlite3 dryad.db.backup "SELECT COUNT(*) FROM users;"
```

### 2. Set Up PostgreSQL

```bash
# Start PostgreSQL
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for PostgreSQL to be ready
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

### 3. Run Alembic Migrations

```bash
# Set PostgreSQL URL
export DATABASE_URL="postgresql+asyncpg://dryad_user:password@localhost/dryad"

# Run migrations
alembic upgrade head
```

### 4. Migrate Data

```bash
# Run migration script
python scripts/database/migrate-to-postgres.py \
  "sqlite:///./dryad.db" \
  "postgresql+asyncpg://dryad_user:password@localhost/dryad"
```

### 5. Verify Migration

```bash
# Check row counts
psql -U dryad_user -d dryad -c "SELECT COUNT(*) FROM users;"
sqlite3 dryad.db "SELECT COUNT(*) FROM users;"
```

### 6. Update Application Configuration

```bash
# Update .env file
DATABASE_URL=postgresql+asyncpg://dryad_user:password@localhost/dryad
```

### 7. Restart Application

```bash
# Restart with PostgreSQL
docker-compose -f docker-compose.prod.yml restart gremlins-api
```

## Rollback Procedure

If migration fails:

```bash
# Stop application
docker-compose -f docker-compose.prod.yml stop gremlins-api

# Restore SQLite
cp dryad.db.backup dryad.db

# Update .env
DATABASE_URL=sqlite+aiosqlite:///./dryad.db

# Restart application
docker-compose -f docker-compose.prod.yml start gremlins-api
```

## Performance Tuning

After migration, optimize PostgreSQL:

```sql
-- Analyze tables
ANALYZE;

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- Update statistics
VACUUM ANALYZE;
```
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] PostgreSQL configured
- [ ] Migration scripts created
- [ ] Data migration tested
- [ ] Row counts verified
- [ ] Application working with PostgreSQL
- [ ] Rollback procedure tested
- [ ] Documentation complete

---

## 🧪 TESTING

```bash
# Test PostgreSQL connection
python -c "from app.database.database import engine; import asyncio; asyncio.run(engine.connect())"

# Test migration
python scripts/database/migrate-to-postgres.py \
  "sqlite:///./test.db" \
  "postgresql+asyncpg://test:test@localhost/test"

# Verify data
psql -U dryad_user -d dryad -c "SELECT * FROM users LIMIT 5;"
```

---

## 📝 NOTES

- Test migration in staging first
- Schedule downtime for production migration
- Keep SQLite backup for rollback
- Monitor PostgreSQL performance
- Optimize indexes after migration


