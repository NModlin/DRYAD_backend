#!/bin/bash
# ============================================================================
# SSL Certificate Generation Script for DRYAD.AI Backend
# Generates self-signed certificates for development/testing
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CERT_DIR="nginx/ssl"
DOMAIN="${DOMAIN:-localhost}"
DAYS="${DAYS:-365}"
KEY_SIZE="${KEY_SIZE:-2048}"

echo -e "${GREEN}🔐 SSL Certificate Generation Script${NC}"
echo "=================================="
echo ""

# Create directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Check if certificates already exist
if [ -f "$CERT_DIR/cert.pem" ] && [ -f "$CERT_DIR/key.pem" ]; then
    echo -e "${YELLOW}⚠️  Certificates already exist!${NC}"
    read -p "Do you want to regenerate them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates."
        exit 0
    fi
fi

echo -e "${GREEN}📝 Generating SSL certificates...${NC}"
echo "Domain: $DOMAIN"
echo "Validity: $DAYS days"
echo "Key size: $KEY_SIZE bits"
echo ""

# Generate private key
echo -e "${GREEN}1. Generating private key...${NC}"
openssl genrsa -out "$CERT_DIR/key.pem" $KEY_SIZE

# Generate certificate signing request (CSR)
echo -e "${GREEN}2. Generating certificate signing request...${NC}"
openssl req -new -key "$CERT_DIR/key.pem" -out "$CERT_DIR/csr.pem" \
    -subj "/C=US/ST=State/L=City/O=DRYAD.AI/OU=IT/CN=$DOMAIN"

# Generate self-signed certificate
echo -e "${GREEN}3. Generating self-signed certificate...${NC}"
openssl x509 -req -days $DAYS \
    -in "$CERT_DIR/csr.pem" \
    -signkey "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -extfile <(printf "subjectAltName=DNS:$DOMAIN,DNS:*.$DOMAIN,DNS:localhost,IP:127.0.0.1")

# Generate DH parameters for stronger security
echo -e "${GREEN}4. Generating Diffie-Hellman parameters (this may take a while)...${NC}"
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# Set proper permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"
chmod 644 "$CERT_DIR/dhparam.pem"

# Clean up CSR
rm "$CERT_DIR/csr.pem"

echo ""
echo -e "${GREEN}✅ SSL certificates generated successfully!${NC}"
echo ""
echo "Files created:"
echo "  - $CERT_DIR/cert.pem (Certificate)"
echo "  - $CERT_DIR/key.pem (Private Key)"
echo "  - $CERT_DIR/dhparam.pem (DH Parameters)"
echo ""
echo -e "${YELLOW}⚠️  Note: These are self-signed certificates for development only!${NC}"
echo -e "${YELLOW}   For production, use Let's Encrypt or a commercial CA.${NC}"
echo ""

# Display certificate info
echo -e "${GREEN}📋 Certificate Information:${NC}"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -text | grep -A 2 "Subject:"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -text | grep -A 1 "Validity"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -text | grep "DNS:"

echo ""
echo -e "${GREEN}🎉 Done!${NC}"

