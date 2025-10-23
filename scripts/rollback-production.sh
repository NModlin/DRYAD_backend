#!/bin/bash
# ============================================================================
# Production Rollback Script for DRYAD.AI Backend
# Automated rollback to previous version
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ROLLBACK_VERSION="${1:-}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
BACKUP_BEFORE_ROLLBACK="${BACKUP_BEFORE_ROLLBACK:-true}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DRYAD.AI Backend - Production Rollback                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${RED}⚠️  WARNING: This will rollback the production deployment${NC}"
echo ""

# Function to send notification
send_notification() {
    local title=$1
    local message=$2
    local color=$3
    
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"title\":\"$title\",\"text\":\"$message\",\"themeColor\":\"$color\"}" \
            2>/dev/null || true
    fi
}

# Function to list recent versions
list_recent_versions() {
    echo -e "${GREEN}Recent versions:${NC}"
    echo ""
    git tag -l --sort=-version:refname | head -5
    echo ""
    echo "Current version: $(git describe --tags 2>/dev/null || git rev-parse --short HEAD)"
    echo ""
}

# Function to select rollback version
select_rollback_version() {
    if [ -z "$ROLLBACK_VERSION" ]; then
        list_recent_versions
        
        echo -n "Enter version to rollback to (or 'q' to quit): "
        read ROLLBACK_VERSION
        
        if [ "$ROLLBACK_VERSION" = "q" ]; then
            echo "Rollback cancelled."
            exit 0
        fi
    fi
    
    # Verify version exists
    if ! git rev-parse "$ROLLBACK_VERSION" > /dev/null 2>&1; then
        echo -e "${RED}❌ Version not found: $ROLLBACK_VERSION${NC}"
        exit 1
    fi
    
    echo ""
    echo "Rollback version: $ROLLBACK_VERSION"
    echo ""
}

# Function to confirm rollback
confirm_rollback() {
    echo -e "${YELLOW}⚠️  This will rollback to version: $ROLLBACK_VERSION${NC}"
    echo ""
    echo -n "Are you sure you want to continue? (yes/no): "
    read confirmation
    
    if [ "$confirmation" != "yes" ]; then
        echo "Rollback cancelled."
        exit 0
    fi
    
    echo ""
}

# Function to create incident log
create_incident_log() {
    echo -e "${GREEN}1. Creating incident log...${NC}"
    
    local log_file="incidents/rollback_$(date +%Y%m%d_%H%M%S).md"
    mkdir -p incidents
    
    cat > "$log_file" << EOF
# Rollback Incident

**Date**: $(date)
**From Version**: $(git describe --tags 2>/dev/null || git rev-parse --short HEAD)
**To Version**: $ROLLBACK_VERSION
**Rolled Back By**: $(whoami)
**Reason**: [TO BE FILLED]

## Timeline
- $(date +%H:%M) - Rollback initiated

## Actions Taken
- Creating incident log
- Backing up current state
- Rolling back code
- Rolling back database
- Restarting services

## Status
In Progress...
EOF
    
    echo -e "${GREEN}  ✅ Incident log created: $log_file${NC}"
    echo ""
    echo "Please update the incident log with the reason for rollback:"
    echo "  nano $log_file"
    echo ""
}

# Function to backup current state
backup_current_state() {
    if [ "$BACKUP_BEFORE_ROLLBACK" = "true" ]; then
        echo -e "${GREEN}2. Backing up current state...${NC}"
        
        # Save current logs
        docker-compose -f docker-compose.prod.yml logs > "logs/pre_rollback_$(date +%Y%m%d_%H%M%S).log" 2>&1 || true
        
        # Create backup
        ./scripts/backup.sh || {
            echo -e "${YELLOW}  ⚠️  Backup failed, continuing anyway${NC}"
        }
        
        echo -e "${GREEN}  ✅ Current state backed up${NC}"
    else
        echo -e "${YELLOW}2. Skipping backup (BACKUP_BEFORE_ROLLBACK=false)${NC}"
    fi
}

# Function to stop services
stop_services() {
    echo -e "${GREEN}3. Stopping services...${NC}"
    
    docker-compose -f docker-compose.prod.yml down || {
        echo -e "${YELLOW}  ⚠️  Some services may not have stopped cleanly${NC}"
    }
    
    echo -e "${GREEN}  ✅ Services stopped${NC}"
}

# Function to rollback code
rollback_code() {
    echo -e "${GREEN}4. Rolling back code...${NC}"
    
    # Checkout rollback version
    git checkout "$ROLLBACK_VERSION" || {
        echo -e "${RED}  ❌ Failed to checkout version${NC}"
        exit 1
    }
    
    # Verify version
    current_version=$(git describe --tags 2>/dev/null || git rev-parse --short HEAD)
    echo -e "${GREEN}  ✅ Code rolled back to: $current_version${NC}"
}

