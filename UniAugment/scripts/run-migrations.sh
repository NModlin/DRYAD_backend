#!/bin/bash
################################################################################
# UniAugment - Database Migration Runner
# Runs Alembic migrations inside the API container
# Usage: ./run-migrations.sh [container_name]
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default container name
CONTAINER_NAME="${1:-uniaugment-api}"

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_container_running() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Container '$CONTAINER_NAME' is not running"
        print_info "Available containers:"
        docker ps --format "  - {{.Names}}"
        exit 1
    fi
    print_success "Container '$CONTAINER_NAME' is running"
}

wait_for_database() {
    print_info "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec "$CONTAINER_NAME" python -c "
import os
import sys
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            print_success "Database is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_warning "Database not ready after ${max_attempts} attempts"
    return 1
}

run_migrations() {
    print_header "Running Database Migrations"
    
    print_info "Executing: alembic upgrade head"
    
    if docker exec "$CONTAINER_NAME" alembic upgrade head; then
        print_success "Migrations completed successfully"
        return 0
    else
        print_error "Migration failed"
        return 1
    fi
}

show_migration_status() {
    print_header "Migration Status"
    
    print_info "Current database revision:"
    docker exec "$CONTAINER_NAME" alembic current || true
    
    echo ""
    print_info "Migration history:"
    docker exec "$CONTAINER_NAME" alembic history --verbose || true
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "UniAugment Database Migration Runner"
    
    # Check if container is running
    check_container_running
    
    # Wait for database
    if ! wait_for_database; then
        print_error "Database is not ready. Please check your database service."
        exit 1
    fi
    
    # Run migrations
    if run_migrations; then
        echo ""
        show_migration_status
        echo ""
        print_success "Migration process complete!"
    else
        print_error "Migration process failed!"
        exit 1
    fi
}

main "$@"

