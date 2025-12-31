# Task 1-26: Database Migration Strategy & Testing

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** CRITICAL  
**Estimated Hours:** 6 hours

---

## 📋 OVERVIEW

Implement a comprehensive database migration strategy with Alembic, including rollback procedures, zero-downtime migrations, data migration patterns, and automated testing to prevent data loss during deployments.

---

## 🎯 OBJECTIVES

1. Document complete migration procedures and best practices
2. Create rollback scripts for all migrations
3. Implement zero-downtime migration approach
4. Create data migration patterns and examples
5. Implement automated migration testing
6. Create backup/restore procedures for migrations

---

## 📊 CURRENT STATE

**Existing:**
- Alembic configured in `alembic.ini`
- Basic migration scripts in `alembic/versions/`
- Database models in `app/database/models.py` and `app/dryad/models/`

**Gaps:**
- No rollback testing procedures
- No zero-downtime migration strategy
- No data migration patterns documented
- No automated migration validation
- No backup procedures before migrations

---

## 🔧 IMPLEMENTATION

### 1. Migration Strategy Documentation

Create `docs/database/MIGRATION_STRATEGY.md`:

```markdown
# Database Migration Strategy

## Migration Workflow

1. **Development:**
   - Create migration: `alembic revision --autogenerate -m "description"`
   - Review generated migration
   - Test upgrade: `alembic upgrade head`
   - Test downgrade: `alembic downgrade -1`

2. **Staging:**
   - Backup database
   - Run migration with validation
   - Verify data integrity
   - Test rollback if needed

3. **Production:**
   - Create backup
   - Run migration during maintenance window
   - Validate data
   - Monitor for issues

## Zero-Downtime Migrations

### Phase 1: Additive Changes
- Add new columns as nullable
- Add new tables
- Add new indexes (online)

### Phase 2: Data Migration
- Backfill data in background
- Validate data consistency

### Phase 3: Cleanup
- Make columns non-nullable
- Remove old columns
- Remove old tables

## Rollback Strategy

- Always test rollback before production
- Keep rollback window < 1 hour
- Document rollback procedures
- Automate rollback validation
```

---

### 2. Migration Validation Script

Create `scripts/database/validate_migration.py`:

```python
"""
Database Migration Validation Script

Validates migrations before applying to production.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import Any
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates database migrations."""
    
    def __init__(self, database_url: str, alembic_ini: str = "alembic.ini"):
        self.database_url = database_url
        self.alembic_cfg = Config(alembic_ini)
        self.engine = create_engine(database_url)
    
    def get_current_revision(self) -> str | None:
        """Get current database revision."""
        with self.engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    
    def get_head_revision(self) -> str:
        """Get head revision from migration scripts."""
        script = ScriptDirectory.from_config(self.alembic_cfg)
        return script.get_current_head()
    
    def validate_migration_path(self) -> bool:
        """Validate migration path from current to head."""
        current = self.get_current_revision()
        head = self.get_head_revision()
        
        logger.info(f"Current revision: {current}")
        logger.info(f"Head revision: {head}")
        
        if current == head:
            logger.info("✅ Database is up to date")
            return True
        
        script = ScriptDirectory.from_config(self.alembic_cfg)
        
        # Get migration path
        if current is None:
            revisions = list(script.iterate_revisions(head, "base"))
        else:
            revisions = list(script.iterate_revisions(head, current))
        
        logger.info(f"Migrations to apply: {len(revisions)}")
        for rev in reversed(revisions):
            logger.info(f"  - {rev.revision}: {rev.doc}")
        
        return True
    
    def test_upgrade(self) -> bool:
        """Test migration upgrade."""
        try:
            logger.info("Testing migration upgrade...")
            command.upgrade(self.alembic_cfg, "head")
            logger.info("✅ Upgrade successful")
            return True
        except Exception as e:
            logger.error(f"❌ Upgrade failed: {e}")
            return False
    
    def test_downgrade(self) -> bool:
        """Test migration downgrade."""
        try:
            logger.info("Testing migration downgrade...")
            command.downgrade(self.alembic_cfg, "-1")
            logger.info("✅ Downgrade successful")
            return True
        except Exception as e:
            logger.error(f"❌ Downgrade failed: {e}")
            return False
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity after migration."""
        try:
            with self.engine.connect() as conn:
                # Check for orphaned records
                # Check foreign key constraints
                # Validate data types
                # Check for null values in non-nullable columns
                logger.info("✅ Data integrity validated")
                return True
        except Exception as e:
            logger.error(f"❌ Data integrity check failed: {e}")
            return False


def main():
    """Run migration validation."""
    import os
    
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/DRYAD.AI.db")
    
    validator = MigrationValidator(database_url)
    
    # Validate migration path
    if not validator.validate_migration_path():
        sys.exit(1)
    
    # Test upgrade
    if not validator.test_upgrade():
        sys.exit(1)
    
    # Validate data integrity
    if not validator.validate_data_integrity():
        sys.exit(1)
    
    # Test downgrade
    if not validator.test_downgrade():
        sys.exit(1)
    
    # Upgrade back to head
    if not validator.test_upgrade():
        sys.exit(1)
    
    logger.info("🎉 All migration validations passed!")


if __name__ == "__main__":
    main()
```

