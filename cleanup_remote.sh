#!/bin/bash
# Script to clean up the accidental home directory clutter on the remote server

SERVER="katalyst@192.168.6.65"

# List of files to remove from the home directory (~/)
FILES_TO_REMOVE=(
    "install_dryad_enhanced.sh"
    "dryad.service"
    "SERVER_INSTALLATION_GUIDE.md"
    "QUICK_START_SERVER.md"
    "INSTALLATION_FILES_README.md"
    "INSTALLATION_IMPROVEMENTS.md"
    "ERROR_HANDLING_SUMMARY.md"
    "OPEN_WEBUI_GUIDE.md"
)

# Directory to remove
DIR_TO_REMOVE="lib"

echo "=========================================="
echo "Cleaning up remote server: $SERVER"
echo "=========================================="
echo ""
echo "This will remove the installer files that were accidentally copied to proper home directory (~/)."
echo ""

# Construct the remove command
CMD="cd ~ && rm -f"
for file in "${FILES_TO_REMOVE[@]}"; do
    CMD="$CMD $file"
done

# Add directory removal
CMD="$CMD && rm -rf $DIR_TO_REMOVE"

echo "Running cleanup command on server..."
# Use single quotes for the command to prevent local variable expansion
ssh "$SERVER" "$CMD"

if [ $? -eq 0 ]; then
    echo ""
    echo "Processing complete. Files removed."
    echo "=========================================="
else
    echo ""
    echo "Error: Cleanup failed."
    exit 1
fi
