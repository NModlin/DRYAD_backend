#!/bin/bash
# ============================================================================
# Restore Script for DRYAD.AI Backend
# Restore from backup with verification
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
RESTORE_DIR="${RESTORE_DIR:-./restore_temp}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DRYAD.AI Backend - Restore Script                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to list available backups
list_backups() {
    echo -e "${GREEN}Available backups:${NC}"
    echo ""
    
    local backups=($(ls -t "$BACKUP_DIR"/DRYAD.AI_backup_*.tar.gz 2>/dev/null || true))
    
    if [ ${#backups[@]} -eq 0 ]; then
        echo -e "${RED}No backups found in $BACKUP_DIR${NC}"
        exit 1
    fi
    
    local i=1
    for backup in "${backups[@]}"; do
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -c %y "$backup" 2>/dev/null || stat -f %Sm "$backup" 2>/dev/null)
        echo "$i) $(basename $backup) - $size - $date"
        i=$((i + 1))
    done
    
    echo ""
}

# Function to select backup
select_backup() {
    list_backups
    
    echo -n "Select backup number (or 'q' to quit): "
    read selection
    
    if [ "$selection" = "q" ]; then
        echo "Restore cancelled."
        exit 0
    fi
    
    local backups=($(ls -t "$BACKUP_DIR"/DRYAD.AI_backup_*.tar.gz))
    local index=$((selection - 1))
    
    if [ $index -lt 0 ] || [ $index -ge ${#backups[@]} ]; then
        echo -e "${RED}Invalid selection${NC}"
        exit 1
    fi
    
    BACKUP_FILE="${backups[$index]}"
    echo ""
    echo "Selected: $(basename $BACKUP_FILE)"
    echo ""
}

# Function to verify backup
verify_backup() {
    echo -e "${GREEN}1. Verifying backup...${NC}"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}  ❌ Backup file not found: $BACKUP_FILE${NC}"
        exit 1
    fi
    
    # Test extraction
    tar -tzf "$BACKUP_FILE" > /dev/null || {
        echo -e "${RED}  ❌ Backup file is corrupted!${NC}"
        exit 1
    }
    
    echo "  ✅ Backup verified"
}

# Function to extract backup
extract_backup() {
    echo -e "${GREEN}2. Extracting backup...${NC}"
    
    # Create restore directory
    mkdir -p "$RESTORE_DIR"
    
    # Extract backup
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
    
    # Find extracted directory
    EXTRACTED_DIR=$(find "$RESTORE_DIR" -maxdepth 1 -type d -name "DRYAD.AI_backup_*" | head -n 1)
    
    if [ -z "$EXTRACTED_DIR" ]; then
        echo -e "${RED}  ❌ Failed to find extracted backup${NC}"
        exit 1
    fi
    
    echo "  ✅ Backup extracted to: $EXTRACTED_DIR"
}

# Function to show backup manifest
show_manifest() {
    echo -e "${GREEN}3. Backup manifest:${NC}"
    echo ""
    
    if [ -f "$EXTRACTED_DIR/manifest.txt" ]; then
        cat "$EXTRACTED_DIR/manifest.txt"
    else
        echo "  ⚠️  No manifest found"
    fi
    
    echo ""
}

# Function to confirm restore
confirm_restore() {
    echo -e "${YELLOW}⚠️  WARNING: This will overwrite existing data!${NC}"
    echo ""
    echo "Current data will be backed up to: ./pre_restore_backup/"
    echo ""
    echo -n "Are you sure you want to continue? (yes/no): "
    read confirmation
    
    if [ "$confirmation" != "yes" ]; then
        echo "Restore cancelled."
        cleanup
        exit 0
    fi
    
    echo ""
}

# Function to backup current data
backup_current_data() {
    echo -e "${GREEN}4. Backing up current data...${NC}"
    
    local pre_backup_dir="./pre_restore_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$pre_backup_dir"
    
    # Backup current database
    if [ -f "data/DRYAD.AI.db" ]; then
        cp data/DRYAD.AI.db "$pre_backup_dir/"
        echo "  ✅ Current database backed up"
    fi
    
    # Backup current logs
    if [ -d "logs" ]; then
        tar -czf "$pre_backup_dir/logs.tar.gz" logs/
        echo "  ✅ Current logs backed up"
    fi
    
    echo "  ✅ Pre-restore backup complete: $pre_backup_dir"
}

# Function to stop services
stop_services() {
    echo -e "${GREEN}5. Stopping services...${NC}"
    
    docker-compose -f docker-compose.prod.yml down || true
    
    echo "  ✅ Services stopped"
}

# Function to restore database
restore_database() {
    echo -e "${GREEN}6. Restoring database...${NC}"
    
    # Restore SQLite
    if [ -f "$EXTRACTED_DIR/DRYAD.AI.db" ]; then
        mkdir -p data
        cp "$EXTRACTED_DIR/DRYAD.AI.db" data/
        echo "  ✅ SQLite database restored"
    fi
    
    # Restore PostgreSQL
    if [ -f "$EXTRACTED_DIR/postgres_dump.sql" ]; then
        echo "  - Restoring PostgreSQL database..."
        psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            < "$EXTRACTED_DIR/postgres_dump.sql"
        echo "  ✅ PostgreSQL database restored"
    fi
}

# Function to restore files
restore_files() {
    echo -e "${GREEN}7. Restoring files...${NC}"
    
    # Restore logs
    if [ -f "$EXTRACTED_DIR/logs.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/logs.tar.gz"
        echo "  ✅ Logs restored"
    fi
    
    # Restore data directory
    if [ -f "$EXTRACTED_DIR/data.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/data.tar.gz"
        echo "  ✅ Data directory restored"
    fi
    
    # Restore models
    if [ -f "$EXTRACTED_DIR/models.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/models.tar.gz"
        echo "  ✅ Models restored"
    fi
}

# Function to restore configuration
restore_configuration() {
    echo -e "${GREEN}8. Restoring configuration...${NC}"
    
    # Restore environment file
    if [ -f "$EXTRACTED_DIR/.env.production" ]; then
        cp "$EXTRACTED_DIR/.env.production" .
        echo "  ✅ Environment configuration restored"
    fi
    
    # Restore nginx configuration
    if [ -f "$EXTRACTED_DIR/nginx_config.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/nginx_config.tar.gz"
        echo "  ✅ Nginx configuration restored"
    fi
    
    # Restore docker-compose files
    if [ -f "$EXTRACTED_DIR/docker_config.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/docker_config.tar.gz"
        echo "  ✅ Docker configuration restored"
    fi
}

# Function to restore SSL certificates
restore_ssl() {
    echo -e "${GREEN}9. Restoring SSL certificates...${NC}"
    
    if [ -f "$EXTRACTED_DIR/ssl_certs.tar.gz" ]; then
        tar -xzf "$EXTRACTED_DIR/ssl_certs.tar.gz"
        echo "  ✅ SSL certificates restored"
    else
        echo "  ⚠️  No SSL certificates in backup"
    fi
}

# Function to start services
start_services() {
    echo -e "${GREEN}10. Starting services...${NC}"
    
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "  ✅ Services started"
}

# Function to verify restoration
verify_restoration() {
    echo -e "${GREEN}11. Verifying restoration...${NC}"
    
    # Wait for services to start
    echo "  - Waiting for services to start..."
    sleep 15
    
    # Check health endpoint
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            echo "  ✅ Health check passed"
            return 0
        fi
        
        echo "  - Attempt $attempt/$max_attempts failed, retrying..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}  ❌ Health check failed after $max_attempts attempts${NC}"
    return 1
}

# Function to cleanup
cleanup() {
    echo -e "${GREEN}12. Cleaning up...${NC}"
    
    if [ -d "$RESTORE_DIR" ]; then
        rm -rf "$RESTORE_DIR"
        echo "  ✅ Temporary files cleaned up"
    fi
}

# Main restore process
main() {
    local start_time=$(date +%s)
    
    # Select backup if not provided
    if [ -z "${BACKUP_FILE:-}" ]; then
        select_backup
    fi
    
    # Perform restore steps
    verify_backup
    extract_backup
    show_manifest
    confirm_restore
    backup_current_data
    stop_services
    restore_database
    restore_files
    restore_configuration
    restore_ssl
    start_services
    verify_restoration
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Restore Complete                                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Restored from: $(basename $BACKUP_FILE)"
    echo "Duration: ${duration}s"
    echo "Timestamp: $(date)"
    echo ""
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Verify application functionality"
    echo "2. Check logs for any errors"
    echo "3. Test critical features"
    echo "4. Monitor system health"
}

# Error handler
error_handler() {
    echo ""
    echo -e "${RED}❌ Restore failed!${NC}"
    echo "Error occurred at line $1"
    
    # Attempt to restart services
    echo "Attempting to restart services..."
    docker-compose -f docker-compose.prod.yml up -d || true
    
    cleanup
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Run main restore
main

