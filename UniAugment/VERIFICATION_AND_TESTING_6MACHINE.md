# ✅ Verification and Testing Procedures for 6-Machine Setup

## Overview
This document provides comprehensive verification and testing procedures to ensure your 6-machine DRYAD backend deployment is functioning correctly.

---

## 📋 Pre-Verification Checklist

### Network Connectivity
- [ ] All 6 machines can ping each other
- [ ] Firewall rules allow required ports
- [ ] Static IP addresses are correctly assigned

### Docker Setup
- [ ] Docker is running on all machines
- [ ] Docker Compose is installed
- [ ] Overlay network `uniaugment-6machine` exists

### Service Health
- [ ] All containers are running
- [ ] No container restarts due to errors
- [ ] Health checks are passing

---

## 🔍 Step 1: Network Connectivity Verification

### Test Inter-Machine Communication
```bash
# From each machine, test connectivity to all others
ping 192.168.1.100  # Machine 1
ping 192.168.1.101  # Machine 2
ping 192.168.1.102  # Machine 3
ping 192.168.1.103  # Machine 4
ping 192.168.1.104  # Machine 5
ping 192.168.1.105  # Machine 6
```

### Test Port Accessibility
```bash
# Test key service ports
nc -zv 192.168.1.100 8000  # Primary API
nc -zv 192.168.1.100 6379  # Redis
nc -zv 192.168.1.100 9090  # Prometheus
nc -zv 192.168.1.101 5432  # PostgreSQL
nc -zv 192.168.1.101 8080  # Weaviate
nc -zv 192.168.1.102 5555  # Flower
nc -zv 192.168.1.103 3000  # Grafana
nc -zv 192.168.1.103 3100  # Loki
nc -zv 192.168.1.104 8001  # Development API
nc -zv 192.168.1.104 5433  # Test Database
nc -zv 192.168.1.105 8002  # QA API
nc -zv 192.168.1.105 3001  # Test Dashboard
```

---

## 🐳 Step 2: Docker Service Verification

### Check Running Containers on Each Machine
```bash
# Machine 1 - API Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-api
# uniaugment-redis
# uniaugment-prometheus
# uniaugment-node-exporter

# Machine 2 - Database Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-postgres
# uniaugment-weaviate
# uniaugment-pgadmin

# Machine 3 - Worker Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-celery-worker-1
# uniaugment-celery-worker-2
# uniaugment-flower

# Machine 4 - Monitoring Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-grafana
# uniaugment-loki
# uniaugment-promtail

# Machine 5 - Development Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-dev-api
# uniaugment-postgres-dev
# uniaugment-dev-tools
# uniaugment-code-watcher
# uniaugment-test-runner

# Machine 6 - Testing Server
docker ps | grep uniaugment

# Expected containers:
# uniaugment-qa-api
# uniaugment-load-tester
# uniaugment-integration-tester
# uniaugment-security-scanner
# uniaugment-performance-monitor
# uniaugment-test-dashboard
# uniaugment-test-aggregator
```

### Check Container Health
```bash
# Check health status of all containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check logs for errors
docker logs uniaugment-api --tail 50
docker logs uniaugment-postgres --tail 50
docker logs uniaugment-dev-api --tail 50
docker logs uniaugment-qa-api --tail 50
```

---

## 🌐 Step 3: API Endpoint Verification

### Test Primary API (Machine 1)
```bash
# Health check
curl -s http://192.168.1.100:8000/health | jq .

# API documentation
curl -s http://192.168.1.100:8000/docs

# Test agent creation (if Agent Studio enabled)
curl -X POST http://192.168.1.100:8000/api/v1/agents/test-agent/visual \
  -H "Content-Type: application/json" \
  -d '{"avatar_style": "abstract"}' | jq .
```

### Test Development API (Machine 5)
```bash
# Health check
curl -s http://192.168.1.104:8001/health | jq .

# API documentation
curl -s http://192.168.1.104:8001/docs

# Test with development-specific endpoints
curl -s http://192.168.1.104:8001/api/v1/debug/info | jq .
```

### Test QA API (Machine 6)
```bash
# Health check
curl -s http://192.168.1.105:8002/health | jq .

# API documentation
curl -s http://192.168.1.105:8002/docs

# Test QA-specific endpoints
curl -s http://192.168.1.105:8002/api/v1/qa/status | jq .
```

---

## 🗄️ Step 4: Database Connectivity Verification

