# 🚀 Quick Start Guide - 6 OptiPlex PC Setup

## Overview
This guide provides a quick setup process for deploying the DRYAD backend across your 6 Dell OptiPlex PCs with 8GB RAM each.

---

## ⚡ 5-Minute Setup Checklist

### Pre-requisites
- [ ] All 6 machines on same network
- [ ] Static IPs assigned: 192.168.1.100-105
- [ ] Docker installed on all machines

### Quick Setup Steps

1. **Clone or copy UniAugment files to each machine**
2. **Run setup scripts in order** (see below)
3. **Start services in order** (see below)
4. **Verify deployment** (see verification commands)

---

## 🖥️ Machine Setup Order

### Step 1: Machine 2 - Database Server (192.168.1.101)
```bash
# Linux
chmod +x UniAugment/scripts/setup-arch-linux-6machine.sh
sudo ./UniAugment/scripts/setup-arch-linux-6machine.sh

# Windows (Admin PowerShell)
powershell -ExecutionPolicy Bypass -File UniAugment\scripts\setup-windows-6machine.ps1
```
**When prompted:**
- Machine name: `optiplex-2`
- Machine IP: `192.168.1.101`
- Role: `2` (Database Server)

### Step 2: Machine 1 - API Server (192.168.1.100)
**When prompted:**
- Machine name: `optiplex-1`
- Machine IP: `192.168.1.100`
- Role: `1` (API Server)

### Step 3: Machine 3 - Worker Server (192.168.1.102)
**When prompted:**
- Machine name: `optiplex-3`
- Machine IP: `192.168.1.102`
- Role: `3` (Worker Server)

### Step 4: Machine 4 - Monitoring Server (192.168.1.103)
**When prompted:**
- Machine name: `optiplex-4`
- Machine IP: `192.168.1.103`
- Role: `4` (Monitoring Server)

### Step 5: Machine 5 - Development Server (192.168.1.104)
**When prompted:**
- Machine name: `optiplex-5`
- Machine IP: `192.168.1.104`
- Role: `5` (Development Server)

### Step 6: Machine 6 - Testing Server (192.168.1.105)
**When prompted:**
- Machine name: `optiplex-6`
- Machine IP: `192.168.1.105`
- Role: `6` (Testing Server)

---

## ▶️ Service Startup Order

**Start services in this exact order:**

1. **Machine 2** (Database): `systemctl start uniaugment` (Linux) or `start-services-6machine.bat` (Windows)
2. **Machine 1** (API): Wait 30 seconds, then start
3. **Machine 3** (Worker): Wait 10 seconds, then start
4. **Machine 4** (Monitoring): Start anytime after Machine 1
5. **Machine 5** (Development): Start anytime
6. **Machine 6** (Testing): Start anytime

---

## ✅ Quick Verification Commands

### Basic Health Check (Run on any machine)
```bash
# Test primary API
curl http://192.168.1.100:8000/health

# Test development API
curl http://192.168.1.104:8001/health

# Test QA API
curl http://192.168.1.105:8002/health

# Check running containers
docker ps | grep uniaugment
```

### Expected Results
- All health checks return `{"status":"healthy"}`
- Each machine shows 2-5 running uniaugment containers
- No error messages in logs

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Production API** | http://192.168.1.100:8000/docs | Main application |
| **Development API** | http://192.168.1.104:8001/docs | Development sandbox |
| **Testing API** | http://192.168.1.105:8002/docs | Quality assurance |
| **Monitoring** | http://192.168.1.103:3000 | System dashboards |
| **Task Monitor** | http://192.168.1.102:5555 | Background jobs |
| **Database Admin** | http://192.168.1.101:5050 | Database management |

---

## 🔧 Common Quick Fixes

### Issue: Containers not starting
```bash
# Check Docker daemon
systemctl status docker  # Linux
Get-Service docker      # Windows

# Restart Docker if needed
systemctl restart docker
```

### Issue: Network connectivity
```bash
# Test basic connectivity
ping 192.168.1.100
ping 192.168.1.101
# ... test all IPs

# Check firewall
sudo ufw status  # Linux
Get-NetFirewallRule | Where-Object Enabled -eq True  # Windows
```