# Function to rollback database
rollback_database() {
    echo -e "${GREEN}5. Rolling back database...${NC}"
    
    # Check if database migrations need to be rolled back
    echo -n "  Do you need to rollback database migrations? (yes/no): "
    read rollback_db
    
    if [ "$rollback_db" = "yes" ]; then
        echo "  How many migrations to rollback? (enter number or 'all'): "
        read migration_count
        
        if [ "$migration_count" = "all" ]; then
            # Restore from backup
            echo "  Restoring database from backup..."
            ./scripts/restore.sh || {
                echo -e "${RED}  ❌ Database restore failed${NC}"
                exit 1
            }
        else
            # Downgrade migrations
            for i in $(seq 1 $migration_count); do
                docker-compose -f docker-compose.prod.yml run --rm backend alembic downgrade -1 || {
                    echo -e "${RED}  ❌ Migration rollback failed${NC}"
                    exit 1
                }
            done
        fi
        
        echo -e "${GREEN}  ✅ Database rolled back${NC}"
    else
        echo -e "${YELLOW}  ⏭️  Skipping database rollback${NC}"
    fi
}

# Function to rebuild images
rebuild_images() {
    echo -e "${GREEN}6. Rebuilding Docker images...${NC}"
    
    docker-compose -f docker-compose.prod.yml build || {
        echo -e "${RED}  ❌ Image build failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}  ✅ Images rebuilt${NC}"
}

# Function to start services
start_services() {
    echo -e "${GREEN}7. Starting services...${NC}"
    
    docker-compose -f docker-compose.prod.yml up -d || {
        echo -e "${RED}  ❌ Failed to start services${NC}"
        exit 1
    }
    
    echo -e "${GREEN}  ✅ Services started${NC}"
}

# Function to wait for services
wait_for_services() {
    echo -e "${GREEN}8. Waiting for services to start...${NC}"
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            echo -e "${GREEN}  ✅ Services are healthy${NC}"
            return 0
        fi
        
        echo "  Attempt $attempt/$max_attempts..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}  ❌ Services failed to start${NC}"
    return 1
}

# Function to verify rollback
verify_rollback() {
    echo -e "${GREEN}9. Verifying rollback...${NC}"
    
    # Check version
    current_version=$(git describe --tags 2>/dev/null || git rev-parse --short HEAD)
    if [ "$current_version" != "$ROLLBACK_VERSION" ]; then
        echo -e "${RED}  ❌ Version mismatch${NC}"
        return 1
    fi
    
    # Check health
    if ! curl -f http://localhost/health > /dev/null 2>&1; then
        echo -e "${RED}  ❌ Health check failed${NC}"
        return 1
    fi
    
    # Check containers
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${RED}  ❌ Some containers are not running${NC}"
        return 1
    fi
    
    echo -e "${GREEN}  ✅ Rollback verified${NC}"
}

# Function to monitor system
monitor_system() {
    echo -e "${GREEN}10. Monitoring system...${NC}"
    echo ""
    echo "Monitoring for 2 minutes. Press Ctrl+C to stop."
    echo ""
    
    for i in {1..24}; do
        # Check health
        if curl -f http://localhost/health > /dev/null 2>&1; then
            echo -e "${GREEN}  ✅ Health check $i/24 passed${NC}"
        else
            echo -e "${RED}  ❌ Health check $i/24 failed${NC}"
        fi
        
        sleep 5
    done
    
    echo ""
    echo -e "${GREEN}  ✅ System stable${NC}"
}

# Main rollback process
main() {
    local start_time=$(date +%s)
    
    # Send start notification
    send_notification "🔄 Rollback Started" "Rolling back DRYAD.AI to $ROLLBACK_VERSION" "FFA500"
    
    # Run rollback steps
    select_rollback_version
    confirm_rollback
    create_incident_log
    backup_current_state
    stop_services
    rollback_code
    rollback_database
    rebuild_images
    start_services
    wait_for_services
    verify_rollback
    monitor_system
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Rollback Complete                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Rolled back to: $ROLLBACK_VERSION"
    echo "Duration: ${duration}s"
    echo "Timestamp: $(date)"
    echo ""
    echo -e "${GREEN}✅ Rollback completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Continue monitoring system health"
    echo "2. Update incident log with details"
    echo "3. Investigate root cause of issue"
    echo "4. Plan fix for next deployment"
    
    # Send success notification
    send_notification "✅ Rollback Complete" "DRYAD.AI rolled back to $ROLLBACK_VERSION in ${duration}s" "28A745"
}

# Error handler
error_handler() {
    echo ""
    echo -e "${RED}❌ Rollback failed!${NC}"
    echo "Error occurred at line $1"
    
    # Send failure notification
    send_notification "❌ Rollback Failed" "DRYAD.AI rollback failed at line $1" "DC3545"
    
    echo ""
    echo "Manual intervention required!"
    echo "Contact on-call engineer immediately."
    
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Run main rollback
main

