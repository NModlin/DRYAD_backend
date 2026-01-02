#!/bin/bash
# Script to deploy DRYAD installation files to the server

SERVER="katalyst@192.168.6.65"
FILES=(
    "install_dryad_server.sh"
    "verify_installation.sh"
    "dryad.service"
    "SERVER_INSTALLATION_GUIDE.md"
    "QUICK_START_SERVER.md"
    "INSTALLATION_FILES_README.md"
    "INSTALLATION_IMPROVEMENTS.md"
    "ERROR_HANDLING_SUMMARY.md"
    "OPEN_WEBUI_GUIDE.md"
)

echo "=========================================="
echo "DRYAD.AI Server Deployment Script"
echo "=========================================="
echo ""
echo "Copying installation files to $SERVER..."
echo ""

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Copying $file..."
        scp "$file" "$SERVER:~/"
    else
        echo "Warning: $file not found, skipping..."
    fi
done

echo ""
echo "=========================================="
echo "Files copied successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH into the server:"
echo "   ssh $SERVER"
echo ""
echo "2. Run the installation script:"
echo "   chmod +x install_dryad_server.sh"
echo "   ./install_dryad_server.sh"
echo ""
echo "3. (Optional) Set up systemd service:"
echo "   sudo cp dryad.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable dryad"
echo "   sudo systemctl start dryad"
echo ""
echo "For detailed instructions, see SERVER_INSTALLATION_GUIDE.md"
echo ""

