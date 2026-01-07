#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Docker relocation to /home/docker-data...${NC}"

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Please run as root (use sudo)${NC}"
  exit 1
fi

# 1. Stop Docker
echo "Stopping Docker service..."
systemctl stop docker
systemctl stop docker.socket

# 2. Create new directory
echo "Creating new directory at /home/docker-data..."
mkdir -p /home/docker-data

# 3. Move data (rsync to preserve permissions)
echo "Moving existing Docker data (this may take a while)..."
rsync -aP /var/lib/docker/ /home/docker-data/

# 4. Backup old directory
echo "Backing up old /var/lib/docker..."
mv /var/lib/docker /var/lib/docker.bak

# 5. Configure Docker to use new location
echo "Configuring daemon.json..."
mkdir -p /etc/docker
if [ -f /etc/docker/daemon.json ]; then
    # If exists, we need to merge or edit. For now, let's assume simple case or back it up.
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    # Using python to safe merge or just jq if available, but let's try simple sed/cat approach if potential conflict
    # OR simpler: just write the file if we know what we want.
    # Let's check safely. 
    echo -e "${RED}Warning: /etc/docker/daemon.json already exists. Overwriting/Merging...${NC}"
    # Minimal valid json with data-root
    echo '{ "data-root": "/home/docker-data" }' > /etc/docker/daemon.json
else
    echo '{ "data-root": "/home/docker-data" }' > /etc/docker/daemon.json
fi

# 6. Restart Docker
echo "Restarting Docker..."
systemctl start docker

# 7. Verification
echo "Verifying Docker info..."
docker info | grep "Docker Root Dir"

echo -e "${GREEN}Docker successfully relocated to /home/docker-data!${NC}"
echo "You can now remove the backup '/var/lib/docker.bak' once you confirm everything works to free up space on /"
