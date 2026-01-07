#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Docker Configuration Fix...${NC}"

# 1. Stop Docker to be safe
echo "Stopping Docker..."
sudo systemctl stop docker || true

# 2. Ensure /etc/docker exists
echo "Ensuring /etc/docker directory exists..."
sudo mkdir -p /etc/docker

# 3. Write the daemon.json config
echo "Configuring Docker to use /home/docker-data..."
echo '{ "data-root": "/home/docker-data" }' | sudo tee /etc/docker/daemon.json > /dev/null

# 4. Ensure the data directory exists
echo "Ensuring /home/docker-data directory exists..."
sudo mkdir -p /home/docker-data

# 5. Restart Docker
echo "Restarting Docker..."
sudo systemctl restart docker

# 6. Verify Configuration
echo "Verifying Docker Root Dir..."
ROOT_DIR=$(sudo docker info --format '{{.DockerRootDir}}')
echo "Detected Root Dir: $ROOT_DIR"

if [[ "$ROOT_DIR" == "/home/docker-data" ]]; then
    echo -e "${GREEN}SUCCESS: Docker is now correctly configured to use /home/docker-data${NC}"
    
    echo "Cleaning up any potential leftovers..."
    sudo docker system prune -a -f
    
    echo -e "${GREEN}You can now proceed with the installation!${NC}"
else
    echo -e "${RED}ERROR: Docker is still using $ROOT_DIR${NC}"
    echo "Please inspect /etc/docker/daemon.json manually."
    exit 1
fi
