#!/bin/bash
set -e

# DRYAD.AI Production Deployment Script
# Deploys the self-contained AI system with proper resource allocation and monitoring

echo "🚀 DRYAD.AI Production Deployment"
echo "=================================="

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
PROJECT_NAME="DRYAD.AI-production"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check system resources
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt 8 ]; then
        warn "System has less than 8GB RAM. AI performance may be limited."
    fi
    
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 4 ]; then
        warn "System has less than 4 CPU cores. AI performance may be limited."
    fi
    
    log "✅ Prerequisites check completed"
    log "   RAM: ${TOTAL_RAM}GB"
    log "   CPU Cores: ${CPU_CORES}"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p models logs data cache monitoring/grafana/dashboards monitoring/grafana/datasources
    chmod 755 models logs data cache
    
    log "✅ Directories created"
}

# Backup existing deployment
backup_existing() {
    if [ -f "$COMPOSE_FILE" ] && docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | grep -q "Up"; then
        log "Backing up existing deployment..."
        
        mkdir -p "$BACKUP_DIR"
        
        # Backup data
        if [ -d "./data" ]; then
            cp -r ./data "$BACKUP_DIR/"
        fi
        
        # Backup logs
        if [ -d "./logs" ]; then
            cp -r ./logs "$BACKUP_DIR/"
        fi
        
        # Export database if exists
        if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | grep -q postgres; then
            log "Backing up database..."
            docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T postgres pg_dumpall -U postgres > "$BACKUP_DIR/database_backup.sql"
        fi
        
        log "✅ Backup completed: $BACKUP_DIR"
    fi
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    log "✅ Images pulled"
}

# Build application image
build_application() {
    log "Building DRYAD.AI application image..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache DRYAD.AI
    log "✅ Application image built"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    
    log "✅ Services deployed"
}

# Wait for services to be healthy
wait_for_health() {
    log "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | grep -q "healthy\|Up"; then
            log "✅ Services are healthy"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts - Waiting for services..."
        sleep 10
        ((attempt++))
    done
    
    error "Services failed to become healthy within timeout"
    return 1
}

# Run post-deployment tests
run_tests() {
    log "Running post-deployment tests..."
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Health check passed"
    else
        error "Health check failed"
        return 1
    fi
    
    # Test AI functionality
    log "Testing AI functionality..."
    response=$(curl -s -X POST http://localhost:8000/api/v1/agents/simple-query \
        -H "Content-Type: application/json" \
        -d '{"query": "What is artificial intelligence?"}' || echo "FAILED")
    
    if [[ "$response" != "FAILED" ]] && [[ "$response" == *"result"* ]]; then
        log "✅ AI functionality test passed"
    else
        warn "AI functionality test failed or incomplete"
    fi
    
    log "✅ Post-deployment tests completed"
}

# Display deployment information
show_deployment_info() {
    log "Deployment Information:"
    echo "======================"
    echo "🌐 Application URL: http://localhost:8000"
    echo "📊 API Documentation: http://localhost:8000/docs"
    echo "📈 Monitoring (Grafana): http://localhost:3000 (admin/admin123)"
    echo "📊 Prometheus: http://localhost:9090"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo "📁 Data Directories:"
    echo "   Models: ./models"
    echo "   Logs: ./logs"
    echo "   Data: ./data"
    echo "   Cache: ./cache"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"
    echo "   Stop services: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
    echo "   Restart: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart"
    echo "   Scale: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d --scale DRYAD.AI=2"
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        error "Deployment failed. Check logs for details:"
        echo "docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment process
main() {
    log "Starting DRYAD.AI production deployment..."
    
    check_prerequisites
    create_directories
    backup_existing
    pull_images
    build_application
    deploy_services
    
    if wait_for_health; then
        run_tests
        show_deployment_info
        log "🎉 Deployment completed successfully!"
    else
        error "Deployment failed during health checks"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log "Stopping DRYAD.AI services..."
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
        log "✅ Services stopped"
        ;;
    "restart")
        log "Restarting DRYAD.AI services..."
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart
        log "✅ Services restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
        ;;
    "backup")
        backup_existing
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|backup}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the production system (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  backup  - Backup current deployment"
        exit 1
        ;;
esac
