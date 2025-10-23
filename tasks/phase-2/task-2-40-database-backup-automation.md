# Task 2-40: Database Backup Automation

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** HIGH  
**Estimated Hours:** 4 hours

---

## 📋 OVERVIEW

Implement automated database backup system with scheduled backups, retention policies, backup verification, and restore procedures.

---

## 🎯 OBJECTIVES

1. Create automated backup scripts
2. Configure backup schedule
3. Implement retention policy
4. Add backup verification
5. Create restore procedures
6. Test backup/restore process

---

## 📊 CURRENT STATE

**Existing:**
- Manual backup procedures
- No automation
- No retention policy

**Gaps:**
- No automated backups
- No backup verification
- No retention management
- Risk of data loss

---

## 🔧 IMPLEMENTATION

### 1. Backup Script

Create `scripts/database/backup-database.sh`:

```bash
#!/bin/bash
#
# Database Backup Script
#
# Automated database backup with compression and retention

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATABASE_URL="${DATABASE_URL}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse database type from URL
if [[ $DATABASE_URL == postgresql* ]]; then
    DB_TYPE="postgresql"
    BACKUP_FILE="${BACKUP_DIR}/postgres_backup_${TIMESTAMP}.sql.gz"
elif [[ $DATABASE_URL == sqlite* ]]; then
    DB_TYPE="sqlite"
    BACKUP_FILE="${BACKUP_DIR}/sqlite_backup_${TIMESTAMP}.db.gz"
else
    echo "❌ Unsupported database type"
    exit 1
fi

echo "🔄 Starting database backup..."
echo "  Type: ${DB_TYPE}"
echo "  File: ${BACKUP_FILE}"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Perform backup based on database type
if [ "$DB_TYPE" = "postgresql" ]; then
    # PostgreSQL backup
    PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        -d ${POSTGRES_DB:-dryad} \
        --format=plain \
        --no-owner \
        --no-acl \
        | gzip > ${BACKUP_FILE}
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    # SQLite backup
    DB_PATH=$(echo $DATABASE_URL | sed 's/sqlite.*:\/\///')
    sqlite3 ${DB_PATH} ".backup /tmp/backup.db"
    gzip -c /tmp/backup.db > ${BACKUP_FILE}
    rm /tmp/backup.db
fi

# Verify backup
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "✅ Backup created: ${BACKUP_SIZE}"
else
    echo "❌ Backup failed"
    exit 1
fi

# Clean up old backups
echo "🧹 Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
find ${BACKUP_DIR} -name "*backup_*.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(find ${BACKUP_DIR} -name "*backup_*.gz" | wc -l)
echo "  Remaining backups: ${REMAINING}"

# Create backup metadata
cat > ${BACKUP_DIR}/latest_backup.json <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "file": "${BACKUP_FILE}",
  "size": "${BACKUP_SIZE}",
  "database_type": "${DB_TYPE}",
  "retention_days": ${RETENTION_DAYS}
}
EOF

echo "✅ Backup complete!"
```

---

### 2. Restore Script

Create `scripts/database/restore-database.sh`:

```bash
#!/bin/bash
#
# Database Restore Script
#
# Restore database from backup

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /app/backups/postgres_backup_20250120_120000.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will replace the current database!"
echo "  Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Determine database type from filename
if [[ $BACKUP_FILE == *postgres* ]]; then
    DB_TYPE="postgresql"
elif [[ $BACKUP_FILE == *sqlite* ]]; then
    DB_TYPE="sqlite"
else
    echo "❌ Cannot determine database type from filename"
    exit 1
fi

echo "🔄 Starting database restore..."

if [ "$DB_TYPE" = "postgresql" ]; then
    # PostgreSQL restore
    echo "  Dropping existing database..."
    PGPASSWORD=${POSTGRES_PASSWORD} dropdb \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        --if-exists ${POSTGRES_DB:-dryad}
    
    echo "  Creating new database..."
    PGPASSWORD=${POSTGRES_PASSWORD} createdb \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        ${POSTGRES_DB:-dryad}
    
    echo "  Restoring data..."
    gunzip -c ${BACKUP_FILE} | PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        -d ${POSTGRES_DB:-dryad}
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    # SQLite restore
    DB_PATH=$(echo $DATABASE_URL | sed 's/sqlite.*:\/\///')
    
    echo "  Backing up current database..."
    cp ${DB_PATH} ${DB_PATH}.pre-restore
    
    echo "  Restoring data..."
    gunzip -c ${BACKUP_FILE} > ${DB_PATH}
fi

echo "✅ Restore complete!"
```

