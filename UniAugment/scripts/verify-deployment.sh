#!/bin/bash

################################################################################
# DRYAD.AI - Deployment Verification Script (Arch Linux)
# 
# This script verifies that the UniAugment deployment is working correctly
# including the Agentic Research University System (Level 6).
#
# Usage: ./verify-deployment.sh [container_name]
# Example: ./verify-deployment.sh uniaugment-api
#
# Author: DRYAD Development Team
# Date: October 23, 2025
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Container name (default or from argument)
CONTAINER_NAME="${1:-uniaugment-api}"
API_BASE_URL="http://localhost:8000"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

################################################################################
# Verification Functions
################################################################################

check_docker_running() {
    print_header "Checking Docker Status"
    
    if docker ps &> /dev/null; then
        print_success "Docker is running"
    else
        print_failure "Docker is not running or not accessible"
        return 1
    fi
}

check_container_running() {
    print_header "Checking Container Status"
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_success "Container '${CONTAINER_NAME}' is running"
        
        # Get container health status
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "none")
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Container health status: healthy"
        elif [ "$HEALTH_STATUS" = "none" ]; then
            print_info "Container has no health check configured"
        else
            print_warning "Container health status: $HEALTH_STATUS"
        fi
    else
        print_failure "Container '${CONTAINER_NAME}' is not running"
        return 1
    fi
}

check_database_connection() {
    print_header "Checking Database Connection"
    
    # Try to execute a simple query inside the container
    if docker exec "${CONTAINER_NAME}" python -c "
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('Database connection successful')
        exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>&1 | grep -q "Database connection successful"; then
        print_success "Database connection successful"
    else
        print_failure "Database connection failed"
        return 1
    fi
}

check_migration_status() {
    print_header "Checking Migration Status"
    
    # Check if all migrations are applied
    MIGRATION_OUTPUT=$(docker exec "${CONTAINER_NAME}" python -m alembic current 2>&1 || echo "ERROR")
    
    if echo "$MIGRATION_OUTPUT" | grep -q "ERROR"; then
        print_failure "Failed to check migration status"
        return 1
    fi
    
    # Check for specific migrations
    EXPECTED_MIGRATIONS=(
        "001_initial_schema"
        "002_add_agent_creation_studio"
        "003_add_visual_customization"
        "004_add_behavioral_customization"
        "005_add_specializations"
        "006_add_progression_paths"
        "007_add_universities"
        "008_add_curriculum_system"
        "009_add_competition_system"
    )
    
    MIGRATIONS_APPLIED=0
    for migration in "${EXPECTED_MIGRATIONS[@]}"; do
        if echo "$MIGRATION_OUTPUT" | grep -q "$migration"; then
            ((MIGRATIONS_APPLIED++))
        fi
    done
    
    if [ $MIGRATIONS_APPLIED -gt 0 ]; then
        print_success "Migrations applied: $MIGRATIONS_APPLIED found"
        print_info "Current migration: $(echo "$MIGRATION_OUTPUT" | head -n 1)"
    else
        print_warning "Could not verify specific migrations, but alembic is working"
    fi
}

check_api_health() {
    print_header "Checking API Health"
    
    # Check root endpoint
    if curl -s -f "${API_BASE_URL}/" > /dev/null 2>&1; then
        print_success "API root endpoint is accessible"
    else
        print_failure "API root endpoint is not accessible"
        return 1
    fi
    
    # Check health endpoint if it exists
    if curl -s -f "${API_BASE_URL}/health" > /dev/null 2>&1; then
        print_success "API health endpoint is accessible"
    else
        print_info "API health endpoint not found (optional)"
    fi
    
    # Check docs endpoint
    if curl -s -f "${API_BASE_URL}/docs" > /dev/null 2>&1; then
        print_success "API documentation is accessible at ${API_BASE_URL}/docs"
    else
        print_warning "API documentation endpoint not accessible"
    fi
}

check_agent_studio_endpoints() {
    print_header "Checking Agent Creation Studio Endpoints"
    
    # Phase 1 endpoints (7 endpoints)
    PHASE1_ENDPOINTS=(
        "/api/v1/agents/visual-config"
        "/api/v1/agents/behavioral-config"
    )
    
    # Phase 2 endpoints (sample)
    PHASE2_ENDPOINTS=(
        "/api/v1/specializations"
        "/api/v1/skill-trees"
    )
    
    ENDPOINT_COUNT=0
    for endpoint in "${PHASE1_ENDPOINTS[@]}" "${PHASE2_ENDPOINTS[@]}"; do
        if curl -s -f "${API_BASE_URL}${endpoint}" > /dev/null 2>&1 || \
           curl -s "${API_BASE_URL}${endpoint}" 2>&1 | grep -q "405\|422"; then
            ((ENDPOINT_COUNT++))
        fi
    done
    
    if [ $ENDPOINT_COUNT -gt 0 ]; then
        print_success "Agent Studio endpoints accessible ($ENDPOINT_COUNT tested)"
    else
        print_warning "Could not verify Agent Studio endpoints"
    fi
}

