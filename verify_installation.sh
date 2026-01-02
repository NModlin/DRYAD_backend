#!/bin/bash
# DRYAD.AI Installation Verification Script
# Run this after installation to verify all services are working

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "DRYAD.AI Installation Verification"
echo -e "==========================================${NC}"
echo ""

# Track overall status
ALL_GOOD=true

# Function to check service
check_service() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -n "Checking $name... "
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ALL_GOOD=false
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name at $url... "
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ALL_GOOD=false
        return 1
    fi
}

echo -e "${YELLOW}System Services:${NC}"
check_service "Redis" "redis-cli ping | grep -q PONG"
check_service "Docker" "docker ps"
check_service "Ollama" "systemctl is-active ollama"
echo ""

echo -e "${YELLOW}Docker Containers:${NC}"
check_service "Weaviate container" "docker ps | grep -q weaviate"
check_service "Open WebUI container" "docker ps | grep -q open-webui"
echo ""

echo -e "${YELLOW}HTTP Services:${NC}"
check_http "Ollama API" "http://localhost:11434/api/tags"
check_http "Weaviate" "http://localhost:8080/v1/.well-known/ready"
check_http "Open WebUI" "http://localhost:3000"
check_http "DRYAD Health" "http://localhost:8000/health"
echo ""

echo -e "${YELLOW}Ollama Models:${NC}"
if command -v ollama &> /dev/null; then
    MODELS=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$MODELS" -gt 0 ]; then
        echo -e "${GREEN}✓ Found $MODELS model(s)${NC}"
        ollama list
    else
        echo -e "${RED}✗ No models found${NC}"
        echo "  Run: ollama pull llama3.2:8b"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}✗ Ollama not installed${NC}"
    ALL_GOOD=false
fi
echo ""

echo -e "${YELLOW}Python Environment:${NC}"
if [ -d "$HOME/dryad_backend/.venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    
    # Check if we can activate and import dryad
    if source "$HOME/dryad_backend/.venv/bin/activate" 2>/dev/null; then
        echo -e "${GREEN}✓ Virtual environment can be activated${NC}"
        
        # Check if dryad module is importable
        if python -c "import dryad" 2>/dev/null; then
            echo -e "${GREEN}✓ DRYAD module is importable${NC}"
        else
            echo -e "${RED}✗ DRYAD module cannot be imported${NC}"
            ALL_GOOD=false
        fi
        deactivate 2>/dev/null
    else
        echo -e "${RED}✗ Cannot activate virtual environment${NC}"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    ALL_GOOD=false
fi
echo ""

echo -e "${YELLOW}GPU Status:${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader
    echo -e "${GREEN}✓ GPU detected${NC}"
else
    echo -e "${YELLOW}⚠ nvidia-smi not found (GPU may not be available)${NC}"
fi
echo ""

echo -e "${YELLOW}Network Connectivity:${NC}"
check_http "Internet (example.com)" "http://example.com"
echo ""

echo -e "${YELLOW}File System:${NC}"
if [ -f "$HOME/dryad_backend/.env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
else
    echo -e "${RED}✗ .env file not found${NC}"
    ALL_GOOD=false
fi

if [ -f "$HOME/dryad_backend/dryad.db" ] || [ -f "$HOME/dryad_backend/data/DRYAD.AI.db" ]; then
    echo -e "${GREEN}✓ Database file exists${NC}"
else
    echo -e "${YELLOW}⚠ Database file not found (will be created on first run)${NC}"
fi
echo ""

# Final summary
echo -e "${BLUE}=========================================="
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "DRYAD.AI is ready to use!"
    echo ""
    echo "Access points:"
    echo "  - DRYAD API Docs: http://localhost:8000/docs"
    echo "  - DRYAD Health: http://localhost:8000/health"
    echo "  - Open WebUI (Chat): http://localhost:3000"
    echo "  - Ollama API: http://localhost:11434"
    echo "  - Weaviate: http://localhost:8080"
    echo ""
    echo "To start DRYAD:"
    echo "  sudo systemctl start dryad"
    echo ""
    echo "Or manually:"
    echo "  cd ~/dryad_backend"
    echo "  source .venv/bin/activate"
    echo "  python -m uvicorn dryad.main:app --host 0.0.0.0 --port 8000"
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please review the errors above and:"
    echo "  1. Check service status: systemctl status <service>"
    echo "  2. View logs: journalctl -u <service> -n 50"
    echo "  3. Restart services: systemctl restart <service>"
    echo ""
    echo "For help, see SERVER_INSTALLATION_GUIDE.md"
fi
echo -e "==========================================${NC}"

