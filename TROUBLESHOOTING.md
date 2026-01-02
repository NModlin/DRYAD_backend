# Troubleshooting Guide

## Error: "No such file or directory" for lib/utils.sh

### Symptom
```
./install_dryad_enhanced.sh: line 16: /home/katalyst/DRYAD_backend/lib/utils.sh: No such file or directory
```

### Possible Causes

1. **Wrong directory** - You're running the script from the wrong location
2. **Missing files** - The lib directory or files are missing
3. **Symlink issue** - There's a broken symlink
4. **Multiple copies** - You have multiple copies of the repository

---

## Solution Steps

### Step 1: Run Diagnostics

```bash
./diagnose_install.sh
```

This will show you:
- Current directory
- Script location
- Whether lib files exist
- All DRYAD directories on your system

### Step 2: Verify You're in the Right Directory

```bash
pwd
```

Should show: `/home/katalyst/GitHub/DRYAD_backend`

If not, navigate there:
```bash
cd /home/katalyst/GitHub/DRYAD_backend
```

### Step 3: Verify Files Exist

```bash
ls -la lib/
```

Should show:
- config_generators.sh
- health_checks.sh
- install_functions.sh
- menu_functions.sh
- utils.sh

If files are missing, you may need to pull the latest changes:
```bash
git pull origin main
# or
git pull origin refactor
```

### Step 4: Make Sure Scripts are Executable

```bash
chmod +x install_dryad_enhanced.sh
chmod +x lib/*.sh
```

### Step 5: Try Running Again

```bash
./install_dryad_enhanced.sh
```

---

## Alternative: Fresh Clone

If the above doesn't work, try a fresh clone:

```bash
# Go to home directory
cd ~

# Remove old directory (if it exists)
rm -rf DRYAD_backend

# Clone fresh copy
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# Make scripts executable
chmod +x install_dryad_enhanced.sh lib/*.sh

# Run installer
./install_dryad_enhanced.sh
```

---

## Checking for Multiple Copies

```bash
# Find all DRYAD directories
find ~ -type d -name "*DRYAD*" 2>/dev/null

# Find all install scripts
find ~ -name "install_dryad_enhanced.sh" 2>/dev/null
```

If you find multiple copies, make sure you're using the one in:
`/home/katalyst/GitHub/DRYAD_backend`

---

## Manual Verification

Test the path resolution manually:

```bash
# Set the script directory
SCRIPT_DIR="$(cd "$(dirname "./install_dryad_enhanced.sh")" && pwd)"

# Print it
echo "SCRIPT_DIR: $SCRIPT_DIR"

# Check if lib exists
ls -la "$SCRIPT_DIR/lib/"

# Try to source the file
source "$SCRIPT_DIR/lib/utils.sh" && echo "SUCCESS: utils.sh loaded"
```

---

## Common Mistakes

### ❌ Running from wrong directory
```bash
cd /home/katalyst
./install_dryad_enhanced.sh  # WRONG - script not in this directory
```

### ✅ Running from correct directory
```bash
cd /home/katalyst/GitHub/DRYAD_backend
./install_dryad_enhanced.sh  # CORRECT
```

### ❌ Using absolute path from wrong location
```bash
cd /tmp
/home/katalyst/DRYAD_backend/install_dryad_enhanced.sh  # WRONG - wrong path
```

### ✅ Using absolute path correctly
```bash
cd /tmp
/home/katalyst/GitHub/DRYAD_backend/install_dryad_enhanced.sh  # CORRECT
```

---

## Still Not Working?

### Check Git Status

```bash
cd /home/katalyst/GitHub/DRYAD_backend
git status
git log --oneline -5
```

### Verify Branch

```bash
git branch
```

If you're on a different branch, switch to the correct one:
```bash
git checkout main
# or
git checkout refactor
```

### Pull Latest Changes

```bash
git pull
```

---

## Nuclear Option: Complete Reinstall

If nothing else works:

```bash
# 1. Remove everything
cd ~
rm -rf DRYAD_backend
rm -rf GitHub/DRYAD_backend

# 2. Fresh clone
mkdir -p GitHub
cd GitHub
git clone https://github.com/NModlin/DRYAD_backend.git
cd DRYAD_backend

# 3. Verify files
ls -la lib/

# 4. Make executable
chmod +x install_dryad_enhanced.sh lib/*.sh

# 5. Run diagnostics
./diagnose_install.sh

# 6. Run installer
./install_dryad_enhanced.sh
```

---

## Getting Help

If you're still stuck, provide this information:

```bash
# Run this and share the output
cat << 'EOF'
=== System Info ===
EOF
uname -a
echo ""

cat << 'EOF'
=== Current Directory ===
EOF
pwd
echo ""

cat << 'EOF'
=== Directory Contents ===
EOF
ls -la
echo ""

cat << 'EOF'
=== Lib Directory ===
EOF
ls -la lib/ 2>&1
echo ""

cat << 'EOF'
=== Script Path Test ===
EOF
SCRIPT_DIR="$(cd "$(dirname "./install_dryad_enhanced.sh")" && pwd)"
echo "SCRIPT_DIR: $SCRIPT_DIR"
ls -la "$SCRIPT_DIR/lib/" 2>&1
```

---

## Quick Reference

| Issue | Command |
|-------|---------|
| Check current directory | `pwd` |
| List files | `ls -la` |
| Check lib directory | `ls -la lib/` |
| Run diagnostics | `./diagnose_install.sh` |
| Make executable | `chmod +x install_dryad_enhanced.sh lib/*.sh` |
| Fresh clone | `git clone https://github.com/NModlin/DRYAD_backend.git` |
| Pull updates | `git pull` |
| Check branch | `git branch` |

