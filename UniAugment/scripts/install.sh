#!/bin/bash
# UniAugment Stack Installer
# Interactive installation with stack selection
# Usage: ./install.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         UniAugment Installation - Choose Your Stack            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Show options
show_options() {
    echo -e "${YELLOW}Available Stacks:${NC}\n"
    
    echo "1) ${GREEN}LITE Stack${NC} (Minimal, Single Container)"
    echo "   - FastAPI + SQLite"
    echo "   - In-memory caching"
    echo "   - APScheduler for tasks"
    echo "   - Perfect for: Development, Phase 1-3"
    echo "   - Resources: ~500MB RAM, 1 CPU"
    echo ""
    
    echo "2) ${GREEN}FULL Stack${NC} (Production, Microservices)"
    echo "   - FastAPI + PostgreSQL"
    echo "   - Redis caching"
    echo "   - Celery workers"
    echo "   - Weaviate vector DB"
    echo "   - Monitoring (Prometheus, Grafana)"
    echo "   - Perfect for: Production, Phase 4+"
    echo "   - Resources: ~4GB RAM, 4 CPUs"
    echo ""
    
    echo "3) ${GREEN}HYBRID Stack${NC} (Best of Both)"
    echo "   - FastAPI + PostgreSQL"
    echo "   - In-memory cache (no Redis)"
    echo "   - APScheduler (no Celery)"
    echo "   - Weaviate vector DB"
    echo "   - Perfect for: Staging, Phase 2-3"
    echo "   - Resources: ~2GB RAM, 2 CPUs"
    echo ""
}

# Get user selection
get_selection() {
    read -p "Select stack (1-3): " STACK_CHOICE
    
    case $STACK_CHOICE in
        1)
            STACK_TYPE="lite"
            COMPOSE_FILE="docker-compose.lite.yml"
            ENV_FILE=".env.lite"
            ;;
        2)
            STACK_TYPE="full"
            COMPOSE_FILE="docker-compose.full.yml"
            ENV_FILE=".env.full"
            ;;
        3)
            STACK_TYPE="hybrid"
            COMPOSE_FILE="docker-compose.hybrid.yml"
            ENV_FILE=".env.hybrid"
            ;;
        *)
            echo -e "${RED}Invalid selection. Exiting.${NC}"
            exit 1
            ;;
    esac
}

# Validate prerequisites
validate_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    local missing=()
    
    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing+=("docker-compose")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}Missing required tools: ${missing[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Create environment file
create_env() {
    echo -e "\n${YELLOW}Creating environment file...${NC}"
    
    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}Warning: .env file already exists${NC}"
        read -p "Overwrite? (y/n) [n]: " OVERWRITE
        if [ "$OVERWRITE" != "y" ]; then
            echo -e "${GREEN}✓ Using existing .env file${NC}"
            return
        fi
    fi
    
    cp "$PROJECT_ROOT/config/$ENV_FILE" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ Environment file created${NC}"
}

# Build images
build_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    
    cd "$PROJECT_ROOT"
    docker-compose -f "compose/$COMPOSE_FILE" build
    
    echo -e "${GREEN}✓ Docker images built${NC}"
}

# Start services
start_services() {
    echo -e "\n${YELLOW}Starting services...${NC}"
    
    cd "$PROJECT_ROOT"
    docker-compose -f "compose/$COMPOSE_FILE" up -d
    
    echo -e "${GREEN}✓ Services started${NC}"
}

# Wait for services
wait_services() {
    echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 10
    echo -e "${GREEN}✓ Services ready${NC}"
}

# Show status
show_status() {
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Installation Complete!                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${BLUE}Stack Type:${NC} $STACK_TYPE"
    echo -e "${BLUE}Compose File:${NC} compose/$COMPOSE_FILE"
    echo -e "${BLUE}Environment:${NC} .env\n"
    
    echo -e "${YELLOW}Service URLs:${NC}"
    echo -e "  ${GREEN}API:${NC}        http://localhost:8000"
    echo -e "  ${GREEN}API Docs:${NC}   http://localhost:8000/docs"
    
    if [ "$STACK_TYPE" = "full" ] || [ "$STACK_TYPE" = "hybrid" ]; then
        echo -e "  ${GREEN}Weaviate:${NC}   http://localhost:8081"
    fi
    
    if [ "$STACK_TYPE" = "full" ]; then
        echo -e "  ${GREEN}Prometheus:${NC} http://localhost:9090"
        echo -e "  ${GREEN}Grafana:${NC}    http://localhost:3000 (admin/admin)"
    fi
    
    echo ""
    
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Check service health: docker-compose -f compose/$COMPOSE_FILE ps"
    echo "  2. View logs: docker-compose -f compose/$COMPOSE_FILE logs -f"
    echo "  3. Stop services: docker-compose -f compose/$COMPOSE_FILE down"
    echo ""
    
    if [ "$STACK_TYPE" = "full" ]; then
        echo -e "${BLUE}For automated full deployment with credential management:${NC}"
        echo "  ./scripts/deploy-full-stack.sh"
        echo ""
    fi
}

# Main
main() {
    print_banner
    show_options
    get_selection
    
    echo -e "\n${GREEN}✓ Selected: $STACK_TYPE Stack${NC}\n"
    
    validate_prerequisites
    create_env
    build_images
    start_services
    wait_services
    show_status
    
    echo -e "${GREEN}Installation complete! Happy coding! 🚀${NC}"
}

main "$@"

