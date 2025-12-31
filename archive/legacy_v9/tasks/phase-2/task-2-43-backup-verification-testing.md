# Task 2-43: Backup Verification Testing

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** HIGH  
**Estimated Hours:** 3 hours

---

## 📋 OVERVIEW

Implement automated backup verification and restore testing to ensure backups are valid and can be successfully restored in disaster recovery scenarios.

---

## 🎯 OBJECTIVES

1. Create backup verification scripts
2. Implement automated restore testing
3. Verify data integrity after restore
4. Test disaster recovery procedures
5. Document verification process
6. Schedule regular verification tests

---

## 📊 CURRENT STATE

**Existing:**
- Automated backups configured
- Manual restore procedures

**Gaps:**
- No automated verification
- No restore testing
- No data integrity checks
- Unknown backup reliability

---

## 🔧 IMPLEMENTATION

### 1. Backup Verification Script

Create `scripts/database/verify-backup-restore.sh`:

```bash
#!/bin/bash
#
# Backup Restore Verification
#
# Tests backup restore process

set -e

BACKUP_FILE=$1
TEST_DB="dryad_test_restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "🔍 Verifying backup restore: $BACKUP_FILE"

# Determine database type
if [[ $BACKUP_FILE == *postgres* ]]; then
    DB_TYPE="postgresql"
elif [[ $BACKUP_FILE == *sqlite* ]]; then
    DB_TYPE="sqlite"
else
    echo "❌ Unknown database type"
    exit 1
fi

if [ "$DB_TYPE" = "postgresql" ]; then
    echo "📦 Testing PostgreSQL restore..."
    
    # Drop test database if exists
    PGPASSWORD=${POSTGRES_PASSWORD} dropdb \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        --if-exists ${TEST_DB}
    
    # Create test database
    PGPASSWORD=${POSTGRES_PASSWORD} createdb \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        ${TEST_DB}
    
    # Restore backup
    gunzip -c ${BACKUP_FILE} | PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        -d ${TEST_DB} \
        > /dev/null 2>&1
    
    # Verify tables exist
    TABLE_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        -d ${TEST_DB} \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
    
    echo "  Tables restored: ${TABLE_COUNT}"
    
    # Verify data
    USER_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        -d ${TEST_DB} \
        -t -c "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
    
    echo "  Users restored: ${USER_COUNT}"
    
    # Cleanup
    PGPASSWORD=${POSTGRES_PASSWORD} dropdb \
        -h ${POSTGRES_HOST:-localhost} \
        -U ${POSTGRES_USER:-dryad_user} \
        ${TEST_DB}
    
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "📦 Testing SQLite restore..."
    
    # Extract to test file
    TEST_FILE="/tmp/${TEST_DB}.db"
    gunzip -c ${BACKUP_FILE} > ${TEST_FILE}
    
    # Verify database integrity
    sqlite3 ${TEST_FILE} "PRAGMA integrity_check;" | grep -q "ok"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Database integrity OK"
    else
        echo "  ❌ Database integrity check failed"
        rm ${TEST_FILE}
        exit 1
    fi
    
    # Verify tables
    TABLE_COUNT=$(sqlite3 ${TEST_FILE} "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
    echo "  Tables restored: ${TABLE_COUNT}"
    
    # Verify data
    USER_COUNT=$(sqlite3 ${TEST_FILE} "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo "  Users restored: ${USER_COUNT}"
    
    # Cleanup
    rm ${TEST_FILE}
fi

echo "✅ Backup verification successful!"
```

---

### 2. Data Integrity Verification

Create `scripts/database/verify-data-integrity.py`:

```python
#!/usr/bin/env python3
"""
Data Integrity Verification

Verify data integrity after restore.
"""
from __future__ import annotations

import asyncio
import sys
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import User, Conversation, Message, Document


async def verify_data_integrity(database_url: str) -> bool:
    """
    Verify data integrity.
    
    Args:
        database_url: Database URL
    
    Returns:
        True if valid, False otherwise
    """
    print("🔍 Verifying data integrity...\n")
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    checks_passed = 0
    checks_failed = 0
    
    async with async_session() as session:
        # Check 1: User count
        result = await session.execute(select(func.count(User.id)))
        user_count = result.scalar()
        print(f"✓ Users: {user_count}")
        checks_passed += 1
        
        # Check 2: Conversations have valid user_id
        result = await session.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id.is_(None))
        )
        invalid_conversations = result.scalar()
        if invalid_conversations > 0:
            print(f"✗ Invalid conversations: {invalid_conversations}")
            checks_failed += 1
        else:
            print(f"✓ All conversations have valid user_id")
            checks_passed += 1
        
        # Check 3: Messages have valid conversation_id
        result = await session.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id.is_(None))
        )
        invalid_messages = result.scalar()
        if invalid_messages > 0:
            print(f"✗ Invalid messages: {invalid_messages}")
            checks_failed += 1
        else:
            print(f"✓ All messages have valid conversation_id")
            checks_passed += 1
        
        # Check 4: Documents have valid user_id
        result = await session.execute(
            select(func.count(Document.id))
            .where(Document.user_id.is_(None))
        )
        invalid_documents = result.scalar()
        if invalid_documents > 0:
            print(f"✗ Invalid documents: {invalid_documents}")
            checks_failed += 1
        else:
            print(f"✓ All documents have valid user_id")
            checks_passed += 1
    
    await engine.dispose()
    
    print(f"\n📊 Results: {checks_passed} passed, {checks_failed} failed")
    
    return checks_failed == 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify-data-integrity.py <database_url>")
        sys.exit(1)
    
    database_url = sys.argv[1]
    success = asyncio.run(verify_data_integrity(database_url))
    
    sys.exit(0 if success else 1)
```

