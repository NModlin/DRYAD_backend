# DRYAD.AI Enhanced Installation System

A comprehensive, interactive installation system for DRYAD.AI with full component selection and configuration.

## Features

✨ **Interactive Menu System**
- Step-by-step guided installation
- Clear descriptions of each option
- Resource requirement estimates
- Port conflict detection

🎯 **Flexible Deployment Options**
- 7 deployment configurations (minimal to GPU-accelerated)
- 3 optional frontend applications
- Multiple backend enhancements
- Comprehensive monitoring and logging

🔧 **Smart Configuration**
- Automatic .env file generation
- Secure secret generation
- LLM provider configuration
- Domain customization

🏥 **Health Checks**
- Automated service verification
- Comprehensive status reporting
- Detailed troubleshooting information

📊 **Resource Management**
- Memory and disk space checking
- Estimated resource requirements
- Warning for insufficient resources

## Quick Start

```bash
./install_dryad_enhanced.sh
```

Follow the interactive prompts to customize your installation.

## Architecture

### Directory Structure

```
DRYAD_backend/
├── install_dryad_enhanced.sh    # Main installation script
├── lib/                         # Library modules
│   ├── utils.sh                 # Common utilities
│   ├── menu_functions.sh        # Interactive menus
│   ├── install_functions.sh     # Installation logic
│   ├── config_generators.sh     # Configuration generators
│   └── health_checks.sh         # Health check functions
├── ENHANCED_INSTALLER_GUIDE.md  # User guide
└── README_INSTALLER.md          # This file
```

### Module Breakdown

#### `utils.sh`
Common utility functions used across all modules:
- Logging and output formatting
- Color-coded messages
- Service health checks
- Port availability checks
- System resource queries
- User confirmation prompts

#### `menu_functions.sh`
Interactive menu system:
- Welcome screen
- Deployment configuration selection
- Frontend application selection
- Optional component selection
- LLM provider configuration
- Domain configuration
- Installation confirmation with summary

#### `install_functions.sh`
Installation logic:
- Prerequisites checking
- Directory creation
- Backend service installation
- Frontend application installation
- MCP server enablement
- Ollama setup

#### `config_generators.sh`
Configuration file generators:
- Backend .env file generation
- Secure secret generation
- Port conflict detection
- Component-specific configuration

#### `health_checks.sh`
Service health verification:
- Backend API health checks
- Frontend health checks
- Monitoring stack verification
- Logging stack verification
- Comprehensive status reporting

## Deployment Configurations

| Configuration | RAM    | Disk  | Features                          |
|--------------|--------|-------|-----------------------------------|
| Minimal      | 1-2GB  | 5GB   | Core API only                     |
| Basic        | 2-4GB  | 10GB  | Standard features                 |
| Development  | 4-6GB  | 15GB  | Hot reload + debugging            |
| Full         | 6-8GB  | 20GB  | All services + Celery             |
| Production   | 8-10GB | 25GB  | Nginx + SSL + monitoring          |
| Scalable     | 10-12GB| 30GB  | Multi-worker + load balancing     |
| GPU          | 12GB+  | 40GB  | GPU-accelerated ML                |

## Frontend Applications

### Dryads Console (Port 3001)
- Quantum-inspired knowledge tree navigator
- Multi-provider AI consultation
- Memory Keeper system
- Document viewer with Perplexity AI

### DRYAD University UI (Port 3006)
- Student/Faculty/Admin dashboards
- Agent creation wizard
- Competition system
- Curriculum management

### Writer Portal (Port 3000)
- Next.js document management
- RAG queries with citations
- Real-time WebSocket progress
- OAuth2 Google login

## Optional Components

### Backend Enhancements
- **MCP Server:** Model Context Protocol endpoint
- **PostgreSQL:** Production-grade database (instead of SQLite)
- **Celery Workers:** Background task processing

### Monitoring & Observability
- **Prometheus + Grafana:** Metrics and visualization
- **ELK Stack:** Elasticsearch, Kibana, Fluentd logging
- **Full Metrics Suite:** All exporters (cAdvisor, Node, Postgres, Redis)

## LLM Providers

- **Mock:** Fake responses for testing (no API key needed)
- **OpenAI:** GPT models (requires API key)
- **Anthropic:** Claude models (requires API key)
- **Ollama:** Local LLM (downloads models automatically)

## Prerequisites

- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Node.js:** 18+ (for frontends)
- **npm:** 8+ (for frontends)
- **Bash:** 4.0+

## Installation Process

1. Clone the repository
2. Run `./install_dryad_enhanced.sh`
3. Follow the interactive prompts
4. Wait for installation to complete
5. Access your services!

## Post-Installation

After installation, you'll receive:
- Complete service URLs
- Management commands
- Troubleshooting tips
- Configuration file locations
- Installation summary file

## Customization

### Adding New Deployment Configurations

Edit `lib/install_functions.sh` and add your configuration to the `install_backend()` function.

### Adding New Frontend Applications

1. Add the frontend to `lib/menu_functions.sh` in `select_frontends()`
2. Add installation logic to `lib/install_functions.sh` in `install_frontend()`
3. Add health check to `lib/health_checks.sh`

### Adding New Optional Components

1. Add the component to `lib/menu_functions.sh` in `select_optional_components()`
2. Add installation logic to `lib/install_functions.sh`
3. Update configuration generation in `lib/config_generators.sh`

## Troubleshooting

### Script Fails to Start

```bash
# Make sure script is executable
chmod +x install_dryad_enhanced.sh lib/*.sh

# Check bash version
bash --version  # Should be 4.0+
```

### Docker Issues

```bash
# Check Docker is running
docker info

# Check Docker Compose
docker compose version
```

### Port Conflicts

The installer automatically checks for port conflicts. If detected:
- Stop conflicting services
- Or choose to continue anyway (may cause issues)

### Frontend Build Failures

```bash
# Check Node.js version
node --version  # Should be 18+

# Try manual installation
cd archive/legacy_v9/clients/[frontend-name]
npm install --legacy-peer-deps
npm run dev
```

## Contributing

To contribute to the installer:

1. Follow the modular architecture
2. Add functions to appropriate library files
3. Update documentation
4. Test thoroughly with different configurations

## License

Same as DRYAD.AI project license.

---

**Made with ❤️ for the DRYAD.AI community**

