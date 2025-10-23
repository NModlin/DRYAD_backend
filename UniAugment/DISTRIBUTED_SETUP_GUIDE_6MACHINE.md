# 🖥️ UniAugment 6-Machine Distributed Setup Guide

## Your Hardware Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Machine 1 (192.168.1.100) - Primary API Server                        │
│  ├─ FastAPI Application (Port 8000)                                    │
│  ├─ Redis Cache (Port 6379)                                            │
│  └─ Prometheus Monitoring (Port 9090)                                  │
│                                                                         │
│  Machine 2 (192.168.1.101) - Database Server                           │
│  ├─ PostgreSQL Database (Port 5432)                                    │
│  ├─ Weaviate Vector DB (Port 8080)                                     │
│  └─ pgAdmin (Port 5050)                                                │
│                                                                         │
│  Machine 3 (192.168.1.102) - Worker Server                             │
│  ├─ Celery Workers (4 workers)                                         │
│  └─ Flower Task Monitor (Port 5555)                                    │
│                                                                         │
│  Machine 4 (192.168.1.103) - Monitoring Server                         │
│  ├─ Grafana Dashboards (Port 3000)                                     │
│  └─ Loki Log Aggregation (Port 3100)                                   │
│                                                                         │
│  Machine 5 (192.168.1.104) - Development Server                        │
│  ├─ Development API (Port 8001)                                        │
│  ├─ Test Database (Port 5433)                                          │
│  └─ Development tools                                                  │
│                                                                         │
│  Machine 6 (192.168.1.105) - Testing Server                            │
│  ├─ QA API (Port 8002)                                                 │
│  ├─ Automated testing tools                                            │
│  └─ Staging environment                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Setup Checklist

- [ ] All 6 machines are on the same network
- [ ] All machines have static IP addresses assigned (192.168.1.100-105)
- [ ] Docker is installed on all machines (or will be installed by script)
- [ ] SSH access configured (for Linux machines)
- [ ] Windows machines have Docker Desktop installed (or will be installed by script)
- [ ] Firewall rules allow inter-machine communication
- [ ] Scripts have execute permissions (Linux machines)

---

## 🚀 Step 1: Setup Machine 1 - Primary API Server

### On Machine 1 (Linux or Windows):

**For Linux:**
```bash
# Make script executable
chmod +x UniAugment/scripts/setup-arch-linux-6machine.sh

# Run as root
sudo ./UniAugment/scripts/setup-arch-linux-6machine.sh
```

**For Windows:**
```powershell
# Run PowerShell as Administrator
powershell -ExecutionPolicy Bypass -File UniAugment\scripts\setup-windows-6machine.ps1
```

**When prompted:**
- Machine name: `optiplex-1`
- Machine IP: `192.168.1.100`
- Machine 1 (API): `192.168.1.100`
- Machine 2 (DB): `192.168.1.101`
- Machine 3 (Worker): `192.168.1.102`
- Machine 4 (Monitor): `192.168.1.103`
- Machine 5 (Dev): `192.168.1.104`
- Machine 6 (Test): `192.168.1.105`
- Role: `1` (Primary API Server + Redis + Prometheus)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.api-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## 🗄️ Step 2: Setup Machine 2 - Database Server

### On Machine 2 (Linux or Windows):

**When prompted:**
- Machine name: `optiplex-2`
- Machine IP: `192.168.1.101`
- Role: `2` (Database Server - PostgreSQL + Weaviate)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.database-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## ⚙️ Step 3: Setup Machine 3 - Worker Server

### On Machine 3 (Linux or Windows):

**When prompted:**
- Machine name: `optiplex-3`
- Machine IP: `192.168.1.102`
- Role: `3` (Worker Server - Celery Workers + Flower)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.worker-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## 📊 Step 4: Setup Machine 4 - Monitoring Server

### On Machine 4 (Linux or Windows):

**When prompted:**
- Machine name: `optiplex-4`
- Machine IP: `192.168.1.103`
- Role: `4` (Monitoring Server - Grafana + Loki)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.monitoring-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## 💻 Step 5: Setup Machine 5 - Development Server

### On Machine 5 (Linux or Windows):

**When prompted:**
- Machine name: `optiplex-5`
- Machine IP: `192.168.1.104`
- Role: `5` (Development Server - Dev API + Test DB)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.development-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## 🧪 Step 6: Setup Machine 6 - Testing Server

