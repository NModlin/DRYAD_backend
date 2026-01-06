#!/bin/bash
# Fix script for madhatter server - removes the erroneous function call

echo "Fixing lib/install_functions.sh on madhatter..."

# Backup the original file
cp /home/katalyst/DRYAD_backend/lib/install_functions.sh /home/katalyst/DRYAD_backend/lib/install_functions.sh.backup

# Remove line 142 which has the bad function call
sed -i '142d' /home/katalyst/DRYAD_backend/lib/install_functions.sh

echo "✓ Fixed! Removed the erroneous function call on line 142"
echo "✓ Backup saved to: /home/katalyst/DRYAD_backend/lib/install_functions.sh.backup"
echo ""
echo "You can now run the installer again:"
echo "  cd /home/katalyst/DRYAD_backend"
echo "  ./install_dryad_enhanced.sh"