### Issue: Service dependencies
```bash
# Check if database is ready
psql -h 192.168.1.101 -U uniaugment -d uniaugment -c "SELECT 1"

# Check Redis
redis-cli -h 192.168.1.100 ping
```

---

## 📊 Resource Monitoring Quick View

### Check System Resources
```bash
# Linux - check memory usage
free -h

# Windows - check memory usage
Get-WmiObject -Class Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory

# Docker resource usage
docker stats --no-stream
```

### Expected Resource Usage
- **Each machine**: 2-4GB RAM used (out of 8GB)
- **Total**: 12-24GB RAM used across 6 machines
- **Plenty of headroom** for additional services

---

## 🚀 Development Workflow Quick Start

### 1. Develop on Machine 5 (Development Server)
```bash
# Access development environment
curl http://192.168.1.104:8001/docs

# Test your changes here first
```

### 2. Test on Machine 6 (Testing Server)
```bash
# Run automated tests
curl -X POST http://192.168.1.105:8002/api/v1/qa/run-tests

# Check results
curl http://192.168.1.105:8002/api/v1/qa/test-results
```

### 3. Deploy to Machine 1 (Production)
```bash
# When tests pass, deploy to production
# (Manual process - restart production containers)
systemctl restart uniaugment  # On Machine 1
```

---

## 🔄 Daily Operations

### Morning Check
```bash
# Quick health check
curl http://192.168.1.100:8000/health
curl http://192.168.1.104:8001/health
docker ps | wc -l  # Should show ~20 containers total
```

### Evening Check
```bash
# Check for errors
docker logs --since 1h uniaugment-api | grep -i error
docker logs --since 1h uniaugment-postgres | grep -i error
```

### Weekly Maintenance
```bash
# Restart all services (maintenance window)
# On each machine:
systemctl restart uniaugment  # Linux
# OR
.\start-services-6machine.bat  # Windows
```

---

## 📞 Quick Support

### First Steps if Something Fails
1. **Check logs**: `docker logs [container-name]`
2. **Verify network**: `ping [machine-ip]`
3. **Check Docker**: `docker ps` and `docker stats`
4. **Review config**: Check `.env.6machine` files

### Common Error Messages and Solutions

**"Connection refused"**
- Check if service is running: `docker ps`
- Check firewall rules
- Verify IP addresses in config

**"Database connection failed"**
- Ensure Machine 2 (database) is running
- Check PostgreSQL logs: `docker logs uniaugment-postgres`
- Verify connection string in `.env.6machine`

**"Container restarting"**
- Check resource limits: `docker stats`
- Review application logs for errors
- Check if dependencies are available

---

## 🎯 Success Indicators

### Immediate Success (5 minutes after setup)
- [ ] All 6 machines show running Docker containers
- [ ] Health checks return "healthy"
- [ ] API documentation pages load
- [ ] No error messages in logs

### Medium-term Success (24 hours)
- [ ] Background tasks processing normally
- [ ] Monitoring dashboards showing data
- [ ] Development environment usable
- [ ] Testing environment functional

### Long-term Success (1 week)
- [ ] Stable operation with no crashes
- [ ] Development workflow established
- [ ] Testing procedures working
- [ ] Resource usage stable

---

## 📋 Next Steps After Setup

1. **Change default passwords** in `.env.6machine` files
2. **Configure backups** for important data
3. **Set up monitoring alerts**
4. **Train team members** on the 6-machine workflow
5. **Develop your application** using the development environment

---

## 💡 Pro Tips

### For Optimal Performance
- Use Machine 5 for active development work
- Use Machine 6 for continuous testing
- Monitor resource usage on Machine 4 (Grafana)
- Keep Machine 1 (production) stable - avoid direct changes

### For Troubleshooting
- Machine 4 (monitoring) is your best friend for diagnostics
- Use Machine 6 (testing) to reproduce issues safely
- Machine 5 (development) is perfect for debugging

### For Scaling
- You have plenty of RAM headroom (8GB per machine)
- Easy to add more services to any machine
- Consider adding more OptiPlex PCs if needed

---

**Remember**: This 6-machine setup provides excellent isolation between development, testing, and production environments. Take advantage of this separation to work safely and efficiently!