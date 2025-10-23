# Task 2-30: SSL/TLS Certificate Management

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** HIGH  
**Estimated Hours:** 3 hours

---

## 📋 OVERVIEW

Implement automated SSL/TLS certificate management using Let's Encrypt with automatic renewal, certificate monitoring, and secure storage.

---

## 🎯 OBJECTIVES

1. Set up Let's Encrypt with Certbot
2. Configure automatic certificate renewal
3. Implement certificate monitoring
4. Set up certificate expiry alerts
5. Configure nginx for SSL/TLS
6. Test certificate renewal process

---

## 📊 CURRENT STATE

**Existing:**
- HTTP-only configuration
- No SSL/TLS certificates
- No certificate management

**Gaps:**
- No HTTPS support
- No certificate automation
- No certificate monitoring
- No renewal process

---

## 🔧 IMPLEMENTATION

### 1. Certbot Setup with Docker

Create `docker/certbot/Dockerfile`:

```dockerfile
FROM certbot/certbot:latest

# Install renewal hooks
COPY renewal-hooks /etc/letsencrypt/renewal-hooks/

# Make hooks executable
RUN chmod +x /etc/letsencrypt/renewal-hooks/deploy/*.sh
```

---

### 2. Certificate Renewal Script

Create `scripts/ssl/renew-certificates.sh`:

```bash
#!/bin/bash
#
# SSL Certificate Renewal Script
#
# Automatically renews Let's Encrypt certificates

set -e

DOMAIN="${DOMAIN:-dryad.ai}"
EMAIL="${SSL_EMAIL:-admin@dryad.ai}"
WEBROOT="/var/www/certbot"

echo "🔐 Starting certificate renewal for ${DOMAIN}"

# Run certbot renewal
docker run --rm \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    -v "/var/www/certbot:/var/www/certbot" \
    certbot/certbot renew \
    --webroot \
    --webroot-path=${WEBROOT} \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    --quiet

# Reload nginx if certificates were renewed
if [ $? -eq 0 ]; then
    echo "✅ Certificates renewed successfully"
    docker exec dryad-nginx nginx -s reload
    echo "✅ Nginx reloaded"
else
    echo "❌ Certificate renewal failed"
    exit 1
fi
```

---

### 3. Initial Certificate Acquisition

Create `scripts/ssl/init-certificates.sh`:

```bash
#!/bin/bash
#
# Initial SSL Certificate Setup
#
# Obtains initial Let's Encrypt certificates

set -e

DOMAIN="${DOMAIN:-dryad.ai}"
EMAIL="${SSL_EMAIL:-admin@dryad.ai}"
STAGING="${STAGING:-0}"

echo "🔐 Obtaining SSL certificates for ${DOMAIN}"

# Use staging for testing
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
    echo "⚠️  Using Let's Encrypt staging environment"
else
    STAGING_ARG=""
fi

# Create webroot directory
mkdir -p /var/www/certbot

# Obtain certificate
docker run --rm \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    -v "/var/www/certbot:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    ${STAGING_ARG} \
    -d ${DOMAIN} \
    -d www.${DOMAIN}

if [ $? -eq 0 ]; then
    echo "✅ Certificates obtained successfully"
    echo "📁 Certificates stored in /etc/letsencrypt/live/${DOMAIN}/"
else
    echo "❌ Failed to obtain certificates"
    exit 1
fi
```

---

### 4. Nginx SSL Configuration

Create `docker/nginx/ssl.conf`:

```nginx
# SSL Configuration

# SSL protocols and ciphers
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;

# SSL session cache
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

Update `docker/nginx/nginx.conf`:

```nginx
server {
    listen 80;
    server_name dryad.ai www.dryad.ai;
    
    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name dryad.ai www.dryad.ai;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/dryad.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dryad.ai/privkey.pem;
    
    # Include SSL configuration
    include /etc/nginx/ssl.conf;
    
    # Application proxy
    location / {
        proxy_pass http://gremlins-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### 5. Certificate Monitoring

Create `app/core/ssl_monitor.py`:

```python
"""
SSL Certificate Monitoring

Monitor certificate expiry and send alerts.
"""
from __future__ import annotations

import ssl
import socket
from datetime import datetime, timedelta
from pathlib import Path
import logging
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class SSLCertificateMonitor:
    """Monitor SSL certificate expiry."""
    
    def __init__(self, cert_path: str = "/etc/letsencrypt/live"):
        self.cert_path = Path(cert_path)
    
    def check_certificate_expiry(self, domain: str) -> dict[str, any]:
        """
        Check certificate expiry for domain.
        
        Args:
            domain: Domain name
        
        Returns:
            Certificate information
        """
        cert_file = self.cert_path / domain / "fullchain.pem"
        
        if not cert_file.exists():
            logger.error(f"Certificate not found: {cert_file}")
            return {"error": "Certificate not found"}
        
        # Load certificate
        with open(cert_file, "rb") as f:
            cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        
        # Get expiry date
        expiry_date = cert.not_valid_after
        days_until_expiry = (expiry_date - datetime.now()).days
        
        # Determine status
        if days_until_expiry < 0:
            status = "expired"
        elif days_until_expiry < 7:
            status = "critical"
        elif days_until_expiry < 30:
            status = "warning"
        else:
            status = "ok"
        
        return {
            "domain": domain,
            "expiry_date": expiry_date.isoformat(),
            "days_until_expiry": days_until_expiry,
            "status": status,
            "issuer": cert.issuer.rfc4514_string(),
            "subject": cert.subject.rfc4514_string()
        }
    
    def check_all_certificates(self) -> list[dict]:
        """
        Check all certificates.
        
        Returns:
            List of certificate information
        """
        results = []
        
        if not self.cert_path.exists():
            logger.warning(f"Certificate path not found: {self.cert_path}")
            return results
        
        for domain_dir in self.cert_path.iterdir():
            if domain_dir.is_dir():
                result = self.check_certificate_expiry(domain_dir.name)
                results.append(result)
        
        return results


# Global monitor instance
ssl_monitor = SSLCertificateMonitor()
```

---

### 6. Certificate Expiry Endpoint

Create `app/api/v1/endpoints/ssl.py`:

```python
"""
SSL Certificate Endpoints

Monitor SSL certificate status.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.ssl_monitor import ssl_monitor

router = APIRouter()


class CertificateStatus(BaseModel):
    """Certificate status response."""
    domain: str
    expiry_date: str
    days_until_expiry: int
    status: str


@router.get("/ssl/status", response_model=list[CertificateStatus])
async def get_ssl_status():
    """Get SSL certificate status for all domains."""
    return ssl_monitor.check_all_certificates()
```

---

### 7. Cron Job for Renewal

Create `docker/cron/certbot-renew`:

```cron
# Renew certificates twice daily
0 0,12 * * * /app/scripts/ssl/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Let's Encrypt certificates obtained
- [ ] Automatic renewal configured
- [ ] Certificate monitoring implemented
- [ ] Expiry alerts configured
- [ ] Nginx SSL/TLS configured
- [ ] HTTPS working in production
- [ ] Certificate renewal tested

---

## 🧪 TESTING

```bash
# Test certificate acquisition (staging)
STAGING=1 ./scripts/ssl/init-certificates.sh

# Test certificate renewal
./scripts/ssl/renew-certificates.sh

# Test HTTPS connection
curl -I https://dryad.ai

# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/dryad.ai/fullchain.pem -noout -dates
```

---

## 📝 NOTES

- Use staging environment for testing
- Renew certificates before 30 days expiry
- Monitor certificate expiry daily
- Keep backup of certificates
- Test renewal process regularly


