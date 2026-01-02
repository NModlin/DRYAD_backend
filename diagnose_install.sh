#!/bin/bash
# Diagnostic script to troubleshoot installation issues

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    DRYAD.AI Installation Diagnostics                         ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "1. Current Directory:"
echo "   $(pwd)"
echo ""

echo "2. Script Location:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "   $SCRIPT_DIR"
echo ""

echo "3. Checking for lib directory:"
if [ -d "$SCRIPT_DIR/lib" ]; then
    echo "   ✓ lib directory exists"
    echo ""
    echo "4. Files in lib directory:"
    ls -lh "$SCRIPT_DIR/lib/"
else
    echo "   ✗ lib directory NOT found at: $SCRIPT_DIR/lib"
    echo ""
    echo "   Searching for lib directory..."
    find "$SCRIPT_DIR" -type d -name "lib" 2>/dev/null | head -5
fi
echo ""

echo "5. Checking install_dryad_enhanced.sh:"
if [ -f "$SCRIPT_DIR/install_dryad_enhanced.sh" ]; then
    echo "   ✓ install_dryad_enhanced.sh exists"
    echo "   Path: $SCRIPT_DIR/install_dryad_enhanced.sh"
    echo "   Permissions: $(ls -lh "$SCRIPT_DIR/install_dryad_enhanced.sh" | awk '{print $1}')"
else
    echo "   ✗ install_dryad_enhanced.sh NOT found"
fi
echo ""

echo "6. Testing path resolution:"
TEST_PATH="$SCRIPT_DIR/lib/utils.sh"
echo "   Looking for: $TEST_PATH"
if [ -f "$TEST_PATH" ]; then
    echo "   ✓ File exists and is accessible"
else
    echo "   ✗ File NOT found"
fi
echo ""

echo "7. Checking all DRYAD directories in home:"
find /home/katalyst -maxdepth 3 -type d -name "*DRYAD*" 2>/dev/null | while read dir; do
    echo "   Found: $dir"
done
echo ""

echo "8. Git repository info:"
if [ -d "$SCRIPT_DIR/.git" ]; then
    echo "   ✓ This is a git repository"
    echo "   Branch: $(git -C "$SCRIPT_DIR" branch --show-current 2>/dev/null || echo 'unknown')"
    echo "   Remote: $(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null || echo 'none')"
else
    echo "   ✗ Not a git repository"
fi
echo ""

echo "9. Recommended action:"
echo ""
if [ -f "$SCRIPT_DIR/lib/utils.sh" ]; then
    echo "   ✅ Everything looks good! Try running:"
    echo ""
    echo "      cd $SCRIPT_DIR"
    echo "      ./install_dryad_enhanced.sh"
    echo ""
else
    echo "   ⚠️  Missing library files. Please run:"
    echo ""
    echo "      cd /home/katalyst"
    echo "      git clone https://github.com/NModlin/DRYAD_backend.git"
    echo "      cd DRYAD_backend"
    echo "      ./install_dryad_enhanced.sh"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════════════════════════"

