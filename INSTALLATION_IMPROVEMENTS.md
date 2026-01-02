# Installation Script Improvements - Version 2.0

## Overview

The installation script has been completely rewritten with comprehensive error handling and intelligent detection of existing installations.

---

## 🆕 What's New in Version 2.0

### 1. **Removed `set -e` - Manual Error Handling**

**Before:**
```bash
set -e  # Exit on ANY error
```

**Problem:** Would exit if a package was already installed or any minor issue occurred.

**After:**
- Manual error checking for each operation
- Graceful handling of non-critical failures
- Continues installation even if optional components fail

### 2. **Smart Detection of Existing Installations**

#### System Packages
```bash
# Checks if package is already installed before attempting installation
if is_package_installed "$pkg"; then
    info "$pkg already installed"
else
    info "Installing $pkg..."
fi
```

**Handles:**
- ✅ Docker already installed → Skips installation
- ✅ Redis already installed → Skips installation
- ✅ All system packages checked individually

#### Services
```bash
# Checks if service is already running
if is_service_running "docker"; then
    success "Docker already running"
else
    sudo systemctl start docker
fi
```

**Handles:**
- ✅ Docker already running → Doesn't restart
- ✅ Redis already running → Doesn't restart
- ✅ Ollama already running → Doesn't restart

#### Ollama Models
```bash
# Checks if model exists before pulling
if ollama list | grep -q "^$model"; then
    success "Model $model already installed"
else
    ollama pull "$model"
fi
```

**Handles:**
- ✅ Models already downloaded → Skips download
- ✅ Failed model download → Continues with warning
- ✅ Can retry failed downloads later

#### Weaviate Container
```bash
# Checks if container exists
if docker ps -a --format '{{.Names}}' | grep -q "weaviate"; then
    # Container exists, check if running
    if docker ps --format '{{.Names}}' | grep -q "weaviate"; then
        success "Weaviate already running"
    else
        docker start weaviate
    fi
fi
```

**Handles:**
- ✅ Container exists and running → Does nothing
- ✅ Container exists but stopped → Starts it
- ✅ Container doesn't exist → Creates it

#### Git Repository
```bash
if [ -d "$INSTALL_DIR" ]; then
    # Directory exists
    if [ -d ".git" ]; then
        # Stash local changes
        git stash
        git pull
    fi
else
    git clone ...
fi
```

**Handles:**
- ✅ Directory exists → Updates instead of failing
- ✅ Local changes → Stashes them before pulling
- ✅ Not a git repo → Uses existing directory

#### Environment File
```bash
if [ -f ".env" ]; then
    # Backup existing
    cp .env ".env.backup.$(date +%s)"
    # Ask user
    read -p "Overwrite existing .env? (y/N): "
fi
```

**Handles:**
- ✅ .env exists → Backs up and asks before overwriting
- ✅ Preserves existing configuration if desired

### 3. **Comprehensive Logging**

```bash
LOG_FILE="$HOME/dryad_install.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}
```

**Features:**
- ✅ All actions logged with timestamps
- ✅ Log file saved to `~/dryad_install.log`
- ✅ Can review installation history
- ✅ Helpful for troubleshooting

### 4. **Better User Feedback**

**Color-coded messages:**
- 🟢 **Green (success):** Operation completed successfully
- 🟡 **Yellow (warning):** Non-critical issue, continuing
- 🔴 **Red (error):** Critical error, stopping
- 🔵 **Blue (info):** Informational message

**Progress tracking:**
```bash
INSTALL_STATE=()  # Tracks what was installed

success() {
    echo -e "${GREEN}✓ $1${NC}"
    INSTALL_STATE+=("$1")
}
```

### 5. **Installation Summary**

At the end, shows:
- ✅ List of all successfully installed components
- ✅ Current status of all services
- ✅ Access points and URLs
- ✅ Next steps
- ✅ Important notes and warnings

### 6. **Validation and Verification**

**Service checks:**
```bash
# Verify Ollama is accessible
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    success "Ollama API is accessible"
fi

# Verify Weaviate is ready
for i in {1..30}; do
    if curl -s http://localhost:8080/v1/.well-known/ready &> /dev/null; then
        success "Weaviate is ready"
        break
    fi
    sleep 1
done
```

---

## 🔧 Error Handling Examples

### Example 1: Package Already Installed

**Before (v1.0):**
```bash
sudo pacman -S docker  # Would fail if already installed
```

**After (v2.0):**
```bash
if is_package_installed "docker"; then
    info "docker already installed"
else
    sudo pacman -S --noconfirm docker
fi
```

### Example 2: Service Already Running

**Before (v1.0):**
```bash
sudo systemctl start redis  # Would show error if already running
```

**After (v2.0):**
```bash
if ! is_service_running "redis"; then
    sudo systemctl start redis
else
    success "Redis already running"
fi
```

### Example 3: Failed Model Download

**Before (v1.0):**
```bash
ollama pull llama3.2:8b  # Script exits if download fails
```

**After (v2.0):**
```bash
if ollama pull "llama3.2:8b"; then
    success "Model downloaded"
else
    warn "Failed to pull model (you can pull it later)"
    # Script continues
fi
```

---

## 📊 What Happens If...

### Docker is already installed?
✅ Script detects it, skips installation, verifies it's running

### Redis is already running?
✅ Script detects it, confirms status, continues

### Weaviate container exists?
✅ Script checks if running, starts if stopped, creates if missing

### Ollama models are already downloaded?
✅ Script checks each model, skips already-downloaded ones

### DRYAD directory already exists?
✅ Script updates repository, stashes local changes if needed

### .env file already exists?
✅ Script backs it up, asks if you want to overwrite

### Installation fails midway?
✅ Script logs error, shows what was completed, can resume

### Network connection fails?
✅ Script warns, continues with what's available, can retry later

---

## 🎯 Key Benefits

1. **Idempotent** - Can run multiple times safely
2. **Resumable** - Can continue after failures
3. **Non-destructive** - Preserves existing installations
4. **Informative** - Clear feedback at every step
5. **Logged** - Complete installation history
6. **Flexible** - Handles various system states
7. **Safe** - Backs up before overwriting

---

## 📝 Usage

The script works exactly the same way:

```bash
./install_dryad_server.sh
```

But now it's much smarter about:
- What's already installed
- What needs to be updated
- What can be skipped
- What failed and why

---

## 🔍 Troubleshooting

If something goes wrong:

1. **Check the log file:**
   ```bash
   cat ~/dryad_install.log
   ```

2. **Review the summary** at the end of installation

3. **Run verification:**
   ```bash
   ./verify_installation.sh
   ```

4. **Re-run the script** - It's safe to run multiple times!

---

## 🚀 Next Steps

After installation:

1. Review the installation summary
2. Check service status
3. Run verification script
4. Set up systemd service
5. Test the API

The improved script makes installation much more reliable and user-friendly!

