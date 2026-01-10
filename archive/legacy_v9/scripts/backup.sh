#!/bin/bash
# ============================================================================
# Backup Script for DRYAD.AI Backend
# Automated backup of database, files, and configuration
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="DRYAD.AI_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Notification
WEBHOOK_URL="${WEBHOOK_URL:-}"
EMAIL_TO="${EMAIL_TO:-}"

# S3 Configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_ENABLED="${S3_ENABLED:-false}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DRYAD.AI Backend - Backup Script                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Backup name: $BACKUP_NAME"
echo "Backup path: $BACKUP_PATH"
echo "Timestamp: $(date)"
echo ""

# Create backup directory
mkdir -p "$BACKUP_PATH"

# Function to send notification
send_notification() {
    local message=$1
    local status=$2
    
    echo -e "${GREEN}📧 Sending notification...${NC}"
    
    # Webhook notification
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$message\",\"status\":\"$status\"}" \
            2>/dev/null || true
    fi
    
    # Email notification
    if [ -n "$EMAIL_TO" ]; then
        echo "$message" | mail -s "DRYAD.AI Backup $status" "$EMAIL_TO" || true
    fi
}

# Function to backup database
backup_database() {
    echo -e "${GREEN}1. Backing up database...${NC}"
    
    # SQLite backup
    if [ -f "data/DRYAD.AI.db" ]; then
        echo "  - Backing up SQLite database..."
        sqlite3 data/DRYAD.AI.db ".backup '${BACKUP_PATH}/DRYAD.AI.db'"
        echo "  ✅ SQLite backup complete"
    fi
    
    # PostgreSQL backup (if used)
    if [ -n "${POSTGRES_HOST:-}" ]; then
        echo "  - Backing up PostgreSQL database..."
        pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            > "${BACKUP_PATH}/postgres_dump.sql"
        echo "  ✅ PostgreSQL backup complete"
    fi
}

# Function to backup application files
backup_files() {
    echo -e "${GREEN}2. Backing up application files...${NC}"
    
    # Backup logs
    if [ -d "logs" ]; then
        echo "  - Backing up logs..."
        tar -czf "${BACKUP_PATH}/logs.tar.gz" logs/
        echo "  ✅ Logs backup complete"
    fi
    
    # Backup data directory
    if [ -d "data" ]; then
        echo "  - Backing up data directory..."
        tar -czf "${BACKUP_PATH}/data.tar.gz" data/ --exclude='*.db'
        echo "  ✅ Data backup complete"
    fi
    
    # Backup models
    if [ -d "models" ]; then
        echo "  - Backing up models..."
        tar -czf "${BACKUP_PATH}/models.tar.gz" models/
        echo "  ✅ Models backup complete"
    fi
}

# Function to backup configuration
backup_configuration() {
    echo -e "${GREEN}3. Backing up configuration...${NC}"
    
    # Backup environment files
    echo "  - Backing up environment configuration..."
    if [ -f ".env.production" ]; then
        cp .env.production "${BACKUP_PATH}/.env.production"
    fi
    
    # Backup nginx configuration
    if [ -d "nginx" ]; then
        echo "  - Backing up nginx configuration..."
        tar -czf "${BACKUP_PATH}/nginx_config.tar.gz" nginx/
    fi
    
    # Backup docker-compose files
    echo "  - Backing up docker-compose files..."
    tar -czf "${BACKUP_PATH}/docker_config.tar.gz" docker-compose*.yml
    
    echo "  ✅ Configuration backup complete"
}

# Function to backup SSL certificates
backup_ssl() {
    echo -e "${GREEN}4. Backing up SSL certificates...${NC}"
    
    if [ -d "nginx/ssl" ]; then
        echo "  - Backing up SSL certificates..."
        tar -czf "${BACKUP_PATH}/ssl_certs.tar.gz" nginx/ssl/
        echo "  ✅ SSL certificates backup complete"
    else
        echo "  ⚠️  No SSL certificates found"
    fi
}