### Test PostgreSQL Connections
```bash
# Test production database (Machine 2)
psql -h 192.168.1.101 -U uniaugment -d uniaugment -c "SELECT version();"

# Test development database (Machine 5)
psql -h 192.168.1.104 -U uniaugment -d uniaugment-dev -c "SELECT version();"

# Test from API containers
docker exec uniaugment-api python -c "
import psycopg2
conn = psycopg2.connect('postgresql://uniaugment:password@192.168.1.101:5432/uniaugment')
print('Database connection successful')
conn.close()
"
```

### Test Weaviate Connectivity
```bash
# Test Weaviate health
curl -s http://192.168.1.101:8080/v1/.well-known/ready | jq .

# Test from API containers
docker exec uniaugment-api python -c "
import requests
response = requests.get('http://192.168.1.101:8080/v1/.well-known/ready')
print(f'Weaviate health: {response.status_code}')
"
```

### Test Redis Connectivity
```bash
# Test Redis connection
redis-cli -h 192.168.1.100 ping

# Test from worker containers
docker exec uniaugment-celery-worker-1 python -c "
import redis
r = redis.Redis(host='192.168.1.100', port=6379, password='password')
print(f'Redis ping: {r.ping()}')
"
```

---

## ⚙️ Step 5: Background Processing Verification

### Test Celery Workers (Machine 3)
```bash
# Check Flower dashboard
curl -s http://192.168.1.102:5555

# Test task submission
docker exec uniaugment-api python -c "
from src.core.celery_app import test_task
result = test_task.delay('verification')
print(f'Task ID: {result.id}')
"

# Check task status in Flower
# Visit http://192.168.1.102:5555 to see active tasks
```

### Test Development Tools (Machine 5)
```bash
# Check development tools status
docker logs uniaugment-dev-tools --tail 20

# Check code watcher
docker logs uniaugment-code-watcher --tail 20

# Run test suite
docker exec uniaugment-test-runner python -m pytest /app/tests/test_basic.py -v
```

---

## 📊 Step 6: Monitoring System Verification

### Test Prometheus (Machine 1)
```bash
# Check Prometheus metrics
curl -s http://192.168.1.100:9090/api/v1/query?query=up | jq .

# Check node exporter
curl -s http://192.168.1.100:9100/metrics | head -20
```

### Test Grafana (Machine 4)
```bash
# Check Grafana health
curl -s http://192.168.1.103:3000/api/health | jq .

# Access dashboard: http://192.168.1.103:3000
# Login: admin/admin (change password after first login)
```

### Test Loki (Machine 4)
```bash
# Check Loki health
curl -s http://192.168.1.103:3100/ready | jq .

# Check logs in Grafana Loki datasource
```

### Test Test Dashboard (Machine 6)
```bash
# Check test dashboard
curl -s http://192.168.1.105:3001/api/health | jq .

# Access: http://192.168.1.105:3001
```

---

## 🧪 Step 7: Testing Environment Verification

### Run Automated Tests (Machine 6)
```bash
# Test load testing
docker exec uniaugment-load-tester python -c "
from src.services.load_tester import run_basic_test
result = run_basic_test()
print(f'Load test result: {result}')
"

# Test integration testing
docker exec uniaugment-integration-tester python -c "
from src.services.integration_tester import run_basic_integration_test
result = run_basic_integration_test()
print(f'Integration test result: {result}')
"

# Test security scanning
docker exec uniaugment-security-scanner python -c "
from src.services.security_scanner import run_basic_scan
result = run_basic_scan()
print(f'Security scan result: {result}')
"
```

### Check Test Results Aggregation
```bash
# Check test aggregator
docker logs uniaugment-test-aggregator --tail 20

# Check performance monitoring
docker logs uniaugment-performance-monitor --tail 20
```

---

## 🔄 Step 8: Cross-Environment Testing

### Test Environment Isolation
```bash
# Ensure development doesn't affect production
curl -s http://192.168.1.104:8001/api/v1/agents | jq '. | length'
curl -s http://192.168.1.100:8000/api/v1/agents | jq '. | length'

# These should return different results if environments are isolated
```

### Test Data Separation
```bash
# Create test data in development
curl -X POST http://192.168.1.104:8001/api/v1/agents/dev-test \
  -H "Content-Type: application/json" \
  -d '{"name": "dev-test-agent"}'

# Verify it doesn't appear in production
curl -s http://192.168.1.100:8000/api/v1/agents/dev-test | jq '.error'

# Should return an error (not found)
```

### Test Service Intercommunication
```bash
# Test that services can communicate across machines
docker exec uniaugment-qa-api python -c "
import requests
# Test connection to primary API
response = requests.get('http://192.168.1.100:8000/health')
print(f'Primary API health: {response.status_code}')

# Test connection to development API
response = requests.get('http://192.168.1.104:8001/health')
print(f'Development API health: {response.status_code}')
"
```

