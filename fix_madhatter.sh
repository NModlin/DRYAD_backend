#!/bin/bash
# Quick fix for madhatter's install_functions.sh
# This adds the missing override file creation code

cd /home/katalyst/DRYAD_backend

# Backup the file
cp lib/install_functions.sh lib/install_functions.sh.backup_$(date +%Y%m%d_%H%M%S)

# Create a temporary file with the fix
cat > /tmp/install_functions_fix.txt << 'ENDFIX'
    # Create override file for external services
    if [[ "$USE_EXTERNAL_REDIS" == "true" ]] || [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then
        print_info "Creating docker-compose override for external services..."

        # Create the override file
        cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
EOF

        # If using external Redis, disable it in Docker
        if [[ "$USE_EXTERNAL_REDIS" == "true" ]]; then
            cat >> docker-compose.override.yml << 'EOF'
  redis:
    deploy:
      replicas: 0
    profiles:
      - disabled
EOF
        fi

        # If using external Ollama, disable it in Docker
        if [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then
            cat >> docker-compose.override.yml << 'EOF'
  ollama:
    deploy:
      replicas: 0
    profiles:
      - disabled
EOF
        fi

        print_success "Created docker-compose.override.yml for external services"
        compose_files="$compose_files -f docker-compose.override.yml"
    fi
ENDFIX

# Find and replace the broken section
sed -i '/# Create override file for external services/,/compose_files="$compose_files -f docker-compose.override.yml"/c\
    # Create override file for external services\
    if [[ "$USE_EXTERNAL_REDIS" == "true" ]] || [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then\
        print_info "Creating docker-compose override for external services..."\
\
        # Create the override file\
        cat > docker-compose.override.yml << '\''EOF'\''\
version: '\''3.8'\''\
\
services:\
EOF\
\
        # If using external Redis, disable it in Docker\
        if [[ "$USE_EXTERNAL_REDIS" == "true" ]]; then\
            cat >> docker-compose.override.yml << '\''EOF'\''\
  redis:\
    deploy:\
      replicas: 0\
    profiles:\
      - disabled\
EOF\
        fi\
\
        # If using external Ollama, disable it in Docker\
        if [[ "$USE_EXTERNAL_OLLAMA" == "true" ]]; then\
            cat >> docker-compose.override.yml << '\''EOF'\''\
  ollama:\
    deploy:\
      replicas: 0\
    profiles:\
      - disabled\
EOF\
        fi\
\
        print_success "Created docker-compose.override.yml for external services"\
        compose_files="$compose_files -f docker-compose.override.yml"\
    fi' lib/install_functions.sh

echo "✓ Fixed lib/install_functions.sh"
echo "✓ Backup saved"
echo ""
echo "Now you can run the installer again:"
echo "  ./install_dryad_enhanced.sh"