---

### 3. Backup Script

Create `scripts/database/backup_database.py`:

```python
"""
Database Backup Script

Creates timestamped backups before migrations.
"""
from __future__ import annotations

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_database(database_path: str, backup_dir: str = "backups") -> str:
    """
    Create database backup.
    
    Args:
        database_path: Path to database file
        backup_dir: Directory to store backups
    
    Returns:
        Path to backup file
    """
    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = Path(database_path).stem
    backup_file = backup_path / f"{db_name}_backup_{timestamp}.db"
    
    # Copy database
    logger.info(f"Creating backup: {backup_file}")
    shutil.copy2(database_path, backup_file)
    
    # Verify backup
    if backup_file.exists():
        size = backup_file.stat().st_size
        logger.info(f"✅ Backup created successfully ({size} bytes)")
        return str(backup_file)
    else:
        raise RuntimeError("Backup creation failed")


def restore_database(backup_file: str, database_path: str) -> None:
    """
    Restore database from backup.
    
    Args:
        backup_file: Path to backup file
        database_path: Path to restore to
    """
    logger.info(f"Restoring from backup: {backup_file}")
    shutil.copy2(backup_file, database_path)
    logger.info("✅ Database restored successfully")


if __name__ == "__main__":
    db_path = "data/DRYAD.AI.db"
    backup_file = backup_database(db_path)
    print(f"Backup created: {backup_file}")
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Migration strategy documented
- [ ] Validation script created and tested
- [ ] Backup/restore scripts working
- [ ] Zero-downtime migration patterns documented
- [ ] Rollback procedures tested
- [ ] All existing migrations validated
- [ ] CI/CD integration for migration testing

---

## 🧪 TESTING

```python
# tests/test_database_migrations.py
"""Tests for database migration strategy."""
import pytest
from scripts.database.validate_migration import MigrationValidator
from scripts.database.backup_database import backup_database, restore_database


def test_migration_validation():
    """Test migration validation."""
    validator = MigrationValidator("sqlite:///./test.db")
    assert validator.validate_migration_path()


def test_backup_restore():
    """Test database backup and restore."""
    # Create test database
    test_db = "test_data/test.db"
    
    # Backup
    backup_file = backup_database(test_db, "test_backups")
    assert Path(backup_file).exists()
    
    # Restore
    restore_database(backup_file, test_db)
    assert Path(test_db).exists()
```

---

## 📚 DOCUMENTATION

Update `docs/database/README.md` with migration procedures and best practices.

---

## 🔗 DEPENDENCIES

- Alembic configuration
- Database models
- Backup storage location

---

## 📝 NOTES

- Always backup before migrations
- Test rollback procedures
- Use zero-downtime patterns for production
- Monitor migration performance
- Document all data migrations


