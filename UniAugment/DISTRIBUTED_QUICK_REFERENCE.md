# 🖥️ Distributed Setup - Quick Reference

## Your Hardware

```
Arch Linux 1 (HP Envy)     Arch Linux 2 (HP Envy)     Windows (Larger)
192.168.1.100              192.168.1.101              192.168.1.50
├─ FastAPI (8000)          ├─ Celery Workers          ├─ PostgreSQL (5432)
├─ Redis (6379)            ├─ Grafana (3000)          ├─ Weaviate (8080)
└─ Prometheus (9090)       ├─ Flower (5555)           ├─ pgAdmin (5050)
                           └─ Loki (3100)             └─ Adminer (8081)
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Arch Linux Machine 1:
```bash
chmod +x UniAugment/scripts/setup-arch-linux.sh
sudo ./UniAugment/scripts/setup-arch-linux.sh
# Select: arch-1, Role 1 (API Server)
# ✅ Docker Compose file auto-generated!
```

### 2. Arch Linux Machine 2:
```bash
chmod +x UniAugment/scripts/setup-arch-linux.sh
sudo ./UniAugment/scripts/setup-arch-linux.sh
# Select: arch-2, Role 2 (Workers)
# ✅ Docker Compose file auto-generated!
```

### 3. Windows Machine:
```powershell
powershell -ExecutionPolicy Bypass -File UniAugment\scripts\setup-windows.ps1
# Select: windows-db
# ✅ Docker Compose file auto-generated!
```

### 4. Start services:
```bash
# Windows first
C:\uniaugment\start-services.bat

# Then Arch machines
systemctl start uniaugment
```

**That's it!** No manual file copying needed - everything is auto-generated!

---

## 📊 Service Ports

| Port | Service | Machine |
|------|---------|---------|
| 8000 | FastAPI | Arch 1 |
| 6379 | Redis | Arch 1 |
| 9090 | Prometheus | Arch 1 |
| 3000 | Grafana | Arch 2 |
| 5555 | Flower | Arch 2 |
| 3100 | Loki | Arch 2 |
| 5432 | PostgreSQL | Windows |
| 8080 | Weaviate | Windows |
| 5050 | pgAdmin | Windows |
| 8081 | Adminer | Windows |

---

## 🔗 Access URLs

```
API:        http://192.168.1.100:8000/docs
Prometheus: http://192.168.1.100:9090
Grafana:    http://192.168.1.101:3000
Flower:     http://192.168.1.101:5555
Loki:       http://192.168.1.101:3100
pgAdmin:    http://192.168.1.50:5050
Adminer:    http://192.168.1.50:8081
Weaviate:   http://192.168.1.50:8080
```

---

## 🛠️ Common Commands

### Check services:
```bash
docker ps
docker-compose ps
```

### View logs:
```bash
docker logs -f uniaugment-api
docker logs -f uniaugment-postgres
docker logs -f uniaugment-weaviate
```

### Restart services:
```bash
# Arch Linux
systemctl restart uniaugment

# Windows
C:\uniaugment\start-services.bat
```

### Stop services:
```bash
# Arch Linux
systemctl stop uniaugment

# Windows
docker-compose -f C:\uniaugment\compose\docker-compose.windows.yml down
```

---

## 🔍 Troubleshooting

### Test connectivity:
```bash
# From Arch 1 to Windows
ping 192.168.1.50
psql -h 192.168.1.50 -U uniaugment -d uniaugment

# From Arch 2 to Arch 1
redis-cli -h 192.168.1.100 ping
```

### Check firewall:
```bash
# Arch Linux
sudo ufw status
sudo ufw allow 5432
sudo ufw allow 6379
sudo ufw allow 8080
```

### View resource usage:
```bash
# Arch Linux
htop

# Windows
Get-Process | Sort-Object WorkingSet -Descending | Select -First 10
```

---

## 📁 File Locations

### Arch Linux:
```
/opt/uniaugment/config/.env.distributed
/opt/uniaugment/compose/docker-compose.arch-*.yml
/opt/uniaugment/logs/
/opt/uniaugment/data/
```

### Windows:
```
C:\uniaugment\config\.env.distributed
C:\uniaugment\compose\docker-compose.windows.yml
C:\uniaugment\logs\
C:\uniaugment\data\
```

---

## 🔐 Security Checklist

- [ ] Change default passwords in `.env.distributed`
- [ ] Enable firewall on all machines
- [ ] Configure SSH keys (Arch Linux)
- [ ] Backup `.env.distributed` files
- [ ] Set up automated backups
- [ ] Enable monitoring alerts

---

## 📈 Scaling

### Add more Celery workers:
```bash
# Edit docker-compose.arch-workers.yml
# Add celery-worker-3, celery-worker-4, etc.
docker-compose up -d
```

### Add more API instances:
```bash
# On Arch 1, scale API service
docker-compose -f docker-compose.arch-api.yml up -d --scale uniaugment-api=2
```

---

## 🎯 Container Reuse

Your containers are reusable for other AI projects:

```bash
# Pull image
docker pull 192.168.1.100:5000/uniaugment:full

# Run for different project
docker run -it --rm \
  -e PROJECT_NAME=my-project \
  192.168.1.100:5000/uniaugment:full \
  python my_script.py
```

---

## 📞 Support

1. Check logs: `docker logs -f <container>`
2. Run health check: `./scripts/utils/health-check.sh`
3. Review DISTRIBUTED_SETUP_GUIDE.md
4. Check firewall rules
5. Verify network connectivity

---

## ✅ Verification Checklist

- [ ] All 3 machines running
- [ ] Docker services started
- [ ] API responding at http://192.168.1.100:8000/docs
- [ ] Database accessible from Arch machines
- [ ] Redis accessible from Arch 2
- [ ] Grafana dashboard loading
- [ ] Prometheus collecting metrics
- [ ] Weaviate responding

---

**Status**: Ready for distributed deployment!

**Next**: Start services and verify all connections.

