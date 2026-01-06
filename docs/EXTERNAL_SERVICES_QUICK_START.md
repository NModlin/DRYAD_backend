# External Services - Quick Start Guide

## For Users

### I already have Redis/Ollama installed. What do I do?

**Nothing!** Just run the installer normally:

```bash
./install_dryad_enhanced.sh
```

The installer will:
1. Detect your existing services
2. Configure DRYAD to use them
3. Skip starting duplicate Docker containers

### How do I know if it detected my services?

Look for these messages during installation:

```
[SUCCESS] ✓ Detected existing Redis service
[SUCCESS] ✓ Detected existing Ollama service

[INFO] The following existing services will be used:
  ✓ Redis (port 6379) - will use existing instance
  ✓ Ollama (port 11434) - will use existing instance
```

### What if I want to use Docker services instead?

Stop your system services before running the installer:

```bash
# Stop Redis
sudo systemctl stop redis
# or
sudo service redis stop

# Stop Ollama
sudo systemctl stop ollama
# or
pkill ollama
```

Then run the installer.

### Can I switch between external and Docker services later?

Yes! Just:

1. Stop the DRYAD backend:
   ```bash
   docker compose down
   ```

2. Start/stop your external services as needed

3. Update `.env` file:
   ```bash
   # For external Redis:
   REDIS_URL=redis://localhost:6379
   
   # For Docker Redis:
   REDIS_URL=redis://redis:6379
   
   # For external Ollama:
   OLLAMA_BASE_URL=http://localhost:11434
   
   # For Docker Ollama:
   OLLAMA_BASE_URL=http://ollama:11434
   ```

4. Restart:
   ```bash
   docker compose up -d
   ```

## For Developers

### Testing Service Detection

Run the test script:

```bash
./test_service_detection.sh
```

### Adding Support for New Services

To add detection for a new service (e.g., PostgreSQL):

1. **Add detection function in `lib/utils.sh`:**

```bash
is_postgresql_running() {
    # Check if psql command works
    if command_exists psql; then
        if psql -U postgres -c "SELECT 1" &>/dev/null; then
            return 0
        fi
    fi
    
    # Check via network connection
    if timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/5432" 2>/dev/null; then
        return 0
    fi
    
    return 1
}
```

2. **Add detection in `lib/config_generators.sh`:**

```bash
# In check_port_conflicts() function
5432)
    if is_postgresql_running; then
        existing_services+=("PostgreSQL (port 5432) - will use existing instance")
        export USE_EXTERNAL_POSTGRESQL=true
        export POSTGRES_HOST="localhost"
        print_success "✓ Detected existing PostgreSQL service"
    else
        conflicts+=("Port $port ($service) is in use by unknown process")
    fi
    ;;
```

3. **Update config generation in `lib/config_generators.sh`:**

```bash
# In generate_backend_env() function
# Database
$(if [[ "$USE_EXTERNAL_POSTGRESQL" == "true" ]]; then
  echo "DATABASE_URL=postgresql://user:pass@localhost:5432/dryad"
else
  echo "DATABASE_URL=postgresql://user:pass@postgres:5432/dryad"
fi)
```

4. **Add to override in `lib/install_functions.sh`:**

```bash
# In install_backend() function, in the override creation section
if [[ "$USE_EXTERNAL_POSTGRESQL" == "true" ]]; then
    cat >> docker-compose.override.yml << 'EOF'
  postgres:
    deploy:
      replicas: 0
    profiles:
      - disabled
EOF
fi
```

### Environment Variables Set by Installer

During installation, these variables are exported:

```bash
USE_EXTERNAL_REDIS=true|false
USE_EXTERNAL_OLLAMA=true|false
REDIS_HOST="localhost"
OLLAMA_HOST="http://localhost:11434"
```

Access them in your functions:

```bash
if [[ "$USE_EXTERNAL_REDIS" == "true" ]]; then
    echo "Using external Redis"
fi
```

### Debugging

Enable debug output:

```bash
set -x  # Enable bash debug mode
./install_dryad_enhanced.sh
```

Check service detection manually:

```bash
source lib/utils.sh

# Test Redis
if is_redis_running; then
    echo "Redis is running"
fi

# Test Ollama
if is_ollama_running; then
    echo "Ollama is running"
fi
```

### Common Issues

**Issue:** Service detected but connection fails

**Solution:** Check firewall and service configuration:
```bash
# For Redis
redis-cli ping

# For Ollama
curl http://localhost:11434/api/tags
```

**Issue:** Service not detected but is running

**Solution:** Check if service is listening on localhost:
```bash
netstat -tuln | grep 6379   # Redis
netstat -tuln | grep 11434  # Ollama
```

**Issue:** Want to force Docker services

**Solution:** Stop external services before installation:
```bash
sudo systemctl stop redis ollama
./install_dryad_enhanced.sh
```

## Architecture

```
┌─────────────────────────────────────────┐
│     install_dryad_enhanced.sh           │
│                                         │
│  1. Check prerequisites                 │
│  2. Gather configuration                │
│  3. Check port conflicts ◄──────────┐   │
│     └─ Detect services              │   │
│        └─ Set USE_EXTERNAL_* flags  │   │
│  4. Generate configs                │   │
│     └─ Use correct URLs based on    │   │
│        external service flags       │   │
│  5. Create override file            │   │
│  6. Start Docker services           │   │
│     └─ Skip external services       │   │
└─────────────────────────────────────────┘
         │
         ├─► lib/utils.sh
         │   └─ is_redis_running()
         │   └─ is_ollama_running()
         │
         ├─► lib/config_generators.sh
         │   └─ check_port_conflicts()
         │   └─ generate_backend_env()
         │
         └─► lib/install_functions.sh
             └─ install_backend() (creates override inline)
             └─ setup_ollama()
```

## Quick Reference

| Service | Port  | Detection Method | Config Variable |
|---------|-------|------------------|-----------------|
| Redis   | 6379  | redis-cli ping   | USE_EXTERNAL_REDIS |
| Ollama  | 11434 | HTTP API check   | USE_EXTERNAL_OLLAMA |

| File | Purpose |
|------|---------|
| `lib/utils.sh` | Service detection functions |
| `lib/config_generators.sh` | Port checking and config generation |
| `lib/install_functions.sh` | Installation orchestration |
| `docker-compose.override.yml` | Disable external services in Docker |
| `.env` | Application configuration |

---

**Need Help?** Check the full documentation in `EXTERNAL_SERVICES_SUPPORT.md`

