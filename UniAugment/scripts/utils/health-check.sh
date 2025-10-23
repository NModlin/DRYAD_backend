#!/bin/bash
# Health Check Script for UniAugment Services
# Checks the health of all running services

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

# Determine which compose file to use
COMPOSE_FILE="${1:-compose/docker-compose.full.yml}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}UniAugment Health Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Function to check service
check_service() {
    local service=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Checking $service... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "$expected_code" ]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠ WARNING${NC} (HTTP $response, expected $expected_code)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        return 1
    fi
}

# Function to check container
check_container() {
    local container=$1
    
    echo -n "Checking container $container... "
    
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Check containers
echo -e "${YELLOW}Container Status:${NC}"
check_container "uniaugment-api" || true
check_container "uniaugment-postgres" || true
check_container "uniaugment-redis" || true
check_container "uniaugment-weaviate" || true
check_container "uniaugment-celery-worker" || true
check_container "uniaugment-prometheus" || true
check_container "uniaugment-grafana" || true

echo ""
echo -e "${YELLOW}Service Health:${NC}"

# Check API
check_service "API" "http://localhost:8000/health" "200" || true

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
if docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T postgres pg_isready -U uniaugment > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Check Redis
echo -n "Checking Redis... "
if docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Check Weaviate
check_service "Weaviate" "http://localhost:8081/v1/.well-known/ready" "200" || true

# Check Prometheus
check_service "Prometheus" "http://localhost:9090/-/healthy" "200" || true

# Check Grafana
check_service "Grafana" "http://localhost:3000/api/health" "200" || true

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Health check complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

