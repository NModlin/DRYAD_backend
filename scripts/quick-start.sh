#!/bin/bash
# DRYAD.AI Backend - Quick Start Script
# Automated setup and deployment for new users

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_INSTALL_TIER="standard"
DEFAULT_LLM_PROVIDER="mock"

# Function to print colored output
print_header() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check system resources
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}' 2>/dev/null || echo "unknown")
    if [[ "$available_memory" != "unknown" && "$available_memory" -lt 2048 ]]; then
        print_warning "Available memory is ${available_memory}MB. Recommended: 4GB+ for standard installation."
        print_warning "Consider using minimal installation if you encounter memory issues."
    fi
    
    print_success "Prerequisites check completed"
}

# Function to gather user preferences
gather_preferences() {
    print_step "Gathering your preferences..."
    
    echo "Welcome to DRYAD.AI Backend Quick Start!"
    echo "This script will help you set up and deploy the DRYAD.AI Backend system."
    echo ""
    
    # Installation tier
    echo "Choose your installation tier:"
    echo "1) Minimal    - Basic API only (1-2GB RAM)"
    echo "2) Standard   - Full AI features (4-6GB RAM) [Recommended]"
    echo "3) Full       - All features including multimodal (8GB+ RAM)"
    echo "4) Development - Development environment with hot reload"
    echo ""
    
    while true; do
        read -p "Enter your choice (1-4) [2]: " tier_choice
        tier_choice=${tier_choice:-2}
        
        case $tier_choice in
            1) INSTALL_TIER="minimal"; break;;
            2) INSTALL_TIER="standard"; break;;
            3) INSTALL_TIER="full"; break;;
            4) INSTALL_TIER="development"; break;;
            *) echo "Please enter 1, 2, 3, or 4";;
        esac
    done
    
    # LLM Provider
    echo ""
    echo "Choose your LLM provider:"
    echo "1) Mock       - Fake responses for testing [Recommended for quick start]"
    echo "2) OpenAI     - Use OpenAI GPT models (requires API key)"
    echo "3) Ollama     - Local LLM (will download models)"
    echo ""
    
    while true; do
        read -p "Enter your choice (1-3) [1]: " llm_choice
        llm_choice=${llm_choice:-1}
        
        case $llm_choice in
            1) LLM_PROVIDER="mock"; break;;
            2) LLM_PROVIDER="openai"; break;;
            3) LLM_PROVIDER="ollama"; break;;
            *) echo "Please enter 1, 2, or 3";;
        esac
    done
    
    # Get OpenAI API key if needed
    if [[ "$LLM_PROVIDER" == "openai" ]]; then
        echo ""
        read -p "Enter your OpenAI API key: " OPENAI_API_KEY
        if [[ -z "$OPENAI_API_KEY" ]]; then
            print_warning "No API key provided. Falling back to mock provider."
            LLM_PROVIDER="mock"
        fi
    fi
    
    # Domain configuration
    echo ""
    read -p "Enter your domain (or press Enter for localhost): " DOMAIN
    DOMAIN=${DOMAIN:-localhost}
    
    print_success "Preferences gathered"
    print_info "Installation tier: $INSTALL_TIER"
    print_info "LLM provider: $LLM_PROVIDER"
    print_info "Domain: $DOMAIN"
}

# Function to setup environment
setup_environment() {
    print_step "Setting up environment configuration..."
    
    # Create .env file from template
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            print_success "Created .env file from template"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_warning ".env file already exists. Creating backup..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Generate secure JWT secret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -base64 48)
    
    # Update .env file
    sed -i.bak "s/INSTALL_TIER=.*/INSTALL_TIER=$INSTALL_TIER/" .env
    sed -i.bak "s/LLM_PROVIDER=.*/LLM_PROVIDER=$LLM_PROVIDER/" .env
    sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    
    if [[ "$LLM_PROVIDER" == "openai" && -n "$OPENAI_API_KEY" ]]; then
        sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
    fi
    
    if [[ "$DOMAIN" != "localhost" ]]; then
        sed -i.bak "s|API_BASE_URL=.*|API_BASE_URL=https://$DOMAIN|" .env
        sed -i.bak "s|FRONTEND_URL=.*|FRONTEND_URL=https://$DOMAIN|" .env
    fi
    
    # Clean up backup file
    rm -f .env.bak
    
    print_success "Environment configuration completed"
}

# Function to create necessary directories
create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p data logs nginx/ssl monitoring
    chmod 755 data logs
    
    print_success "Directories created"
}

