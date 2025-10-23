# DRYAD.AI Operations Runbook

**Last Updated:** 2025-10-13  
**Version:** 1.0  
**Status:** Production Ready

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Deployment Procedures](#2-deployment-procedures)
3. [Monitoring and Alerting](#3-monitoring-and-alerting)
4. [Troubleshooting Guide](#4-troubleshooting-guide)
5. [Backup and Recovery](#5-backup-and-recovery)
6. [Scaling Procedures](#6-scaling-procedures)
7. [Security Incident Response](#7-security-incident-response)
8. [Common Issues and Solutions](#8-common-issues-and-solutions)

---

## 1. System Architecture Overview

### 1.1 Six-Level Dependency Architecture

DRYAD.AI follows a dependency-driven architecture with 6 levels:

```
Level 5: The Lyceum (Self-Improvement)
    ↓
Level 4: The Dojo (Evaluation Framework)
    ↓
Level 3: Orchestration & HITL (Governance)
    ↓
Level 2: Archivist & Librarian (Stateful Operations)
    ↓
Level 1: Execution & Memory Agents
    ↓
Level 0: Foundation Services (Tool Registry, Memory DB, Logging)
```

### 1.2 Core Components

**Level 0: Foundation Services**
- **Tool Registry**: Manages available tools and permissions
- **Memory Database**: SQLite/PostgreSQL for persistent storage
- **Structured Logging**: Tenant-isolated logging system

**Level 1: Execution & Memory Agents**
- **Sandbox Service**: Isolated code execution environment
- **Memory Coordinator**: Routes memory operations
- **Memory Scribe**: Ingests and processes content
- **Agent Registry**: Tracks available agents and capabilities

**Level 2: Stateful Operations**
- **Archivist Agent**: Short-term memory (Redis/Mock)
- **Librarian Agent**: Long-term memory (ChromaDB/Mock)

**Level 3: Orchestration & Governance**
- **Complexity Scorer**: Analyzes task complexity
- **Decision Engine**: Routes tasks to appropriate execution mode
- **Task Force Manager**: Coordinates multi-agent workflows
- **Hybrid Orchestrator**: Main orchestration engine
- **HITL (Human-in-the-Loop)**: State management and consultation

**Level 4: The Dojo (Evaluation)**
- **Benchmark Registry**: Manages evaluation benchmarks
- **Evaluation Harness**: Executes benchmarks
- **RAG-Gym**: Specialized RAG benchmarks

**Level 5: The Lyceum (Self-Improvement)**
- **Laboratory Sandbox**: Isolated research environment
- **Professor Agent**: Conducts research and experiments
- **Budget Manager**: Controls resource allocation

### 1.3 External Dependencies

**Required Services:**
- **Database**: SQLite (development) or PostgreSQL (production)
- **Redis**: Short-term memory cache (optional, has mock fallback)
- **ChromaDB**: Vector database for long-term memory (optional, has mock fallback)

**Optional Services:**
- **Ollama**: Local LLM server
- **OpenAI/Anthropic**: Cloud LLM providers
- **Nginx**: Reverse proxy and SSL termination
- **Docker**: Containerization

### 1.4 Network Architecture

```
Internet
    ↓
Nginx (Port 443/80) - SSL/TLS Termination, Rate Limiting
    ↓
DRYAD Backend (Port 8000) - FastAPI Application
    ↓
├── PostgreSQL (Port 5432) - Primary Database
├── Redis (Port 6379) - Short-term Memory
├── ChromaDB (Port 8000) - Vector Database
└── Ollama (Port 11434) - Local LLM
```

---

## 2. Deployment Procedures

### 2.1 Pre-Deployment Checklist

- [ ] All validation scripts passing at 100%
- [ ] Environment variables configured
- [ ] SSL certificates generated (production)
- [ ] Database backups created
- [ ] Monitoring stack operational
- [ ] Rollback plan documented

### 2.2 Production Deployment

**Step 1: Prepare Environment**
```bash
# Clone repository
git clone https://github.com/your-org/DRYAD_backend.git
cd DRYAD_backend

# Copy production environment template
cp .env.production.example .env.production

# Edit environment variables
nano .env.production
```

**Step 2: Configure SSL/TLS**
```bash
# Generate SSL certificates (Let's Encrypt)
./scripts/generate-ssl-certs.sh your-domain.com

# Or use self-signed for testing
./scripts/generate-ssl-certs.sh --self-signed
```

**Step 3: Build and Deploy**
```bash
# Build production image
docker build -f Dockerfile.production -t dryad-backend:latest .

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify health
curl https://your-domain.com/health
```

**Step 4: Validate Deployment**
```bash
# Run all validation scripts
python scripts/validate_level_0.py
python scripts/validate_level_1.py
python scripts/validate_level_2.py
python scripts/validate_level_3.py
python scripts/validate_level_4.py
python scripts/validate_level_5.py

# Check system health
curl https://your-domain.com/api/v1/health/status
```

### 2.3 Rollback Procedure

**If deployment fails:**
```bash
# Stop new deployment
docker-compose -f docker-compose.production.yml down

# Restore from backup
./scripts/restore.sh <backup-timestamp>

# Start previous version
docker-compose -f docker-compose.production.yml up -d

# Verify rollback
curl https://your-domain.com/health
```

---

## 3. Monitoring and Alerting

### 3.1 Health Checks

**Primary Health Endpoint:**
```bash
GET /health
```

**Detailed Health Status:**
```bash
GET /api/v1/health/status
```

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T12:00:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "chromadb": "healthy",
    "llm": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "requests_total": 12345,
    "errors_total": 5
  }
}
```

### 3.2 Monitoring Dashboard

**Access Production Monitor:**
```bash
python scripts/monitor_production.py
```

**Key Metrics to Monitor:**
- **Request Rate**: Requests per second
- **Error Rate**: Errors per minute
- **Response Time**: P50, P95, P99 latencies
- **Memory Usage**: RSS, heap size
- **CPU Usage**: Per-core utilization
- **Database Connections**: Active, idle, max
- **LLM Latency**: Token generation speed
- **Agent Success Rate**: Workflow completion rate

### 3.3 Log Files

**Location:** `logs/`

- `gremlins_app.log` - All application logs
- `gremlins_errors.log` - Errors only
- `gremlins_access.log` - API access logs

**Viewing Logs:**
```bash
# Tail all logs
tail -f logs/gremlins_app.log

# Filter errors
tail -f logs/gremlins_errors.log

# Search for specific tenant
grep "tenant_id.*test_tenant" logs/gremlins_app.log
```

### 3.4 Alerting Rules

**Critical Alerts (Immediate Response):**
- Database connection failure
- All LLM providers unavailable
- Error rate > 10% for 5 minutes
- Memory usage > 90%
- Disk usage > 85%

**Warning Alerts (Monitor Closely):**
- Error rate > 5% for 10 minutes
- Response time P95 > 5 seconds
- Memory usage > 75%
- Disk usage > 70%
- Redis connection lost (fallback to mock)

**Info Alerts (Awareness):**
- New deployment detected
- Configuration change
- Scheduled maintenance window

---

## 4. Troubleshooting Guide

### 4.1 Service Won't Start

**Symptoms:** Container fails to start or crashes immediately

**Diagnosis:**
```bash
# Check container logs
docker logs dryad_backend

# Check environment variables
docker exec dryad_backend env | grep -E "DATABASE|REDIS|LLM"

# Verify database connectivity
docker exec dryad_backend python -c "from app.database.database import engine; engine.connect()"
```

**Common Causes:**
1. **Missing environment variables** - Check `.env.production`
2. **Database not accessible** - Verify DATABASE_URL
3. **Port already in use** - Check `netstat -tulpn | grep 8000`
4. **Insufficient permissions** - Check file ownership

### 4.2 High Error Rate

**Symptoms:** Error rate > 5% in monitoring dashboard

**Diagnosis:**
```bash
# Check recent errors
tail -100 logs/gremlins_errors.log

# Count error types
grep "ERROR" logs/gremlins_app.log | cut -d'-' -f4 | sort | uniq -c | sort -rn

# Check database errors
grep "database" logs/gremlins_errors.log
```

**Common Causes:**
1. **Database connection pool exhausted** - Increase pool size
2. **LLM timeout** - Increase timeout or switch provider
3. **Memory pressure** - Scale horizontally or increase resources
4. **Invalid requests** - Check API validation

### 4.3 Slow Response Times

**Symptoms:** P95 latency > 5 seconds

**Diagnosis:**
```bash
# Check slow queries
grep "duration.*[5-9][0-9][0-9][0-9]" logs/gremlins_app.log

# Monitor database
docker exec postgres pg_stat_statements

# Check LLM latency
grep "llm_latency" logs/gremlins_app.log | tail -20
```

**Common Causes:**
1. **Slow database queries** - Add indexes, optimize queries
2. **LLM provider slow** - Switch provider or increase timeout
3. **Memory swapping** - Increase RAM or reduce memory usage
4. **Network latency** - Check external service connectivity

### 4.4 Memory Leaks

**Symptoms:** Memory usage continuously increasing

**Diagnosis:**
```bash
# Monitor memory over time
watch -n 5 'docker stats dryad_backend --no-stream'

# Check Python memory profiling
docker exec dryad_backend python -m memory_profiler app/main.py

# Analyze heap dump
docker exec dryad_backend python -c "import gc; gc.collect(); print(len(gc.get_objects()))"
```

**Solutions:**
1. Restart service to clear memory
2. Reduce worker count if using Celery
3. Implement connection pooling limits
4. Review code for circular references

### 4.5 Database Connection Issues

**Symptoms:** "Connection refused" or "Too many connections"

**Diagnosis:**
```bash
# Check active connections
docker exec postgres psql -U dryad -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool
grep "pool" logs/gremlins_app.log | tail -20

# Test direct connection
docker exec dryad_backend python -c "from app.database.database import SessionLocal; db = SessionLocal(); print('OK')"
```

**Solutions:**
1. Increase `max_connections` in PostgreSQL
2. Reduce `SQLALCHEMY_POOL_SIZE` in environment
3. Implement connection retry logic
4. Check for connection leaks in code

---

## 5. Backup and Recovery

### 5.1 Backup Strategy

**Automated Daily Backups:**
```bash
# Schedule with cron (daily at 2 AM)
0 2 * * * /path/to/DRYAD_backend/scripts/backup.sh
```

**Manual Backup:**
```bash
# Full system backup
./scripts/backup.sh

# Database only
docker exec postgres pg_dump -U dryad dryad_db > backup_$(date +%Y%m%d).sql

# Application data
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### 5.2 Backup Retention Policy

- **Daily backups**: Keep for 7 days
- **Weekly backups**: Keep for 4 weeks
- **Monthly backups**: Keep for 12 months
- **Critical backups**: Keep indefinitely (before major upgrades)

### 5.3 Recovery Procedures

**Full System Recovery:**
```bash
# Stop services
docker-compose -f docker-compose.production.yml down

# Restore database
docker exec -i postgres psql -U dryad dryad_db < backup_20251013.sql

# Restore application data
tar -xzf data_backup_20251013.tar.gz

# Restart services
docker-compose -f docker-compose.production.yml up -d

# Verify recovery
python scripts/validate_level_0.py
```

**Point-in-Time Recovery (PostgreSQL):**
```bash
# Restore to specific timestamp
docker exec postgres pg_restore --clean --if-exists \
  --dbname=dryad_db \
  --target-time="2025-10-13 12:00:00" \
  backup_20251013.dump
```

### 5.4 Disaster Recovery

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 24 hours

**DR Checklist:**
1. [ ] Identify failure scope (database, application, infrastructure)
2. [ ] Notify stakeholders of incident
3. [ ] Activate DR team
4. [ ] Restore from most recent backup
5. [ ] Validate data integrity
6. [ ] Run all validation scripts
7. [ ] Resume normal operations
8. [ ] Conduct post-mortem analysis

---

## 6. Scaling Procedures

### 6.1 Horizontal Scaling

**Scale Backend Instances:**
```bash
# Scale to 3 instances
docker-compose -f docker-compose.production.yml up -d --scale dryad_backend=3

# Verify load balancing
curl https://your-domain.com/health
```

**Load Balancer Configuration (Nginx):**
```nginx
upstream dryad_backend {
    least_conn;
    server dryad_backend_1:8000 max_fails=3 fail_timeout=30s;
    server dryad_backend_2:8000 max_fails=3 fail_timeout=30s;
    server dryad_backend_3:8000 max_fails=3 fail_timeout=30s;
}
```

### 6.2 Vertical Scaling

**Increase Container Resources:**
```yaml
# docker-compose.production.yml
services:
  dryad_backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### 6.3 Database Scaling

**Read Replicas:**
```bash
# Configure read replica
docker run -d --name postgres_replica \
  -e POSTGRES_USER=dryad \
  -e POSTGRES_PASSWORD=<password> \
  -e POSTGRES_DB=dryad_db \
  -e POSTGRES_MASTER_HOST=postgres_primary \
  postgres:15
```

**Connection Pooling:**
```python
# Increase pool size in environment
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40
```

### 6.4 Caching Strategy

**Redis Caching:**
```bash
# Increase Redis memory
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine \
  --maxmemory 2gb \
  --maxmemory-policy allkeys-lru
```

**Application-Level Caching:**
- Enable response caching for read-heavy endpoints
- Implement query result caching
- Use CDN for static assets

---

## 7. Security Incident Response

### 7.1 Incident Classification

**Severity Levels:**
- **Critical (P0)**: Data breach, system compromise, complete outage
- **High (P1)**: Partial outage, security vulnerability, data corruption
- **Medium (P2)**: Performance degradation, minor security issue
- **Low (P3)**: Cosmetic issues, feature requests

### 7.2 Incident Response Procedure

**Step 1: Detection and Triage (0-15 minutes)**
```bash
# Check for suspicious activity
grep "401\|403\|500" logs/gremlins_access.log | tail -100

# Review recent authentication attempts
grep "authentication" logs/gremlins_app.log | tail -50

# Check for unusual patterns
grep "ERROR" logs/gremlins_errors.log | wc -l
```

**Step 2: Containment (15-60 minutes)**
```bash
# Block suspicious IPs (if identified)
iptables -A INPUT -s <suspicious-ip> -j DROP

# Rotate API keys
python scripts/security/rotate_api_keys.py

# Enable rate limiting
# Edit nginx.conf to reduce limits temporarily
```

**Step 3: Investigation (1-4 hours)**
- Review all logs for incident timeline
- Identify affected users/tenants
- Determine root cause
- Document findings

**Step 4: Remediation (4-24 hours)**
- Apply security patches
- Update vulnerable dependencies
- Implement additional security controls
- Restore from clean backup if compromised

**Step 5: Recovery (24-48 hours)**
- Gradually restore normal operations
- Monitor for recurrence
- Communicate with affected users
- Update security documentation

**Step 6: Post-Incident Review (48-72 hours)**
- Conduct post-mortem meeting
- Document lessons learned
- Update runbook and procedures
- Implement preventive measures

### 7.3 Security Contacts

**Internal:**
- Security Team: security@your-org.com
- On-Call Engineer: oncall@your-org.com
- Management: management@your-org.com

**External:**
- Cloud Provider Support: support@cloud-provider.com
- Security Vendor: vendor@security-company.com

---

## 8. Common Issues and Solutions

### 8.1 "Redis connection failed"

**Issue:** Application logs show Redis connection errors

**Solution:**
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if not running
docker start redis

# Or use mock mode (fallback)
# Set in .env: REDIS_AVAILABLE=false
```

**Impact:** Short-term memory will use mock mode (in-memory storage)

### 8.2 "LLM provider unavailable"

**Issue:** All LLM providers returning errors

**Solution:**
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check OpenAI API key
echo $OPENAI_API_KEY

# Check Anthropic API key
echo $ANTHROPIC_API_KEY

# Fallback to different provider
# Edit .env: PRIMARY_LLM_PROVIDER=ollama
```

**Impact:** AI-powered features will be degraded or unavailable

### 8.3 "Database migration failed"

**Issue:** Alembic migration fails during deployment

**Solution:**
```bash
# Check current migration version
docker exec dryad_backend alembic current

# Rollback one version
docker exec dryad_backend alembic downgrade -1

# Re-run migration
docker exec dryad_backend alembic upgrade head

# If still failing, restore from backup
./scripts/restore.sh <backup-timestamp>
```

### 8.4 "Validation script failing"

**Issue:** Level validation scripts not passing 100%

**Solution:**
```bash
# Run specific level validation
python scripts/validate_level_1.py

# Check detailed error output
python scripts/validate_level_1.py 2>&1 | tee validation.log

# Fix identified issues
# Re-run validation
python scripts/validate_level_1.py
```

**Impact:** System may have degraded functionality

### 8.5 "High memory usage"

**Issue:** Container using > 90% memory

**Solution:**
```bash
# Check memory usage
docker stats dryad_backend --no-stream

# Restart container to clear memory
docker restart dryad_backend

# Increase memory limit
# Edit docker-compose.production.yml
# memory: 8G

# Scale horizontally instead
docker-compose -f docker-compose.production.yml up -d --scale dryad_backend=2
```

### 8.6 "SSL certificate expired"

**Issue:** HTTPS connections failing with certificate error

**Solution:**
```bash
# Check certificate expiration
openssl x509 -in /etc/nginx/ssl/cert.pem -noout -dates

# Renew Let's Encrypt certificate
certbot renew

# Or regenerate self-signed
./scripts/generate-ssl-certs.sh --self-signed

# Reload Nginx
docker exec nginx nginx -s reload
```

---

## Appendix A: Emergency Contacts

**On-Call Rotation:**
- Primary: oncall-primary@your-org.com
- Secondary: oncall-secondary@your-org.com
- Escalation: management@your-org.com

**Vendor Support:**
- Cloud Provider: 1-800-XXX-XXXX
- Database Support: support@postgres.com
- Security Vendor: security@vendor.com

---

## Appendix B: Useful Commands

**Quick Health Check:**
```bash
curl https://your-domain.com/health && echo "OK" || echo "FAIL"
```

**View Recent Errors:**
```bash
tail -50 logs/gremlins_errors.log
```

**Restart All Services:**
```bash
docker-compose -f docker-compose.production.yml restart
```

**Check Disk Space:**
```bash
df -h | grep -E "/$|/data"
```

**Monitor Real-Time Logs:**
```bash
docker-compose -f docker-compose.production.yml logs -f --tail=100
```

---

## Appendix C: Validation Checklist

**Pre-Deployment:**
- [ ] All Level 0-5 validation scripts passing at 100%
- [ ] No deprecation warnings in logs
- [ ] All environment variables configured
- [ ] SSL certificates valid
- [ ] Backup created and verified
- [ ] Monitoring dashboard operational

**Post-Deployment:**
- [ ] Health endpoint returning 200 OK
- [ ] All services started successfully
- [ ] No errors in logs (first 5 minutes)
- [ ] Sample API requests working
- [ ] Monitoring metrics being collected
- [ ] Alerts configured and tested

---

**Document Version:** 1.0
**Last Reviewed:** 2025-10-13
**Next Review:** 2025-11-13
**Owner:** DevOps Team