### On Machine 6 (Linux or Windows):

**When prompted:**
- Machine name: `optiplex-6`
- Machine IP: `192.168.1.105`
- Role: `6` (Testing Server - QA API + Testing Tools)

✅ **The script will automatically:**
- Install Docker and Docker Compose
- Create all directories
- Generate `docker-compose.testing-6machine.yml`
- Create environment files
- Set up systemd service (Linux) or Task Scheduler (Windows)

---

## 📁 Step 7: Docker Compose Files (Auto-Generated!)

**Good news!** The setup scripts automatically generate the docker-compose files for you. No need to copy them manually!

### What the scripts generate:

**On each machine:**
- ✅ Appropriate `docker-compose.*-6machine.yml` file for the selected role
- ✅ All necessary directories and configuration files
- ✅ Environment file with 6-machine network configuration

---

## 🔧 Step 8: Configure Environment Variables

### On All Machines:

Edit the `.env.6machine` file created during setup:

```bash
# Linux
nano /opt/uniaugment/config/.env.6machine

# Windows
notepad C:\uniaugment\config\.env.6machine
```

**Key variables to update:**
```
DATABASE_URL=postgresql://uniaugment:YOUR_PASSWORD@192.168.1.101:5432/uniaugment
TEST_DATABASE_URL=postgresql://uniaugment:YOUR_PASSWORD@192.168.1.104:5433/uniaugment-dev
REDIS_URL=redis://192.168.1.100:6379/0
CELERY_BROKER_URL=redis://192.168.1.100:6379/0
WEAVIATE_URL=http://192.168.1.101:8080
JWT_SECRET_KEY=your-secret-key-here
POSTGRES_PASSWORD=your-db-password-here
```

---

## 🐳 Step 9: Build Docker Images

### On Machine 1 (API Server):

```bash
# Build the full stack image
cd UniAugment
docker build -f docker/full/Dockerfile -t uniaugment:full .

# Tag for distribution
docker tag uniaugment:full localhost:5000/uniaugment:full
```

### Push to all machines:

```bash
# On Machine 1 (API Server)
docker run -d -p 5000:5000 registry:2

# On other machines
docker pull 192.168.1.100:5000/uniaugment:full
```

---

## ▶️ Step 10: Start Services

### Start in this order:

1. **Machine 2 (Database Server) - Start First:**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

2. **Machine 1 (API Server):**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

3. **Machine 3 (Worker Server):**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

4. **Machine 4 (Monitoring Server):**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

5. **Machine 5 (Development Server):**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

6. **Machine 6 (Testing Server):**
```bash
# Linux
systemctl start uniaugment

# Windows
C:\uniaugment\start-services-6machine.bat
```

---

## ✅ Step 11: Verify Deployment

### Check all services:

```bash
# On each machine
docker ps

# Check logs
docker logs uniaugment-api
docker logs uniaugment-postgres
docker logs uniaugment-dev-api
docker logs uniaugment-qa-api
```

### Test connectivity:

```bash
# From any machine, test primary API
curl http://192.168.1.100:8000/docs

# Test development API
curl http://192.168.1.104:8001/docs

# Test QA API
curl http://192.168.1.105:8002/docs

# Test database connectivity
psql -h 192.168.1.101 -U uniaugment -d uniaugment

# Test Redis
redis-cli -h 192.168.1.100 ping
```

---

## 🌐 Access Services

| Service | URL | Machine | Purpose |
|---------|-----|---------|---------|
| **Primary API Docs** | http://192.168.1.100:8000/docs | Machine 1 | Production API |
| **Development API Docs** | http://192.168.1.104:8001/docs | Machine 5 | Development environment |
| **QA API Docs** | http://192.168.1.105:8002/docs | Machine 6 | Testing environment |
| **Prometheus** | http://192.168.1.100:9090 | Machine 1 | Metrics collection |
| **Grafana** | http://192.168.1.103:3000 | Machine 4 | Monitoring dashboards |
| **Test Dashboard** | http://192.168.1.105:3001 | Machine 6 | Test results |
| **Flower** | http://192.168.1.102:5555 | Machine 3 | Task monitoring |
| **Loki** | http://192.168.1.103:3100 | Machine 4 | Log aggregation |
| **pgAdmin** | http://192.168.1.101:5050 | Machine 2 | Database administration |