---

### 3. Backup Verification Script

Create `scripts/database/verify-backup.py`:

```python
#!/usr/bin/env python3
"""
Backup Verification Script

Verify backup integrity and completeness.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from datetime import datetime


def verify_backup(backup_file: str) -> bool:
    """
    Verify backup file integrity.
    
    Args:
        backup_file: Path to backup file
    
    Returns:
        True if valid, False otherwise
    """
    backup_path = Path(backup_file)
    
    print(f"🔍 Verifying backup: {backup_file}")
    
    # Check file exists
    if not backup_path.exists():
        print("❌ Backup file not found")
        return False
    
    # Check file size
    size_mb = backup_path.stat().st_size / 1024 / 1024
    print(f"  Size: {size_mb:.2f} MB")
    
    if size_mb < 0.01:
        print("❌ Backup file too small (< 10 KB)")
        return False
    
    # Verify gzip integrity
    try:
        with gzip.open(backup_path, 'rb') as f:
            # Read first 1KB to verify
            f.read(1024)
        print("  ✅ Gzip integrity OK")
    except Exception as e:
        print(f"❌ Gzip integrity check failed: {e}")
        return False
    
    # Check age
    age_hours = (datetime.now().timestamp() - backup_path.stat().st_mtime) / 3600
    print(f"  Age: {age_hours:.1f} hours")
    
    if age_hours > 48:
        print("⚠️  Backup is older than 48 hours")
    
    print("✅ Backup verification passed")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify-backup.py <backup_file>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    success = verify_backup(backup_file)
    
    sys.exit(0 if success else 1)
```

---

### 4. Cron Schedule

Create `docker/cron/database-backup`:

```cron
# Database Backup Schedule

# Daily backup at 2 AM
0 2 * * * /app/scripts/database/backup-database.sh >> /var/log/backup.log 2>&1

# Weekly verification on Sundays at 3 AM
0 3 * * 0 /app/scripts/database/verify-backup.py /app/backups/latest_backup.json >> /var/log/backup-verify.log 2>&1
```

---

### 5. Backup Monitoring

Create `app/api/v1/endpoints/backup.py`:

```python
"""
Backup Monitoring Endpoints

Monitor backup status and history.
"""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

BACKUP_DIR = Path("/app/backups")


class BackupInfo(BaseModel):
    """Backup information."""
    timestamp: str
    file: str
    size: str
    database_type: str
    age_hours: float


@router.get("/backup/latest", response_model=BackupInfo)
async def get_latest_backup():
    """Get latest backup information."""
    metadata_file = BACKUP_DIR / "latest_backup.json"
    
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="No backup found")
    
    with open(metadata_file) as f:
        data = json.load(f)
    
    # Calculate age
    backup_time = datetime.strptime(data["timestamp"], "%Y%m%d_%H%M%S")
    age_hours = (datetime.now() - backup_time).total_seconds() / 3600
    
    return BackupInfo(**data, age_hours=age_hours)


@router.get("/backup/list")
async def list_backups():
    """List all available backups."""
    if not BACKUP_DIR.exists():
        return {"backups": []}
    
    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("*backup_*.gz"), reverse=True):
        backups.append({
            "file": backup_file.name,
            "size": f"{backup_file.stat().st_size / 1024 / 1024:.2f} MB",
            "created": datetime.fromtimestamp(
                backup_file.stat().st_mtime
            ).isoformat()
        })
    
    return {"backups": backups[:10]}  # Last 10 backups
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Backup script created
- [ ] Restore script created
- [ ] Backup schedule configured
- [ ] Retention policy implemented
- [ ] Backup verification working
- [ ] Monitoring endpoints working
- [ ] Documentation complete

---

## 🧪 TESTING

```bash
# Test backup
./scripts/database/backup-database.sh

# Verify backup
python scripts/database/verify-backup.py /app/backups/latest_backup.json

# Test restore (in staging)
./scripts/database/restore-database.sh /app/backups/postgres_backup_20250120_120000.sql.gz

# Check backup API
curl http://localhost:8000/api/v1/backup/latest
```

---

## 📝 NOTES

- Run backups during low-traffic periods
- Store backups in separate location
- Test restore procedures regularly
- Monitor backup success/failure
- Keep multiple backup copies


