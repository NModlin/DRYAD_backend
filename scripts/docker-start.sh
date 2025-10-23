#!/bin/bash
# DRYAD.AI Backend - Docker Startup Script
# Provides easy commands for different deployment scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_TIER=${INSTALL_TIER:-standard}
ENVIRONMENT=${ENVIRONMENT:-development}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before continuing."
        print_warning "At minimum, set JWT_SECRET_KEY and any API keys you plan to use."
        read -p "Press Enter to continue after editing .env file..."
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs nginx/ssl monitoring
    chmod 755 data logs
}

# Function to start minimal installation
start_minimal() {
    print_status "Starting DRYAD.AI in minimal mode..."
    export INSTALL_TIER=minimal
    docker-compose -f docker-compose.minimal.yml up -d
    print_success "Minimal installation started!"
    print_status "API available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
}

# Function to start standard installation
start_standard() {
    print_status "Starting DRYAD.AI in standard mode..."
    export INSTALL_TIER=standard
    docker-compose up -d gremlins-api weaviate redis celery-worker
    print_success "Standard installation started!"
    print_status "API available at: http://localhost:8000"
    print_status "Weaviate available at: http://localhost:8080"
    print_status "API Documentation: http://localhost:8000/docs"
}

# Function to start full installation
start_full() {
    print_status "Starting DRYAD.AI in full mode..."
    export INSTALL_TIER=full
    docker-compose up -d
    print_success "Full installation started!"
    print_status "API available at: http://localhost:8000"
    print_status "Weaviate available at: http://localhost:8080"
    print_status "API Documentation: http://localhost:8000/docs"
}

# Function to start development environment
start_development() {
    print_status "Starting DRYAD.AI development environment..."
    docker-compose -f docker-compose.development.yml up -d
    print_success "Development environment started!"
    print_status "API available at: http://localhost:8000 (with hot reload)"
    print_status "Weaviate available at: http://localhost:8080"
    print_status "Redis available at: http://localhost:6379"
    print_status "API Documentation: http://localhost:8000/docs"
}

# Function to start with local LLM
start_with_ollama() {
    print_status "Starting DRYAD.AI with Ollama local LLM..."
    docker-compose --profile local-llm up -d
    print_status "Waiting for Ollama to start..."
    sleep 10
    print_status "Pulling recommended model (llama3.2:3b)..."
    docker exec gremlins-ollama ollama pull llama3.2:3b
    print_success "DRYAD.AI with Ollama started!"
    print_status "API available at: http://localhost:8000"
    print_status "Ollama available at: http://localhost:11434"
}

# Function to start with monitoring
start_with_monitoring() {
    print_status "Starting DRYAD.AI with monitoring..."
    docker-compose --profile monitoring up -d
    print_success "DRYAD.AI with monitoring started!"
    print_status "API available at: http://localhost:8000"
    print_status "Grafana available at: http://localhost:3000 (admin/admin)"
    print_status "Prometheus available at: http://localhost:9090"
}

# Function to stop all services
stop_all() {
    print_status "Stopping all DRYAD.AI services..."
    docker-compose -f docker-compose.yml down
    docker-compose -f docker-compose.minimal.yml down
    docker-compose -f docker-compose.development.yml down
    print_success "All services stopped!"
}

# Function to show status
show_status() {
    print_status "DRYAD.AI Service Status:"
    docker-compose ps
}

# Function to show logs
show_logs() {
    local service=${1:-gremlins-api}
    print_status "Showing logs for $service..."
    docker-compose logs -f $service
}

# Function to run health check
health_check() {
    print_status "Running health check..."
    
    # Check API
    if curl -f http://localhost:8000/api/v1/health/status > /dev/null 2>&1; then
        print_success "✓ API is healthy"
    else
        print_error "✗ API is not responding"
    fi
    
    # Check Weaviate (if running)
    if curl -f http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        print_success "✓ Weaviate is healthy"
    else
        print_warning "⚠ Weaviate is not responding (may not be running)"
    fi
    
    # Check Redis (if running)
    if docker exec gremlins-redis redis-cli ping > /dev/null 2>&1; then
        print_success "✓ Redis is healthy"
    else
        print_warning "⚠ Redis is not responding (may not be running)"
    fi
}

# Function to show help
show_help() {
    echo "DRYAD.AI Backend - Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  minimal       Start minimal installation (basic API only)"
    echo "  standard      Start standard installation (with vector DB and multi-agent)"
    echo "  full          Start full installation (all features including multimodal)"
    echo "  dev           Start development environment (with hot reload)"
    echo "  ollama        Start with local Ollama LLM"
    echo "  monitoring    Start with monitoring (Grafana + Prometheus)"
    echo "  stop          Stop all services"
    echo "  status        Show service status"
    echo "  logs [service] Show logs (default: gremlins-api)"
    echo "  health        Run health check"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 minimal                    # Start basic API"
    echo "  $0 standard                   # Start with AI features"
    echo "  $0 dev                        # Start development environment"
    echo "  $0 logs gremlins-api         # Show API logs"
    echo "  $0 health                     # Check service health"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        minimal)
            check_env_file
            create_directories
            start_minimal
            ;;
        standard)
            check_env_file
            create_directories
            start_standard
            ;;
        full)
            check_env_file
            create_directories
            start_full
            ;;
        dev|development)
            check_env_file
            create_directories
            start_development
            ;;
        ollama)
            check_env_file
            create_directories
            start_with_ollama
            ;;
        monitoring)
            check_env_file
            create_directories
            start_with_monitoring
            ;;
        stop)
            stop_all
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs $2
            ;;
        health)
            health_check
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
