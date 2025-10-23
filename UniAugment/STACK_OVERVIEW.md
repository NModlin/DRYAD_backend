# UniAugment Stack Overview

## 📁 Project Structure

```
UniAugment/
├── scripts/                          # Deployment and utility scripts
│   ├── install.sh                   # Interactive stack installer
│   ├── deploy-full-stack.sh         # Automated full stack deployment
│   └── utils/                       # Utility scripts
│       ├── health-check.sh          # Service health verification
│       ├── backup.sh                # Database and data backup
│       └── logs.sh                  # Log viewer
│
├── docker/                          # Docker configurations
│   ├── lite/                        # LITE stack image
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── full/                        # FULL stack image
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── hybrid/                      # HYBRID stack image
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── shared/                      # Shared configurations
│       └── init-db.sql              # Database initialization
│
├── compose/                         # Docker Compose files
│   ├── docker-compose.lite.yml      # LITE stack (1 container)
│   ├── docker-compose.full.yml      # FULL stack (7+ containers)
│   └── docker-compose.hybrid.yml    # HYBRID stack (3 containers)
│
├── config/                          # Configuration files
│   ├── .env.lite                    # LITE stack environment
│   ├── .env.full                    # FULL stack environment
│   ├── .env.hybrid                  # HYBRID stack environment
│   ├── .env.example                 # Configuration template
│   └── stack_config.py              # Runtime stack detection
│
├── monitoring/                      # Monitoring configurations
│   ├── prometheus.yml               # Prometheus scrape config
│   └── grafana/                     # Grafana provisioning
│
├── docs/                            # University documentation (15 files)
│   ├── AGENTIC_UNIVERSITY_ANALYSIS.md
│   ├── AGENTIC_UNIVERSITY_ARCHITECTURE.md
│   ├── ARENA_DOJO_COMPETITION_FRAMEWORK.md
│   ├── TRAINING_DATA_PIPELINE.md
│   ├── WEBSOCKET_INTEGRATION_ARCHITECTURE.md
│   ├── MULTI_UNIVERSITY_DEPLOYMENT_STRATEGY.md
│   └── ... (9 more documentation files)
│
├── src/                             # Application source code (future)
│   └── config/
│       └── stack_config.py          # Stack configuration module
│
├── README.md                        # Project overview
├── DEPLOYMENT_GUIDE.md              # Deployment instructions
├── STACK_OVERVIEW.md                # This file
├── IMPLEMENTATION_CHECKLIST.md      # Phase-by-phase tasks
├── PROJECT_STRUCTURE.md             # Detailed structure
├── SETUP_COMPLETE.md                # Setup status
└── .gitignore                       # Git ignore rules
```

---

## 🎯 Three Deployment Stacks

### LITE Stack
**Single Container - Development & Testing**

```
┌─────────────────────────────────────┐
│     UniAugment LITE Container       │
├─────────────────────────────────────┤
│ • FastAPI + Uvicorn                 │
│ • SQLite Database                   │
│ • In-memory Caching                 │
│ • APScheduler (Tasks)               │
│ • Chroma (Vector DB)                │
└─────────────────────────────────────┘
```

**Resources**: ~500MB RAM, 1 CPU  
**Best For**: Development, Phase 1-3  
**Setup Time**: 2 minutes

### HYBRID Stack
**3 Containers - Staging**

```
┌──────────────────────────────────────────────────┐
│         UniAugment HYBRID Stack                  │
├──────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐  │
│ │ FastAPI + Uvicorn                           │  │
│ │ In-memory Caching                           │  │
│ │ APScheduler (Tasks)                         │  │
│ └─────────────────────────────────────────────┘  │
│ ┌─────────────────────────────────────────────┐  │
│ │ PostgreSQL Database                         │  │
│ └─────────────────────────────────────────────┘  │
│ ┌─────────────────────────────────────────────┐  │
│ │ Weaviate Vector Database                    │  │
│ └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

**Resources**: ~2GB RAM, 2 CPUs  
**Best For**: Staging, Phase 2-3  
**Setup Time**: 5 minutes

### FULL Stack
**7+ Containers - Production**

```
┌────────────────────────────────────────────────────────────┐
│              UniAugment FULL Stack                         │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐   │
│ │ FastAPI + Uvicorn (API)                              │   │
│ │ Redis Caching                                        │   │
│ │ Celery Workers (Background Tasks)                    │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PostgreSQL Database                                  │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Redis (Cache & Task Broker)                          │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Weaviate Vector Database                             │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Ollama (Local LLM - Optional)                        │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Prometheus (Metrics)                                 │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Grafana (Dashboards)                                 │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Resources**: ~4GB RAM, 4 CPUs  
**Best For**: Production, Phase 4+  
**Setup Time**: 10 minutes

---

## 🚀 Quick Start Commands

### Interactive Installation
```bash
./scripts/install.sh
```

### Automated Full Stack Deployment
```bash
./scripts/deploy-full-stack.sh
```

### Manual Deployment
```bash
# LITE
docker-compose -f compose/docker-compose.lite.yml up -d

# HYBRID
docker-compose -f compose/docker-compose.hybrid.yml up -d

# FULL
docker-compose -f compose/docker-compose.full.yml up -d
```

---

## 📊 Configuration Files

### Environment Files
- `.env.lite` - LITE stack configuration
- `.env.full` - FULL stack configuration
- `.env.hybrid` - HYBRID stack configuration
- `.env.example` - Configuration template

### Docker Files
- `docker/lite/Dockerfile` - LITE image
- `docker/full/Dockerfile` - FULL image
- `docker/hybrid/Dockerfile` - HYBRID image

### Compose Files
- `compose/docker-compose.lite.yml` - LITE orchestration
- `compose/docker-compose.full.yml` - FULL orchestration
- `compose/docker-compose.hybrid.yml` - HYBRID orchestration

---

## 🔧 Utility Scripts

| Script | Purpose |
|--------|---------|
| `scripts/install.sh` | Interactive stack selection and installation |
| `scripts/deploy-full-stack.sh` | Automated full stack deployment with credential management |
| `scripts/utils/health-check.sh` | Verify all services are healthy |
| `scripts/utils/backup.sh` | Backup database and data volumes |
| `scripts/utils/logs.sh` | View logs from specific services |

---

## 📈 Service URLs

### LITE Stack
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### HYBRID Stack
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Weaviate: http://localhost:8081
- PostgreSQL: localhost:5432

### FULL Stack
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Weaviate: http://localhost:8081
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- **IMPLEMENTATION_CHECKLIST.md** - Phase-by-phase implementation tasks
- **PROJECT_STRUCTURE.md** - Detailed project structure
- **docs/** - University system documentation (15 files)

---

## 🔐 Security

- All credentials stored in `.env` file
- `.env` is in `.gitignore` (never committed)
- JWT secret keys auto-generated
- Database passwords auto-generated
- SSL/TLS support for production

---

## 🎓 Next Steps

1. **Choose Your Stack**: Run `./scripts/install.sh`
2. **Deploy**: Follow DEPLOYMENT_GUIDE.md
3. **Verify**: Run `./scripts/utils/health-check.sh`
4. **Access API**: http://localhost:8000/docs
5. **Monitor**: Access Grafana at http://localhost:3000

---

**Ready to deploy? Start with `./scripts/install.sh`! 🚀**

