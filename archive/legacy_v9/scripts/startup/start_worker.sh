#!/bin/bash
# start_worker.sh: Script to start Celery workers for DRYAD.AI Phase 5

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting DRYAD.AI Celery Workers...${NC}"

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}Error: Redis is not running. Please start Redis first.${NC}"
    echo -e "${YELLOW}To start Redis:${NC}"
    echo -e "  - On Windows: Start Redis service or run redis-server"
    echo -e "  - On macOS: brew services start redis"
    echo -e "  - On Linux: sudo systemctl start redis"
    exit 1
fi

echo -e "${GREEN}Redis is running!${NC}"

# Set environment variables if not already set
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}

echo -e "${YELLOW}Starting Celery worker with the following configuration:${NC}"
echo -e "  Redis URL: ${REDIS_URL}"
echo -e "  Worker name: DRYAD.AI-worker"
echo -e "  Concurrency: 4"
echo -e "  Log level: INFO"

# Start Celery worker
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --hostname=DRYAD.AI-worker@%h \
    --queues=default,agent_queue,document_queue,orchestration_queue \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=1000

echo -e "${GREEN}Celery worker stopped.${NC}"
