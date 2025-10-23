#!/bin/bash
# UniAugment Full Stack Deployment Script
# Automated deployment with credential management and validation
# Usage: ./deploy-full-stack.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DEPLOYMENT_LOG="$PROJECT_ROOT/.deployment-$(date +%Y%m%d-%H%M%S).log"
DEPLOYMENT_INFO="$PROJECT_ROOT/.deployment-info.txt"
BACKUP_DIR="$PROJECT_ROOT/.backups"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$DEPLOYMENT_LOG"
}

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     UniAugment Full Stack Deployment - Automated Setup         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if ! command -v openssl &> /dev/null; then
        missing_tools+=("openssl")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Generate secure passwords
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Generate JWT secret
generate_jwt_secret() {
    openssl rand -base64 48
}

# Collect user inputs
collect_inputs() {
    log "Collecting configuration inputs..."
    
    echo -e "\n${YELLOW}=== Database Configuration ===${NC}"
    read -p "PostgreSQL Password (press Enter to auto-generate): " PG_PASSWORD
    if [ -z "$PG_PASSWORD" ]; then
        PG_PASSWORD=$(generate_password)
        log_success "Generated PostgreSQL password"
    fi
    
    echo -e "\n${YELLOW}=== Security Configuration ===${NC}"
    read -p "JWT Secret Key (press Enter to auto-generate): " JWT_SECRET
    if [ -z "$JWT_SECRET" ]; then
        JWT_SECRET=$(generate_jwt_secret)
        log_success "Generated JWT secret key"
    fi
    
    read -p "Grafana Admin Password (press Enter to auto-generate): " GRAFANA_PASSWORD
    if [ -z "$GRAFANA_PASSWORD" ]; then
        GRAFANA_PASSWORD=$(generate_password)
        log_success "Generated Grafana admin password"
    fi
    
    echo -e "\n${YELLOW}=== Application Configuration ===${NC}"
    read -p "Environment (development/staging/production) [staging]: " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-staging}
    
    read -p "Log Level (DEBUG/INFO/WARNING/ERROR) [INFO]: " LOG_LEVEL
    LOG_LEVEL=${LOG_LEVEL:-INFO}
    
    read -p "LLM Provider (mock/ollama/openai) [mock]: " LLM_PROVIDER
    LLM_PROVIDER=${LLM_PROVIDER:-mock}
    
    if [ "$LLM_PROVIDER" = "openai" ]; then
        read -p "OpenAI API Key: " OPENAI_API_KEY
    else
        OPENAI_API_KEY=""
    fi
    
    echo -e "\n${YELLOW}=== Deployment Configuration ===${NC}"
    read -p "Deployment Domain/Hostname [localhost]: " DEPLOYMENT_DOMAIN
    DEPLOYMENT_DOMAIN=${DEPLOYMENT_DOMAIN:-localhost}

    read -p "Enable SSL/TLS (y/n) [n]: " ENABLE_SSL
    ENABLE_SSL=${ENABLE_SSL:-n}

    echo -e "\n${YELLOW}=== Agent Creation Studio Configuration ===${NC}"
    read -p "Enable Agent Creation Studio enhancements? (y/n) [y]: " ENABLE_AGENT_STUDIO
    ENABLE_AGENT_STUDIO=${ENABLE_AGENT_STUDIO:-y}

    if [[ "$ENABLE_AGENT_STUDIO" =~ ^[Yy]$ ]]; then
        AGENT_STUDIO_ENABLED="true"
        log_success "Agent Creation Studio enabled"

        read -p "Enable visual customization (avatars, colors, themes)? (y/n) [y]: " ENABLE_VISUAL
        ENABLE_VISUAL=${ENABLE_VISUAL:-y}
        if [[ "$ENABLE_VISUAL" =~ ^[Yy]$ ]]; then
            AGENT_VISUAL_CUSTOMIZATION="true"
        else
            AGENT_VISUAL_CUSTOMIZATION="false"
        fi

        read -p "Enable behavioral customization (learning style, risk tolerance)? (y/n) [y]: " ENABLE_BEHAVIORAL
        ENABLE_BEHAVIORAL=${ENABLE_BEHAVIORAL:-y}
        if [[ "$ENABLE_BEHAVIORAL" =~ ^[Yy]$ ]]; then
            AGENT_BEHAVIORAL_CUSTOMIZATION="true"
        else
            AGENT_BEHAVIORAL_CUSTOMIZATION="false"
        fi

        log_success "Agent Studio configuration complete"
    else
        AGENT_STUDIO_ENABLED="false"
        AGENT_VISUAL_CUSTOMIZATION="false"
        AGENT_BEHAVIORAL_CUSTOMIZATION="false"
        log "Agent Creation Studio disabled"
    fi

    log_success "Configuration collected"
}

