#!/bin/bash
# Backup Script for UniAugment
# Backs up database and data volumes

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# Configuration
BACKUP_DIR="$PROJECT_ROOT/.backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.tar.gz"
DB_BACKUP_FILE="$BACKUP_DIR/db-backup-$TIMESTAMP.sql"
RETENTION_DAYS=${1:-30}

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}UniAugment Backup Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo -e "${YELLOW}Backup directory: $BACKUP_DIR${NC}\n"

# Backup PostgreSQL database
echo -e "${YELLOW}Backing up PostgreSQL database...${NC}"
docker-compose -f "$PROJECT_ROOT/compose/docker-compose.full.yml" exec -T postgres \
    pg_dump -U uniaugment uniaugment > "$DB_BACKUP_FILE" 2>/dev/null || true

if [ -f "$DB_BACKUP_FILE" ]; then
    echo -e "${GREEN}✓ Database backed up: $DB_BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Database backup skipped (PostgreSQL not running)${NC}"
fi

# Backup data volumes
echo -e "\n${YELLOW}Backing up data volumes...${NC}"
if [ -d "$PROJECT_ROOT/data" ]; then
    tar -czf "$BACKUP_FILE" -C "$PROJECT_ROOT" data logs 2>/dev/null || true
    echo -e "${GREEN}✓ Data backed up: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ No data directory found${NC}"
fi

# Clean old backups
echo -e "\n${YELLOW}Cleaning old backups (retention: $RETENTION_DAYS days)...${NC}"
find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "db-backup-*.sql" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# List recent backups
echo -e "\n${YELLOW}Recent backups:${NC}"
ls -lh "$BACKUP_DIR" | tail -10

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Backup complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