check_university_endpoints() {
    print_header "Checking Agentic University System Endpoints"
    
    # University endpoints (sample)
    UNIVERSITY_ENDPOINTS=(
        "/api/v1/universities/"
        "/api/v1/curriculum/paths"
        "/api/v1/competitions/"
    )
    
    ENDPOINT_COUNT=0
    for endpoint in "${UNIVERSITY_ENDPOINTS[@]}"; do
        # Check if endpoint exists (200, 405, or 422 are all valid responses)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE_URL}${endpoint}" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ] || [ "$HTTP_CODE" = "422" ]; then
            ((ENDPOINT_COUNT++))
        fi
    done
    
    if [ $ENDPOINT_COUNT -eq ${#UNIVERSITY_ENDPOINTS[@]} ]; then
        print_success "All University System endpoints accessible (${ENDPOINT_COUNT}/${#UNIVERSITY_ENDPOINTS[@]})"
    elif [ $ENDPOINT_COUNT -gt 0 ]; then
        print_warning "Some University System endpoints accessible (${ENDPOINT_COUNT}/${#UNIVERSITY_ENDPOINTS[@]})"
    else
        print_failure "University System endpoints not accessible"
        return 1
    fi
}

check_configuration() {
    print_header "Checking Configuration"
    
    # Check if .env file exists
    if [ -f ".env" ] || [ -f ".env.distributed" ]; then
        print_success "Environment configuration file found"
    else
        print_warning "No .env or .env.distributed file found"
    fi
    
    # Check university system configuration
    if docker exec "${CONTAINER_NAME}" python -c "
import os
university_enabled = os.getenv('AGENTIC_UNIVERSITY_ENABLED', 'false').lower() == 'true'
if university_enabled:
    print('University System: ENABLED')
else:
    print('University System: DISABLED')
" 2>&1 | grep -q "ENABLED"; then
        print_success "University System is ENABLED"
    else
        print_info "University System is DISABLED (can be enabled in configuration)"
    fi
}

check_database_tables() {
    print_header "Checking Database Tables"
    
    # Check if university tables exist
    TABLES_CHECK=$(docker exec "${CONTAINER_NAME}" python -c "
from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
university_tables = ['universities', 'curriculum_paths', 'curriculum_levels', 
                     'agent_curriculum_progress', 'competitions', 'competition_rounds',
                     'leaderboards', 'leaderboard_rankings']
found_tables = [t for t in university_tables if t in tables]
print(f'{len(found_tables)}/{len(university_tables)}')
" 2>&1 || echo "0/8")
    
    if echo "$TABLES_CHECK" | grep -q "8/8"; then
        print_success "All University System tables exist (8/8)"
    elif echo "$TABLES_CHECK" | grep -q "[1-7]/8"; then
        print_warning "Some University System tables exist ($TABLES_CHECK)"
    else
        print_info "University System tables not found (migrations may not be applied)"
    fi
}

generate_report() {
    print_header "Verification Summary"
    
    echo -e "Total Checks: ${TOTAL_CHECKS}"
    echo -e "${GREEN}Passed: ${PASSED_CHECKS}${NC}"
    echo -e "${RED}Failed: ${FAILED_CHECKS}${NC}"
    
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "\nPass Rate: ${PASS_RATE}%"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL CHECKS PASSED! Deployment is healthy.${NC}"
        return 0
    elif [ $PASS_RATE -ge 80 ]; then
        echo -e "\n${YELLOW}⚠️  MOSTLY HEALTHY: Some checks failed but deployment is mostly functional.${NC}"
        return 0
    else
        echo -e "\n${RED}❌ DEPLOYMENT ISSUES DETECTED: Multiple checks failed.${NC}"
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║        DRYAD.AI - Deployment Verification Script              ║"
    echo "║        Agentic Research University System                     ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    print_info "Container: ${CONTAINER_NAME}"
    print_info "API URL: ${API_BASE_URL}"
    echo ""
    
    # Run all checks
    check_docker_running || true
    check_container_running || true
    check_database_connection || true
    check_migration_status || true
    check_api_health || true
    check_agent_studio_endpoints || true
    check_university_endpoints || true
    check_configuration || true
    check_database_tables || true
    
    # Generate final report
    generate_report
}

# Run main function
main "$@"