# Function to start services
start_services() {
    print_step "Starting DRYAD.AI services..."
    
    case $INSTALL_TIER in
        "minimal")
            docker-compose -f docker-compose.minimal.yml up -d
            ;;
        "standard")
            docker-compose up -d gremlins-api weaviate redis celery-worker
            ;;
        "full")
            docker-compose up -d
            ;;
        "development")
            docker-compose -f docker-compose.development.yml up -d
            ;;
    esac
    
    print_success "Services started"
}

# Function to wait for services
wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    local max_wait=120
    local wait_time=0
    
    while [[ $wait_time -lt $max_wait ]]; do
        if curl -f http://localhost:8000/api/v1/health/status &> /dev/null; then
            print_success "API is ready!"
            break
        fi
        
        echo -n "."
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    if [[ $wait_time -ge $max_wait ]]; then
        print_error "Services did not start within timeout"
        print_info "Check logs with: docker-compose logs"
        exit 1
    fi
}

# Function to run health checks
run_health_checks() {
    print_step "Running health checks..."
    
    # API health check
    if curl -f http://localhost:8000/api/v1/health/status &> /dev/null; then
        print_success "✓ API is healthy"
    else
        print_error "✗ API health check failed"
        return 1
    fi
    
    # Service-specific checks based on installation tier
    if [[ "$INSTALL_TIER" != "minimal" ]]; then
        # Check Weaviate
        if curl -f http://localhost:8080/v1/.well-known/ready &> /dev/null; then
            print_success "✓ Weaviate is healthy"
        else
            print_warning "⚠ Weaviate is not responding (may still be starting)"
        fi
        
        # Check Redis
        if docker exec gremlins-redis redis-cli ping &> /dev/null; then
            print_success "✓ Redis is healthy"
        else
            print_warning "⚠ Redis is not responding"
        fi
    fi
    
    print_success "Health checks completed"
}

# Function to setup Ollama if needed
setup_ollama() {
    if [[ "$LLM_PROVIDER" == "ollama" ]]; then
        print_step "Setting up Ollama local LLM..."
        
        # Start Ollama if not already running
        if ! docker-compose ps ollama | grep -q "Up"; then
            docker-compose up -d ollama
            print_info "Waiting for Ollama to start..."
            sleep 30
        fi
        
        # Pull recommended model
        print_info "Downloading recommended model (llama3.2:3b)..."
        print_warning "This may take several minutes depending on your internet connection..."
        
        if docker exec gremlins-ollama ollama pull llama3.2:3b; then
            print_success "Ollama model downloaded successfully"
        else
            print_error "Failed to download Ollama model"
            print_info "You can download it later with: docker exec gremlins-ollama ollama pull llama3.2:3b"
        fi
    fi
}

# Function to display final information
display_final_info() {
    print_header "🎉 DRYAD.AI Backend Setup Complete!"
    
    echo "Your DRYAD.AI Backend is now running!"
    echo ""
    echo "📍 Access Points:"
    echo "   • API: http://localhost:8000"
    echo "   • Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/api/v1/health/status"
    
    if [[ "$INSTALL_TIER" != "minimal" ]]; then
        echo "   • Weaviate: http://localhost:8080"
    fi
    
    echo ""
    echo "🔧 Management Commands:"
    echo "   • View status: ./scripts/docker-start.sh status"
    echo "   • View logs: docker-compose logs -f gremlins-api"
    echo "   • Stop services: ./scripts/docker-start.sh stop"
    echo "   • Health check: ./scripts/docker-start.sh health"
    
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Test the API: curl http://localhost:8000/api/v1/health/status"
    echo "   2. Explore the documentation: http://localhost:8000/docs"
    echo "   3. Check the deployment guide: DEPLOYMENT_GUIDE.md"
    echo "   4. Set up authentication (see docs for OAuth2 setup)"
    
    if [[ "$LLM_PROVIDER" == "mock" ]]; then
        echo ""
        print_info "You're using mock LLM responses. To use real AI:"
        echo "   • Set up OpenAI: Add OPENAI_API_KEY to .env"
        echo "   • Use local LLM: Run ./scripts/docker-start.sh ollama"
    fi
    
    echo ""
    echo "🆘 Need Help?"
    echo "   • Troubleshooting: TROUBLESHOOTING.md"
    echo "   • Docker Guide: DOCKER_GUIDE.md"
    echo "   • GitHub Issues: <repository-url>/issues"
    
    echo ""
    print_success "Happy coding with DRYAD.AI! 🚀"
}

# Function to handle cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Setup failed. Cleaning up..."
        docker-compose down &> /dev/null || true
    fi
}

# Main execution
main() {
    trap cleanup EXIT
    
    print_header "🚀 DRYAD.AI Backend Quick Start"
    
    check_prerequisites
    gather_preferences
    setup_environment
    create_directories
    start_services
    wait_for_services
    setup_ollama
    run_health_checks
    display_final_info
}

# Run main function
main "$@"