---

## 📈 Step 9: Performance Verification

### Check Resource Usage
```bash
# Check memory usage across all machines
docker stats --no-stream

# Check CPU usage
# Linux: top or htop
# Windows: Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Check disk usage
df -h  # Linux
Get-PSDrive  # Windows
```

### Test Load Handling
```bash
# Simple load test from any machine
for i in {1..10}; do
    curl -s http://192.168.1.100:8000/health > /dev/null &
done
wait

# Check response times
time curl -s http://192.168.1.100:8000/health > /dev/null
```

---

## 🛡️ Step 10: Security Verification

### Test Authentication
```bash
# Test JWT authentication
curl -s http://192.168.1.100:8000/api/v1/protected-endpoint \
  -H "Authorization: Bearer invalid-token" | jq '.detail'

# Should return authentication error
```

### Test Firewall Rules
```bash
# Test that only required ports are open
nmap -p 8000,8001,8002,5432,5433,6379,8080,9090,3000,3001,3100,5555,5050 192.168.1.100-105

# Only the specified ports should be open
```

### Test Backup Systems
```bash
# Check backup service (if configured)
docker logs uniaugment-backup --tail 20
```

---

## 📝 Step 11: Documentation and Logging Verification

### Check Log Aggregation
```bash
# Check if logs are being aggregated properly
docker logs uniaugment-promtail --tail 20

# Check Loki for log entries
curl -s http://192.168.1.103:3100/loki/api/v1/query?query={container=\"uniaugment-api\"} | jq '.data.result[0].values[0]'
```

### Verify Configuration Files
```bash
# Check environment files on each machine
# Machine 1
cat /opt/uniaugment/config/.env.6machine | grep -v PASSWORD

# Machine 2
cat /opt/uniaugment/config/.env.6machine | grep -v PASSWORD

# Repeat for all machines...
```

---

## 🎯 Success Criteria

### Minimum Success Criteria
- [ ] All 6 machines can communicate with each other
- [ ] All Docker containers are running without errors
- [ ] Primary API responds to health checks
- [ ] Development and QA APIs are accessible
- [ ] Database connections work from all machines
- [ ] Background processing is functional
- [ ] Monitoring systems are collecting data

### Optimal Success Criteria
- [ ] All automated tests pass
- [ ] Load testing completes successfully
- [ ] Security scans show no critical issues
- [ ] Performance meets expectations (<2s response time)
- [ ] Resource usage is within acceptable limits
- [ ] Log aggregation is working correctly

---

## 🔄 Continuous Verification

### Daily Health Checks
```bash
#!/bin/bash
# daily-health-check.sh

echo "=== Daily Health Check ==="
echo "Timestamp: $(date)"

# Test primary API
curl -s http://192.168.1.100:8000/health | jq '.status' || echo "Primary API FAILED"

# Test development API
curl -s http://192.168.1.104:8001/health | jq '.status' || echo "Development API FAILED"

# Test database connectivity
psql -h 192.168.1.101 -U uniaugment -d uniaugment -c "SELECT 1" > /dev/null || echo "Database FAILED"

echo "=== Health Check Complete ==="
```

### Weekly Comprehensive Test
```bash
#!/bin/bash
# weekly-comprehensive-test.sh

echo "=== Weekly Comprehensive Test ==="
echo "Timestamp: $(date)"

# Run full test suite on testing environment
curl -X POST http://192.168.1.105:8002/api/v1/qa/run-full-test-suite

# Check results after completion
sleep 60
curl -s http://192.168.1.105:8002/api/v1/qa/test-results | jq .

echo "=== Weekly Test Complete ==="
```

---

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

**Issue**: Containers failing to start
**Solution**: Check Docker logs and ensure all dependencies are running

**Issue**: Network connectivity problems
**Solution**: Verify firewall rules and IP addresses

**Issue**: Database connection failures
**Solution**: Check PostgreSQL logs and connection strings

**Issue**: High resource usage
**Solution**: Monitor with Grafana and adjust resource limits

**Issue**: Test failures
**Solution**: Check test logs and environment configuration

---

## 📞 Support

If you encounter issues during verification:
1. Check the logs: `docker logs [container-name]`
2. Review configuration files
3. Test network connectivity
4. Consult the main setup guide
5. Check monitoring dashboards for insights

**Remember**: The 6-machine setup provides excellent isolation and redundancy. Most issues can be resolved by restarting individual services without affecting the entire system.