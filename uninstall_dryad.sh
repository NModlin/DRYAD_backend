#!/bin/bash
# DRYAD.AI Uninstallation Script
# Removes services, docker containers, images, and large files to free up disk space.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}==========================================${NC}"
echo -e "${RED}      DRYAD.AI UNINSTALLATION TOOL        ${NC}"
echo -e "${RED}==========================================${NC}"
echo -e "${YELLOW}WARNING: This will delete data, containers, and models to free space.${NC}"
echo ""

# 1. Stop Systemd Services
echo -e "${GREEN}Step 1: Stopping Systemd Services...${NC}"
if systemctl is-active --quiet dryad; then
    echo "Stopping dryad service..."
    sudo systemctl stop dryad
    sudo systemctl disable dryad
    sudo rm /etc/systemd/system/dryad.service
    sudo systemctl daemon-reload
    echo "Dryad service removed."
else
    echo "Dryad service not found or not running."
fi

# 2. Stop and Remove Docker Containers
echo -e "${GREEN}Step 2: Cleaning up Docker Containers & Volumes...${NC}"
# defined in install script
CONTAINERS=("dryad-redis" "weaviate" "open-webui")
for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "Stopping and removing $container..."
        docker stop "$container" 2>/dev/null
        docker rm "$container" 2>/dev/null
    fi
done

# Remove associated volumes (where data lives)
echo "Removing Docker volumes..."
docker volume rm redis_data weaviate_data open_webui_data 2>/dev/null || true

# 3. Remove Docker Images
echo -e "${GREEN}Step 3: Removing Docker Images...${NC}"
IMAGES=("redis:7-alpine" "semitechnologies/weaviate:latest" "ghcr.io/open-webui/open-webui:main")
for image in "${IMAGES[@]}"; do
    echo "Removing image $image..."
    docker rmi "$image" 2>/dev/null || true
done

echo "Pruning dangling images..."
docker image prune -f

# 4. Clean up Ollama (Large Models)
echo -e "${GREEN}Step 4: Removing Ollama Models (Space Reclaimer)...${NC}"
if command -v ollama &> /dev/null; then
    # List of models installed by our script
    MODELS=("llama3.2:8b" "mistral:7b" "qwen2.5:14b")
    for model in "${MODELS[@]}"; do
        echo "Removing Ollama model $model..."
        ollama rm "$model" 2>/dev/null || true
    done
    
    echo -e "${YELLOW}Do you want to uninstall Ollama entirely? (y/N)${NC}"
    read -r -n 1 response
    echo ""
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo systemctl stop ollama
        sudo systemctl disable ollama
        sudo rm $(which ollama)
        sudo rm -rf /usr/share/ollama
        sudo userdel ollama
        sudo groupdel ollama
        echo "Ollama uninstalled."
    fi
else
    echo "Ollama not found."
fi

# 5. Remove Python Virtual Environment
echo -e "${GREEN}Step 5: Removing Virtual Environment...${NC}"
if [ -d ".venv" ]; then
    rm -rf .venv
    echo ".venv directory removed."
fi

# 6. Remove Legacy/Archive Data
echo -e "${GREEN}Step 6: Removing Legacy Archives...${NC}"
if [ -d "archive" ]; then
    echo "Removing archive directory..."
    rm -rf archive
    echo "archive directory removed."
fi

if [ -d "src/dryad/services/memory_guild" ]; then
     echo -e "${YELLOW}Do you want to delete the restored source code and database data? (y/N)${NC}"
     echo "This includes 'src' and 'dryad.db'"
     read -r -n 1 response
     echo ""
     if [[ "$response" =~ ^[Yy]$ ]]; then
         rm -rf src
         rm -f dryad.db
         rm -rf data
         echo "Source code and local database removed."
     fi
fi

echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "You may delete this folder manually if you wish to remove the scripts."