# Function to create backup manifest
create_manifest() {
    echo -e "${GREEN}5. Creating backup manifest...${NC}"
    
    cat > "${BACKUP_PATH}/manifest.txt" << EOF
DRYAD.AI Backup Manifest
==========================

Backup Name: $BACKUP_NAME
Timestamp: $(date)
Hostname: $(hostname)
User: $(whoami)

Files Included:
$(ls -lh "$BACKUP_PATH")

Checksums:
$(cd "$BACKUP_PATH" && sha256sum * 2>/dev/null || true)

System Information:
- OS: $(uname -s)
- Kernel: $(uname -r)
- Docker Version: $(docker --version 2>/dev/null || echo "Not installed")

Database Size:
$(du -sh data/DRYAD.AI.db 2>/dev/null || echo "N/A")

Total Backup Size:
$(du -sh "$BACKUP_PATH")
EOF
    
    echo "  ✅ Manifest created"
}

# Function to compress backup
compress_backup() {
    echo -e "${GREEN}6. Compressing backup...${NC}"
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    # Remove uncompressed directory
    rm -rf "$BACKUP_NAME"
    
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    
    echo "  ✅ Backup compressed: $BACKUP_SIZE"
}

# Function to upload to S3
upload_to_s3() {
    if [ "$S3_ENABLED" = "true" ] && [ -n "$S3_BUCKET" ]; then
        echo -e "${GREEN}7. Uploading to S3...${NC}"
        
        aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/backups/" || {
            echo -e "${RED}  ❌ S3 upload failed${NC}"
            return 1
        }
        
        echo "  ✅ Uploaded to S3: s3://${S3_BUCKET}/backups/${BACKUP_NAME}.tar.gz"
    else
        echo -e "${YELLOW}7. S3 upload skipped (not configured)${NC}"
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo -e "${GREEN}8. Cleaning up old backups...${NC}"
    
    # Find and delete backups older than retention period
    find "$BACKUP_DIR" -name "DRYAD.AI_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    deleted_count=$(find "$BACKUP_DIR" -name "DRYAD.AI_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS | wc -l)
    
    echo "  ✅ Deleted $deleted_count old backups (older than $RETENTION_DAYS days)"
}

# Function to verify backup
verify_backup() {
    echo -e "${GREEN}9. Verifying backup...${NC}"
    
    # Check if backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}  ❌ Backup file not found!${NC}"
        return 1
    fi
    
    # Check if backup is not empty
    if [ ! -s "$BACKUP_FILE" ]; then
        echo -e "${RED}  ❌ Backup file is empty!${NC}"
        return 1
    fi
    
    # Test extraction
    echo "  - Testing backup extraction..."
    tar -tzf "$BACKUP_FILE" > /dev/null || {
        echo -e "${RED}  ❌ Backup file is corrupted!${NC}"
        return 1
    }
    
    echo "  ✅ Backup verified successfully"
}

# Main backup process
main() {
    local start_time=$(date +%s)
    
    echo -e "${BLUE}Starting backup process...${NC}"
    echo ""
    
    # Perform backup steps
    backup_database
    backup_files
    backup_configuration
    backup_ssl
    create_manifest
    compress_backup
    upload_to_s3
    cleanup_old_backups
    verify_backup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Backup Complete                                          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Backup file: $BACKUP_FILE"
    echo "Backup size: $BACKUP_SIZE"
    echo "Duration: ${duration}s"
    echo "Timestamp: $(date)"
    echo ""
    
    # Send success notification
    send_notification "Backup completed successfully: $BACKUP_NAME ($BACKUP_SIZE)" "SUCCESS"
    
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
}

# Error handler
error_handler() {
    echo ""
    echo -e "${RED}❌ Backup failed!${NC}"
    echo "Error occurred at line $1"
    
    # Send failure notification
    send_notification "Backup failed at line $1" "FAILED"
    
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Run main backup
main

