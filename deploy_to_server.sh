#!/bin/bash
# Script to deploy DRYAD installation files to the server

SERVER="katalyst@192.168.6.65"

echo "=========================================="
echo "DRYAD.AI Server Deployment Script"
echo "=========================================="
echo ""

INSTALL_DIR="dryad_installer"
DESTINATION="$SERVER:~/$INSTALL_DIR/"

echo "Deploying to: $DESTINATION"
echo ""

# Collect all files and directories to send
ITEMS=(
    "install_dryad_enhanced.sh"
    "force_move_containerd.sh"
    "dryad.service"
    "SERVER_INSTALLATION_GUIDE.md"
    "QUICK_START_SERVER.md"
    "INSTALLATION_FILES_README.md"
    "INSTALLATION_IMPROVEMENTS.md"
    "ERROR_HANDLING_SUMMARY.md"
    "OPEN_WEBUI_GUIDE.md"
    "pyproject.toml"
    "requirements.txt"
    "requirements-dev.txt"
    ".dockerignore"
    "Dockerfile"
    "Dockerfile.production"
    "lib"
    "src"
    "archive"
    "config"
    "configs"
)

FILES_TO_SEND=()

# Process items
for item in "${ITEMS[@]}"; do
    if [ -e "$item" ]; then
        FILES_TO_SEND+=("$item")
    else
        echo "Warning: $item not found, skipping..."
    fi
done

# Execute deployment using rsync for better performance and exclusions
if [ ${#FILES_TO_SEND[@]} -gt 0 ]; then
    # Create directory first
    echo "Creating directory $INSTALL_DIR on server..."
    if ! ssh "$SERVER" "mkdir -p $INSTALL_DIR"; then
        echo "Error: Failed to create directory on server."
        echo "Check your SSH connection and permissions."
        exit 1
    fi
    
    echo "Syncing code to server..."
    # Use rsync instead of scp
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # -z: compress
    # --delete: delete extraneous files from dest dirs (optional, maybe unsafe so omitted for now)
    # --exclude: skip heavy/generated folders
    
    if ! rsync -avz \
        --exclude 'node_modules' \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude '.venv' \
        --exclude 'venv' \
        --exclude '*.pyc' \
        --exclude '.DS_Store' \
        "${FILES_TO_SEND[@]}" \
        "$DESTINATION"; then
        
        echo ""
        echo "=========================================="
        echo "Error: Rsync transfer failed!"
        echo "=========================================="
        echo "Possible reasons:"
        echo "1. Authentication failed"
        echo "2. rsync not installed on remote server"
        echo "3. Network issue"
        exit 1
    fi
else
    echo "Error: No files to transfer!"
    exit 1
fi

echo ""
echo "=========================================="
echo "Files copied successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH into the server:"
echo "   ssh $SERVER"
echo ""
echo "2. Go to the installer directory:"
echo "   cd $INSTALL_DIR"
echo ""
echo "3. Run the installation script:"
echo "   chmod +x install_dryad_enhanced.sh"
echo "   ./install_dryad_enhanced.sh"
echo ""
echo "4. (Optional) Set up systemd service:"
echo "   sudo cp dryad.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable dryad"
echo "   sudo systemctl start dryad"
echo ""
echo "For detailed instructions, see SERVER_INSTALLATION_GUIDE.md"
echo ""