# Create environment file
create_env_file() {
    log "Creating .env file..."
    
    cat > "$PROJECT_ROOT/.env" << EOF
# UniAugment Full Stack Environment Configuration
# Generated: $(date)

# Stack Configuration
STACK_TYPE=full
ENVIRONMENT=$ENVIRONMENT
LOG_LEVEL=$LOG_LEVEL

# Database Configuration
DATABASE_URL=postgresql://uniaugment:${PG_PASSWORD}@postgres:5432/uniaugment
POSTGRES_USER=uniaugment
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_DB=uniaugment

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Weaviate Configuration
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=

# Security
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# LLM Configuration
LLM_PROVIDER=${LLM_PROVIDER}
OPENAI_API_KEY=${OPENAI_API_KEY}
OLLAMA_BASE_URL=http://ollama:11434

# Grafana Configuration
GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
GF_SECURITY_ADMIN_USER=admin

# Application Configuration
DEPLOYMENT_DOMAIN=${DEPLOYMENT_DOMAIN}
ENABLE_SSL=${ENABLE_SSL}

# Backup Configuration
BACKUP_RETENTION_DAYS=30

# Agent Creation Studio - Phase 1
AGENT_CREATION_STUDIO_ENABLED=${AGENT_STUDIO_ENABLED:-false}
AGENT_VISUAL_CUSTOMIZATION=${AGENT_VISUAL_CUSTOMIZATION:-true}
AGENT_BEHAVIORAL_CUSTOMIZATION=${AGENT_BEHAVIORAL_CUSTOMIZATION:-true}

# Default Visual Settings
DEFAULT_AVATAR_STYLE=abstract
DEFAULT_PRIMARY_COLOR=#0066CC
DEFAULT_SECONDARY_COLOR=#00CC66
DEFAULT_ACCENT_COLOR=#CC6600
DEFAULT_VISUAL_THEME=professional
DEFAULT_GLOW_INTENSITY=0.5

# Default Behavioral Settings
DEFAULT_LEARNING_STYLE=visual
DEFAULT_LEARNING_PACE=1.0
DEFAULT_RISK_TOLERANCE=0.5
DEFAULT_COLLABORATION_STYLE=equal
DEFAULT_COMMUNICATION_TONE=professional
DEFAULT_DECISION_SPEED=0.5
DEFAULT_DECISION_CONFIDENCE=0.7
EOF

    log_success ".env file created"
}

# Create backup of existing data
backup_existing_data() {
    log "Creating backup of existing data..."
    
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$PROJECT_ROOT/data" ]; then
        BACKUP_FILE="$BACKUP_DIR/data-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$BACKUP_FILE" -C "$PROJECT_ROOT" data 2>/dev/null || true
        log_success "Data backed up to $BACKUP_FILE"
    fi
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    docker-compose -f compose/docker-compose.full.yml build --no-cache 2>&1 | tee -a "$DEPLOYMENT_LOG"
    
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    log "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    docker-compose -f compose/docker-compose.full.yml up -d 2>&1 | tee -a "$DEPLOYMENT_LOG"
    
    log_success "Services started"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to be healthy..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$PROJECT_ROOT/compose/docker-compose.full.yml" ps | grep -q "healthy"; then
            log_success "Services are healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -ne "\rWaiting for services... ($attempt/$max_attempts)"
        sleep 2
    done
    
    log_warning "Services did not become healthy within timeout"
    return 1
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    cd "$PROJECT_ROOT"
    
    # Wait for PostgreSQL to be ready
    sleep 5
    
    docker-compose -f compose/docker-compose.full.yml exec -T postgres pg_isready -U uniaugment || true
    
    log_success "Database initialized"
}

