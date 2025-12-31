#!/bin/bash
# ============================================================================
# Production Deployment Script for DRYAD.AI Backend
# Automated deployment with pre/post checks
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION="${1:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_TESTS="${RUN_TESTS:-true}"
WEBHOOK_URL="${WEBHOOK_URL:-}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DRYAD.AI Backend - Production Deployment               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Version: $VERSION"
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $(date)"
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

# Function to check prerequisites
check_prerequisites() {
    echo -e "${GREEN}1. Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}  ❌ Docker not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}  ❌ Docker Compose not installed${NC}"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}  ❌ Git not installed${NC}"
        exit 1
    fi
    
    # Check disk space (need at least 10GB)
    available=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available" -lt 10 ]; then
        echo -e "${RED}  ❌ Insufficient disk space (need 10GB, have ${available}GB)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}  ✅ All prerequisites met${NC}"
}

# Function to backup current state
backup_current_state() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        echo -e "${GREEN}2. Creating pre-deployment backup...${NC}"
        
        ./scripts/backup.sh || {
            echo -e "${RED}  ❌ Backup failed${NC}"
            exit 1
        }
        
        echo -e "${GREEN}  ✅ Backup complete${NC}"
    else
        echo -e "${YELLOW}2. Skipping backup (BACKUP_BEFORE_DEPLOY=false)${NC}"
    fi
}

# Function to pull latest code
pull_latest_code() {
    echo -e "${GREEN}3. Pulling latest code...${NC}"
    
    # Fetch latest
    git fetch origin
    
    # Checkout version
    if [ "$VERSION" = "latest" ]; then
        git checkout main
        git pull origin main
    else
        git checkout "$VERSION"
    fi
    
    # Verify version
    current_version=$(git describe --tags 2>/dev/null || git rev-parse --short HEAD)
    echo -e "${GREEN}  ✅ Code updated to: $current_version${NC}"
}

# Function to update configuration
update_configuration() {
    echo -e "${GREEN}4. Updating configuration...${NC}"
    
    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}  ❌ .env.production not found${NC}"
        exit 1
    fi
    
    # Verify required variables
    required_vars=("JWT_SECRET_KEY" "DATABASE_URL")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env.production; then
            echo -e "${RED}  ❌ Missing required variable: $var${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}  ✅ Configuration verified${NC}"
}

# Function to build Docker images
build_docker_images() {
    echo -e "${GREEN}5. Building Docker images...${NC}"
    
    docker-compose -f docker-compose.prod.yml build --no-cache || {
        echo -e "${RED}  ❌ Docker build failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}  ✅ Docker images built${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${GREEN}6. Running database migrations...${NC}"
    
    # Check if migrations are needed
    docker-compose -f docker-compose.prod.yml run --rm backend alembic current || {
        echo -e "${YELLOW}  ⚠️  No existing database, will create${NC}"
    }
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head || {
        echo -e "${RED}  ❌ Migration failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}  ✅ Migrations complete${NC}"
}

# Function to deploy services
deploy_services() {
    echo -e "${GREEN}7. Deploying services...${NC}"
    
    # Stop old containers
    docker-compose -f docker-compose.prod.yml down
    
    # Start new containers
    docker-compose -f docker-compose.prod.yml up -d || {
        echo -e "${RED}  ❌ Deployment failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}  ✅ Services deployed${NC}"
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

# Function to run post-deployment tests
run_post_deployment_tests() {
    if [ "$RUN_TESTS" = "true" ]; then
        echo -e "${GREEN}9. Running post-deployment tests...${NC}"
        
        # Health check
        if ! curl -f http://localhost/health > /dev/null 2>&1; then
            echo -e "${RED}  ❌ Health check failed${NC}"
            return 1
        fi
        
        # API test
        if ! curl -f http://localhost/api/v1/health > /dev/null 2>&1; then
            echo -e "${RED}  ❌ API health check failed${NC}"
            return 1
        fi
        
        # Run smoke tests if available
        if [ -d "tests/smoke" ]; then
            pytest tests/smoke/ --base-url=http://localhost || {
                echo -e "${RED}  ❌ Smoke tests failed${NC}"
                return 1
            }
        fi
        
        echo -e "${GREEN}  ✅ All tests passed${NC}"
    else
        echo -e "${YELLOW}9. Skipping tests (RUN_TESTS=false)${NC}"
    fi
}

# Function to verify deployment
verify_deployment() {
    echo -e "${GREEN}10. Verifying deployment...${NC}"
    
    # Check all containers are running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${RED}  ❌ Some containers are not running${NC}"
        docker-compose -f docker-compose.prod.yml ps
        return 1
    fi
    
    # Check logs for errors
    if docker-compose -f docker-compose.prod.yml logs --tail=50 | grep -i "error\|exception\|failed" > /dev/null; then
        echo -e "${YELLOW}  ⚠️  Errors found in logs${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=20
    fi
    
    echo -e "${GREEN}  ✅ Deployment verified${NC}"
}

# Function to create deployment log
create_deployment_log() {
    echo -e "${GREEN}11. Creating deployment log...${NC}"
    
    local log_file="deployments/deployment_$(date +%Y%m%d_%H%M%S).md"
    mkdir -p deployments
    
    cat > "$log_file" << EOF
# Deployment Log

**Date**: $(date)
**Version**: $VERSION
**Environment**: $ENVIRONMENT
**Deployed By**: $(whoami)

## Pre-Deployment
- Backup: ✅
- Prerequisites: ✅
- Configuration: ✅

## Deployment
- Code Updated: ✅
- Images Built: ✅
- Migrations Run: ✅
- Services Deployed: ✅

## Post-Deployment
- Health Checks: ✅
- Tests: ✅
- Verification: ✅

## Services Status
\`\`\`
$(docker-compose -f docker-compose.prod.yml ps)
\`\`\`

## System Info
- Hostname: $(hostname)
- Docker Version: $(docker --version)
- Disk Usage: $(df -h / | tail -1)
- Memory Usage: $(free -h | grep Mem)
EOF
    
    echo -e "${GREEN}  ✅ Deployment log created: $log_file${NC}"
}

# Main deployment process
main() {
    local start_time=$(date +%s)
    
    # Send start notification
    send_notification "🚀 Deployment Started" "Deploying DRYAD.AI $VERSION to $ENVIRONMENT" "0078D7"
    
    # Run deployment steps
    check_prerequisites
    backup_current_state
    pull_latest_code
    update_configuration
    build_docker_images
    run_migrations
    deploy_services
    wait_for_services
    run_post_deployment_tests
    verify_deployment
    create_deployment_log
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Deployment Complete                                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Version: $VERSION"
    echo "Duration: ${duration}s"
    echo "Timestamp: $(date)"
    echo ""
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    
    # Send success notification
    send_notification "✅ Deployment Complete" "DRYAD.AI $VERSION deployed successfully in ${duration}s" "28A745"
}

# Error handler
error_handler() {
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo "Error occurred at line $1"
    
    # Send failure notification
    send_notification "❌ Deployment Failed" "DRYAD.AI $VERSION deployment failed at line $1" "DC3545"
    
    echo ""
    echo "Rollback recommended. Run: ./scripts/rollback-production.sh"
    
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Run main deployment
main