---

### 3. Automated Verification Schedule

Create `scripts/database/scheduled-backup-verification.sh`:

```bash
#!/bin/bash
#
# Scheduled Backup Verification
#
# Runs weekly backup verification

set -e

BACKUP_DIR="/app/backups"
LOG_FILE="/var/log/backup-verification.log"

echo "🔍 Starting scheduled backup verification..." | tee -a ${LOG_FILE}
echo "Date: $(date)" | tee -a ${LOG_FILE}

# Find latest backup
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/*backup_*.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found" | tee -a ${LOG_FILE}
    exit 1
fi

echo "Testing backup: ${LATEST_BACKUP}" | tee -a ${LOG_FILE}

# Run verification
./scripts/database/verify-backup-restore.sh ${LATEST_BACKUP} 2>&1 | tee -a ${LOG_FILE}

if [ $? -eq 0 ]; then
    echo "✅ Backup verification successful" | tee -a ${LOG_FILE}
    
    # Send success notification
    curl -X POST ${WEBHOOK_URL} \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"✅ Backup verification successful: ${LATEST_BACKUP}\"}"
else
    echo "❌ Backup verification failed" | tee -a ${LOG_FILE}
    
    # Send failure notification
    curl -X POST ${WEBHOOK_URL} \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"❌ Backup verification FAILED: ${LATEST_BACKUP}\"}"
    
    exit 1
fi
```

---

### 4. Disaster Recovery Test

Create `scripts/database/disaster-recovery-test.sh`:

```bash
#!/bin/bash
#
# Disaster Recovery Test
#
# Full disaster recovery simulation

set -e

echo "🚨 DISASTER RECOVERY TEST"
echo "========================="
echo ""
echo "This will:"
echo "1. Create a test backup"
echo "2. Simulate database loss"
echo "3. Restore from backup"
echo "4. Verify data integrity"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Test cancelled"
    exit 0
fi

# Step 1: Create backup
echo ""
echo "Step 1: Creating backup..."
./scripts/database/backup-database.sh

BACKUP_FILE=$(cat /app/backups/latest_backup.json | jq -r '.file')
echo "Backup created: ${BACKUP_FILE}"

# Step 2: Verify backup
echo ""
echo "Step 2: Verifying backup..."
./scripts/database/verify-backup-restore.sh ${BACKUP_FILE}

# Step 3: Test restore
echo ""
echo "Step 3: Testing restore process..."
./scripts/database/restore-database.sh ${BACKUP_FILE}

# Step 4: Verify data integrity
echo ""
echo "Step 4: Verifying data integrity..."
python scripts/database/verify-data-integrity.py ${DATABASE_URL}

echo ""
echo "✅ DISASTER RECOVERY TEST COMPLETE"
echo "All steps passed successfully!"
```

---

### 5. Verification Monitoring

Create `app/api/v1/endpoints/backup_verification.py`:

```python
"""
Backup Verification Endpoints

Monitor backup verification status.
"""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

LOG_FILE = Path("/var/log/backup-verification.log")


class VerificationStatus(BaseModel):
    """Verification status response."""
    last_verification: str | None
    status: str
    backup_file: str | None


@router.get("/backup/verification", response_model=VerificationStatus)
async def get_verification_status():
    """Get last backup verification status."""
    if not LOG_FILE.exists():
        return VerificationStatus(
            last_verification=None,
            status="never_run",
            backup_file=None
        )
    
    # Read last 100 lines
    with open(LOG_FILE) as f:
        lines = f.readlines()[-100:]
    
    # Find last verification
    last_date = None
    last_status = "unknown"
    last_backup = None
    
    for line in reversed(lines):
        if "Date:" in line:
            last_date = line.split("Date:")[1].strip()
        if "✅ Backup verification successful" in line:
            last_status = "success"
            break
        if "❌ Backup verification failed" in line:
            last_status = "failed"
            break
        if "Testing backup:" in line:
            last_backup = line.split("Testing backup:")[1].strip()
    
    return VerificationStatus(
        last_verification=last_date,
        status=last_status,
        backup_file=last_backup
    )
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Backup verification script created
- [ ] Restore testing automated
- [ ] Data integrity checks implemented
- [ ] Disaster recovery test working
- [ ] Verification scheduled
- [ ] Monitoring endpoints working
- [ ] Documentation complete

---

## 🧪 TESTING

```bash
# Test backup verification
./scripts/database/verify-backup-restore.sh /app/backups/latest_backup.gz

# Test data integrity
python scripts/database/verify-data-integrity.py $DATABASE_URL

# Run disaster recovery test
./scripts/database/disaster-recovery-test.sh

# Check verification status
curl http://localhost:8000/api/v1/backup/verification
```

---

## 📝 NOTES

- Run verification weekly
- Test disaster recovery quarterly
- Monitor verification failures
- Document recovery procedures
- Keep verification logs


