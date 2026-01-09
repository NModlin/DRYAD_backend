#!/bin/bash
# Script to clean up old DRYAD installation files from the remote server's home directory
# Use this after a successful migration to ~/dryad_installer

SERVER="katalyst@192.168.6.65"

echo "=========================================="
echo "DRYAD.AI Remote Cleanup Script"
echo "=========================================="
echo "This will remove old installation files from ~/"
echo "and keep the new installation in ~/dryad_installer/"
echo ""

FILES_TO_REMOVE=(
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

echo "Connecting to $SERVER..."
echo "You may be asked for your password."
echo ""

# build the remove command
REMOTE_CMD="cd ~ && echo 'Current directory: \$(pwd)' && "
for item in "${FILES_TO_REMOVE[@]}"; do
    # Be careful not to delete hidden files or directories that might be important
    # Only delete if it exists in the home root and matches our list
    REMOTE_CMD+="if [ -e \"$item\" ]; then echo 'Removing $item...'; rm -rf \"$item\"; fi; "
done

# Execute via SSH
ssh -t "$SERVER" "$REMOTE_CMD"

echo ""
echo "=========================================="
echo "Cleanup complete!"
echo "=========================================="
