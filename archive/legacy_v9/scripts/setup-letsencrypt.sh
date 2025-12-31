#!/bin/bash
# ============================================================================
# Let's Encrypt SSL Certificate Setup Script for DRYAD.AI Backend
# Obtains and configures SSL certificates from Let's Encrypt
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
STAGING="${STAGING:-false}"
WEBROOT="/var/www/certbot"

echo -e "${GREEN}🔐 Let's Encrypt SSL Certificate Setup${NC}"
echo "======================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    exit 1
fi

# Check if domain is provided
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ DOMAIN environment variable is required${NC}"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@example.com ./setup-letsencrypt.sh"
    exit 1
fi

# Check if email is provided
if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ EMAIL environment variable is required${NC}"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@example.com ./setup-letsencrypt.sh"
    exit 1
fi

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Staging: $STAGING"
echo ""

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo -e "${GREEN}📦 Installing certbot...${NC}"
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create webroot directory
mkdir -p "$WEBROOT"

# Determine certbot options
CERTBOT_OPTS="--nginx"
if [ "$STAGING" = "true" ]; then
    CERTBOT_OPTS="$CERTBOT_OPTS --staging"
    echo -e "${YELLOW}⚠️  Using Let's Encrypt staging environment${NC}"
fi

# Obtain certificate
echo -e "${GREEN}📝 Obtaining SSL certificate...${NC}"
certbot certonly \
    $CERTBOT_OPTS \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Check if certificate was obtained successfully
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificate obtained successfully!${NC}"
else
    echo -e "${RED}❌ Failed to obtain certificate${NC}"
    exit 1
fi

# Set up automatic renewal
echo -e "${GREEN}⏰ Setting up automatic renewal...${NC}"

# Create renewal script
cat > /etc/cron.daily/certbot-renew << 'EOF'
#!/bin/bash
# Renew Let's Encrypt certificates

certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose.prod.yml restart nginx"

# Log renewal
if [ $? -eq 0 ]; then
    echo "$(date): Certificate renewal successful" >> /var/log/certbot-renew.log
else
    echo "$(date): Certificate renewal failed" >> /var/log/certbot-renew.log
fi
EOF

chmod +x /etc/cron.daily/certbot-renew

# Test renewal (dry run)
echo -e "${GREEN}🧪 Testing certificate renewal...${NC}"
certbot renew --dry-run

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Renewal test successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Renewal test failed (this is okay for staging)${NC}"
fi

# Display certificate info
echo ""
echo -e "${GREEN}📋 Certificate Information:${NC}"
certbot certificates

echo ""
echo -e "${GREEN}🎉 Let's Encrypt setup complete!${NC}"
echo ""
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "Renewal cron job: /etc/cron.daily/certbot-renew"
echo ""
echo -e "${YELLOW}⚠️  Remember to update your nginx configuration to use these certificates:${NC}"
echo "  ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;"
echo "  ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;"
echo ""
echo -e "${GREEN}📝 Next steps:${NC}"
echo "1. Update nginx configuration"
echo "2. Restart nginx: docker-compose restart nginx"
echo "3. Test HTTPS: curl -I https://$DOMAIN"
echo ""

