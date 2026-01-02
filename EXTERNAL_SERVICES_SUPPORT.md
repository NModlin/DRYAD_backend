# External Services Support

## Overview

The DRYAD.AI enhanced installer now automatically detects and uses already-installed services instead of failing on port conflicts. This is particularly useful when you have Redis or Ollama already running on your system.

## What Changed

### Before
- Installer detected port conflicts (e.g., Redis on 6379, Ollama on 11434)
- Asked if you wanted to continue anyway
- **Failed if you said "No"**
- Would try to start duplicate services in Docker

### After
- Installer **detects** if Redis or Ollama are already running
- **Verifies** they are the correct services (not just any process)
- **Uses** the existing services automatically
- **Skips** starting those services in Docker
- **Configures** the application to connect to existing services

## Supported External Services

### 1. Redis (Port 6379)
**Detection Methods:**
- Checks if `redis-cli ping` works
- Checks if Redis is running in Docker
- Tests network connection to port 6379

**Configuration:**
- If detected: Uses `redis://localhost:6379`
- If not detected: Starts Redis in Docker at `redis://redis:6379`

### 2. Ollama (Port 11434)
**Detection Methods:**
- Checks if `ollama list` command works
- Tests HTTP API at `http://localhost:11434/api/tags`
- Checks if Ollama systemd service is active

**Configuration:**
- If detected: Uses `http://localhost:11434`
- If not detected: Starts Ollama in Docker at `http://ollama:11434`

## How It Works

### 1. Port Conflict Detection
When you run the installer, it checks for port conflicts:

```bash
./install_dryad_enhanced.sh
```

During the "Checking for port conflicts" step:
- Scans all required ports
- For Redis (6379) and Ollama (11434), runs service detection
- Sets flags: `USE_EXTERNAL_REDIS` and `USE_EXTERNAL_OLLAMA`

### 2. Service Verification
The installer verifies services are actually running:

**Redis:**
```bash
redis-cli ping  # Should return PONG
```

**Ollama:**
```bash
ollama list  # Should list available models
curl http://localhost:11434/api/tags  # Should return JSON
```

### 3. Configuration Generation
The `.env` file is generated with correct URLs:

**External Redis:**
```env
REDIS_URL=redis://localhost:6379
```

**External Ollama:**
```env
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Docker Compose Override
A `docker-compose.override.yml` file is created to disable services:

```yaml
version: '3.8'

services:
  redis:
    deploy:
      replicas: 0
    profiles:
      - disabled
  
  ollama:
    deploy:
      replicas: 0
    profiles:
      - disabled
```

This prevents Docker from starting duplicate services.

## Example Installation Flow

### Scenario: Redis and Ollama Already Running

```bash
$ ./install_dryad_enhanced.sh

...

========================================
Step 8: Check Port Conflicts
========================================

[STEP] Checking for port conflicts and existing services...
[SUCCESS] ✓ Detected existing Redis service
[SUCCESS] ✓ Detected existing Ollama service

[INFO] The following existing services will be used:
  ✓ Redis (port 6379) - will use existing instance
  ✓ Ollama (port 11434) - will use existing instance

[SUCCESS] No port conflicts detected

...

[INFO] Creating docker-compose override for external services...
[SUCCESS] Created docker-compose.override.yml for external services

...

[SUCCESS] Using existing Ollama installation
[INFO] Checking if llama3.2:3b model is available...
[SUCCESS] Model llama3.2:3b is already available
```

## Benefits

### 1. No Duplicate Services
- Saves system resources (RAM, CPU)
- Avoids port conflicts
- Uses your existing configuration

### 2. Seamless Integration
- Automatically detects and configures
- No manual configuration needed
- Works with system-installed or Docker services

### 3. Flexibility
- Use system Redis with Docker backend
- Use system Ollama with Docker backend
- Mix and match as needed

## Technical Details

### Files Modified

1. **lib/utils.sh**
   - Added `is_redis_running()` function
   - Added `is_ollama_running()` function
   - Added `get_service_on_port()` function

2. **lib/config_generators.sh**
   - Modified `check_port_conflicts()` to detect services
   - Modified `generate_backend_env()` to use correct URLs

3. **lib/install_functions.sh**
   - Added `create_external_services_override()` function
   - Modified `install_backend()` to use override file
   - Modified `setup_ollama()` to skip if external

### Environment Variables

The installer sets these flags during execution:

```bash
export USE_EXTERNAL_REDIS=true   # or false
export USE_EXTERNAL_OLLAMA=true  # or false
export REDIS_HOST="localhost"
export OLLAMA_HOST="http://localhost:11434"
```

## Troubleshooting

### Redis Not Detected
If Redis is running but not detected:

```bash
# Test manually
redis-cli ping

# Check if it's listening
lsof -i :6379

# Check service status
systemctl status redis
```

### Ollama Not Detected
If Ollama is running but not detected:

```bash
# Test manually
ollama list

# Test HTTP API
curl http://localhost:11434/api/tags

# Check service status
systemctl status ollama
```

### Force Docker Services
If you want to use Docker services even though system services exist:

1. Stop the system services:
   ```bash
   sudo systemctl stop redis
   sudo systemctl stop ollama
   ```

2. Run the installer
3. Restart system services later if needed

## Future Enhancements

Potential additions for future versions:
- PostgreSQL detection and reuse
- Weaviate detection and reuse
- Custom port configuration
- Service health monitoring
- Automatic failover between external and Docker services

---

**Last Updated:** January 2, 2026  
**Version:** 2.1

