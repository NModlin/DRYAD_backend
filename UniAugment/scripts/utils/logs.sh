#!/bin/bash
# Logs Viewer Script for UniAugment
# View logs from specific services

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
COMPOSE_FILE="${2:-compose/docker-compose.full.yml}"

# Service to view logs for
SERVICE="${1:-all}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}UniAugment Logs Viewer${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

if [ "$SERVICE" = "all" ]; then
    echo -e "${YELLOW}Viewing logs for all services...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f
elif [ "$SERVICE" = "api" ]; then
    echo -e "${YELLOW}Viewing logs for API...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f uniaugment-api
elif [ "$SERVICE" = "postgres" ]; then
    echo -e "${YELLOW}Viewing logs for PostgreSQL...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f postgres
elif [ "$SERVICE" = "redis" ]; then
    echo -e "${YELLOW}Viewing logs for Redis...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f redis
elif [ "$SERVICE" = "celery" ]; then
    echo -e "${YELLOW}Viewing logs for Celery Worker...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f celery-worker
elif [ "$SERVICE" = "weaviate" ]; then
    echo -e "${YELLOW}Viewing logs for Weaviate...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f weaviate
elif [ "$SERVICE" = "prometheus" ]; then
    echo -e "${YELLOW}Viewing logs for Prometheus...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f prometheus
elif [ "$SERVICE" = "grafana" ]; then
    echo -e "${YELLOW}Viewing logs for Grafana...${NC}\n"
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f grafana
else
    echo -e "${RED}Unknown service: $SERVICE${NC}"
    echo -e "\n${YELLOW}Available services:${NC}"
    echo "  all         - All services"
    echo "  api         - UniAugment API"
    echo "  postgres    - PostgreSQL"
    echo "  redis       - Redis"
    echo "  celery      - Celery Worker"
    echo "  weaviate    - Weaviate"
    echo "  prometheus  - Prometheus"
    echo "  grafana     - Grafana"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./logs.sh [service] [compose-file]"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./logs.sh api"
    echo "  ./logs.sh postgres compose/docker-compose.full.yml"
    exit 1
fi

