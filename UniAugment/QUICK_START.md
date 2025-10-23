# 🚀 UniAugment Quick Start Guide

## 30-Second Setup

```bash
cd UniAugment
chmod +x scripts/*.sh scripts/utils/*.sh
./scripts/install.sh
```

Choose your stack (1-3) and you're done! ✅

---

## 5-Minute Automated Setup

```bash
cd UniAugment
chmod +x scripts/*.sh scripts/utils/*.sh
./scripts/deploy-full-stack.sh
```

This will:
- Ask for credentials (or auto-generate)
- Build Docker images
- Start all services
- Run health checks
- Show you the deployment info

---

## Stack Selection

| Need | Stack | Command |
|------|-------|---------|
| **Development** | LITE | `./scripts/install.sh` → Choose 1 |
| **Staging** | HYBRID | `./scripts/install.sh` → Choose 3 |
| **Production** | FULL | `./scripts/deploy-full-stack.sh` |

---

## After Deployment

### Access the API
```
http://localhost:8000/docs
```

### Check Health
```bash
./scripts/utils/health-check.sh
```

### View Logs
```bash
./scripts/utils/logs.sh api
./scripts/utils/logs.sh postgres
./scripts/utils/logs.sh all
```

### Backup Data
```bash
./scripts/utils/backup.sh 30
```

---

## Service URLs

### LITE Stack
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### HYBRID Stack
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Weaviate**: http://localhost:8081
- **PostgreSQL**: localhost:5432

### FULL Stack
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Weaviate**: http://localhost:8081
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Common Commands

```bash
# View services
docker-compose -f compose/docker-compose.full.yml ps

# Stop services
docker-compose -f compose/docker-compose.full.yml down

# Restart services
docker-compose -f compose/docker-compose.full.yml restart

# View specific logs
docker-compose -f compose/docker-compose.full.yml logs -f uniaugment-api

# Execute command in container
docker-compose -f compose/docker-compose.full.yml exec postgres psql -U uniaugment
```

---

## Troubleshooting

### Services won't start?
```bash
./scripts/utils/health-check.sh
./scripts/utils/logs.sh all
```

### Port already in use?
Edit `compose/docker-compose.full.yml` and change ports:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Need to reset?
```bash
docker-compose -f compose/docker-compose.full.yml down -v
rm -rf data/ logs/
./scripts/deploy-full-stack.sh
```

---

## File Structure

```
UniAugment/
├── scripts/
│   ├── install.sh                    # Interactive installer
│   ├── deploy-full-stack.sh          # Automated deployment
│   └── utils/
│       ├── health-check.sh
│       ├── backup.sh
│       └── logs.sh
├── docker/
│   ├── lite/
│   ├── full/
│   ├── hybrid/
│   └── shared/
├── compose/
│   ├── docker-compose.lite.yml
│   ├── docker-compose.full.yml
│   └── docker-compose.hybrid.yml
├── config/
│   ├── .env.lite
│   ├── .env.full
│   ├── .env.hybrid
│   └── stack_config.py
├── monitoring/
│   └── prometheus.yml
└── docs/
    └── (15 university documentation files)
```

---

## Documentation

- **DEPLOYMENT_GUIDE.md** - Full deployment instructions
- **STACK_OVERVIEW.md** - Architecture overview
- **DEPLOYMENT_COMPLETE.md** - What was created
- **QUICK_START.md** - This file

---

## Next Steps

1. ✅ Run `./scripts/install.sh`
2. ✅ Choose your stack
3. ✅ Wait for deployment
4. ✅ Access http://localhost:8000/docs
5. ✅ Create your first university!

---

## Need Help?

```bash
# Check deployment info
cat .deployment-info.txt

# View logs
./scripts/utils/logs.sh all

# Run health check
./scripts/utils/health-check.sh

# Read full guide
cat DEPLOYMENT_GUIDE.md
```

---

**Ready? Let's go! 🚀**

```bash
./scripts/install.sh
```