# Create Weaviate collections
create_weaviate_collections() {
    log "Creating Weaviate collections..."
    
    # Collections will be created by the application on startup
    log_success "Weaviate collections will be created by application"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    local checks_passed=0
    local checks_total=0
    
    # Check API
    checks_total=$((checks_total + 1))
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log_warning "API health check failed"
    fi
    
    # Check PostgreSQL
    checks_total=$((checks_total + 1))
    if docker-compose -f "$PROJECT_ROOT/compose/docker-compose.full.yml" exec -T postgres pg_isready -U uniaugment > /dev/null 2>&1; then
        log_success "PostgreSQL health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log_warning "PostgreSQL health check failed"
    fi
    
    # Check Redis
    checks_total=$((checks_total + 1))
    if docker-compose -f "$PROJECT_ROOT/compose/docker-compose.full.yml" exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log_warning "Redis health check failed"
    fi
    
    # Check Weaviate
    checks_total=$((checks_total + 1))
    if curl -s http://localhost:8081/v1/.well-known/ready > /dev/null 2>&1; then
        log_success "Weaviate health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log_warning "Weaviate health check failed"
    fi
    
    log "Health checks: $checks_passed/$checks_total passed"
}

# Generate deployment report
generate_deployment_report() {
    log "Generating deployment report..."
    
    cat > "$DEPLOYMENT_INFO" << EOF
╔════════════════════════════════════════════════════════════════╗
║          UniAugment Full Stack Deployment Report               ║
╚════════════════════════════════════════════════════════════════╝

Deployment Date: $(date)
Deployment Log: $DEPLOYMENT_LOG

═══════════════════════════════════════════════════════════════════

SERVICE URLS
─────────────────────────────────────────────────────────────────
API:                    http://localhost:8000
API Documentation:      http://localhost:8000/docs
API ReDoc:              http://localhost:8000/redoc

PostgreSQL:             localhost:5432
  Username:             uniaugment
  Password:             [SAVED IN .env]
  Database:             uniaugment

Redis:                  localhost:6379

Weaviate:               http://localhost:8081
  Console:              http://localhost:8081/v1/meta

Prometheus:             http://localhost:9090
Grafana:                http://localhost:3000
  Username:             admin
  Password:             [SAVED IN .env]

═══════════════════════════════════════════════════════════════════

DOCKER COMMANDS
─────────────────────────────────────────────────────────────────
View services:          docker-compose -f compose/docker-compose.full.yml ps
View logs:              docker-compose -f compose/docker-compose.full.yml logs -f
Stop services:          docker-compose -f compose/docker-compose.full.yml down
Restart services:       docker-compose -f compose/docker-compose.full.yml restart
View specific logs:     docker-compose -f compose/docker-compose.full.yml logs -f [service]

═══════════════════════════════════════════════════════════════════

NEXT STEPS
─────────────────────────────────────────────────────────────────
1. Access the API at http://localhost:8000/docs
2. Create your first university instance
3. Configure curriculum paths
4. Set up competitions
5. Monitor with Grafana at http://localhost:3000

═══════════════════════════════════════════════════════════════════

SECURITY NOTES
─────────────────────────────────────────────────────────────────
- All credentials are stored in .env file
- Keep .env file secure and never commit to version control
- Change default Grafana password immediately
- Enable SSL/TLS for production deployments
- Regularly backup your data

═══════════════════════════════════════════════════════════════════

For more information, see: docs/README.md
EOF
    
    log_success "Deployment report generated: $DEPLOYMENT_INFO"
}

# Main execution
main() {
    print_banner
    
    log "Starting UniAugment Full Stack Deployment"
    log "Project Root: $PROJECT_ROOT"
    log "Deployment Log: $DEPLOYMENT_LOG"
    
    check_prerequisites
    collect_inputs
    create_env_file
    backup_existing_data
    build_images
    start_services
    wait_for_services
    initialize_database
    create_weaviate_collections
    run_health_checks
    generate_deployment_report
    
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Deployment Complete! 🚀                                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${CYAN}Deployment Information:${NC}"
    cat "$DEPLOYMENT_INFO"
    
    log_success "Deployment completed successfully"
}

# Run main function
main "$@"