---

## 💻 Development/Testing Workflow

### Development Workflow:
1. **Code changes** on your local machine
2. **Test locally** with development environment (Machine 5)
3. **Run automated tests** on testing environment (Machine 6)
4. **Deploy to production** when tests pass

### Testing Capabilities:
- **Unit tests**: Run on development server
- **Integration tests**: Test interactions between services
- **Load testing**: Simulate high traffic
- **Security scanning**: Automated security tests
- **Performance monitoring**: Real-time performance metrics

### Environment Isolation:
- **Development**: Isolated from production
- **Testing**: Separate database and services
- **Production**: Stable, production-ready environment

---

## 🔄 Development Lifecycle

```
Local Development → Machine 5 (Dev) → Machine 6 (Test) → Machine 1 (Production)
     ↓                  ↓                  ↓                  ↓
   Code        →   Development   →   Testing/QA   →   Production
   Changes           API 8001          API 8002          API 8000
```

---

## 📈 Resource Monitoring

### Monitor resource usage across all 6 machines:

```bash
# Check memory usage
docker stats

# View logs
docker-compose logs -f

# Monitor network traffic
# Linux: nethogs
# Windows: Get-NetTCPConnection
```

### Expected Resource Usage:
- **Machine 1**: 2-3GB RAM (API + Redis + Prometheus)
- **Machine 2**: 3-4GB RAM (PostgreSQL + Weaviate)
- **Machine 3**: 1-2GB RAM (Celery workers)
- **Machine 4**: 1-2GB RAM (Grafana + Loki)
- **Machine 5**: 2-3GB RAM (Development environment)
- **Machine 6**: 2-3GB RAM (Testing environment)

**Total**: 11-17GB RAM used, leaving significant headroom

---

## 🛠️ Troubleshooting

### Services won't connect:
```bash
# Check network connectivity
ping 192.168.1.100
ping 192.168.1.101
ping 192.168.1.102
ping 192.168.1.103
ping 192.168.1.104
ping 192.168.1.105

# Check firewall rules
# Linux: sudo ufw status
# Windows: Get-NetFirewallRule
```

### Database connection fails:
```bash
# Test from any machine
psql -h 192.168.1.101 -U uniaugment -d uniaugment -c "SELECT 1"

# Check PostgreSQL logs
docker logs uniaugment-postgres
```

### Development/Testing issues:
```bash
# Check development environment
curl http://192.168.1.104:8001/health

# Check testing environment
curl http://192.168.1.105:8002/health

# View test results
docker logs uniaugment-test-runner
```

---

## 🔐 Security Notes

1. **Change default passwords** in `.env.6machine`
2. **Enable firewall** on all machines
3. **Use VPN** for remote access
4. **Backup credentials** securely
5. **Rotate JWT secrets** regularly
6. **Monitor access logs** for suspicious activity

---

## 📊 Development Benefits

### Parallel Development:
- Multiple developers can work simultaneously
- Isolated development environments
- No conflicts between development and production

### Testing Advantages:
- Comprehensive test suite automation
- Load testing capabilities
- Security scanning integration
- Performance monitoring

### Resource Optimization:
- Distributed processing across 6 machines
- 8GB RAM per machine provides ample resources
- Easy scaling by adding more machines

---

## 🎯 Next Steps

1. ✅ Complete all 6-machine setup steps
2. ✅ Verify all services are running
3. ✅ Test development environment (Machine 5)
4. ✅ Run automated tests (Machine 6)
5. ✅ Configure monitoring dashboards (Machine 4)
6. ✅ Set up backup schedule
7. ✅ Create development workflow documentation
8. ✅ Train team on 6-machine deployment

---

**Status**: Ready for 6-machine distributed deployment with full development/testing capabilities!

**Features Available**:
- ✅ **Production API**: Stable, production-ready environment
- ✅ **Development Environment**: Isolated development sandbox
- ✅ **Testing Environment**: Comprehensive testing capabilities
- ✅ **Monitoring**: Real-time system monitoring
- ✅ **Distributed Processing**: Background task processing
- ✅ **Database Services**: Centralized data storage

**Total API Endpoints**: 3 separate environments (Production, Development, Testing)

**Support**: Check logs and use health-check scripts for troubleshooting.