# Task 2-36: Static File Serving

**Phase:** 2 - Performance & Production Readiness  
**Week:** 7 - Production Infrastructure  
**Priority:** MEDIUM  
**Estimated Hours:** 2 hours

---

## 📋 OVERVIEW

Configure efficient static file serving using nginx with proper caching headers, compression, and CDN integration for optimal performance.

---

## 🎯 OBJECTIVES

1. Configure nginx for static file serving
2. Set up caching headers
3. Enable compression for static assets
4. Configure CDN integration (optional)
5. Test static file performance
6. Document static file strategy

---

## 📊 CURRENT STATE

**Existing:**
- FastAPI serves static files
- No caching headers
- No compression
- No CDN

**Gaps:**
- Inefficient static file serving
- No browser caching
- No compression
- Slow asset loading

---

## 🔧 IMPLEMENTATION

### 1. Nginx Static File Configuration

Create `docker/nginx/static.conf`:

```nginx
# Static File Serving Configuration

# Static files location
location /static/ {
    alias /var/www/static/;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/css
        text/javascript
        text/xml
        text/plain
        application/javascript
        application/json
        application/xml
        application/rss+xml
        image/svg+xml;
    
    # Cache static assets
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    
    # CORS for fonts and assets
    add_header Access-Control-Allow-Origin "*";
    
    # Disable access logs for static files
    access_log off;
    
    # Enable sendfile for better performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
}

# Media files (user uploads)
location /media/ {
    alias /var/www/media/;
    
    # Shorter cache for user content
    expires 7d;
    add_header Cache-Control "public";
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header Content-Security-Policy "default-src 'none'; img-src 'self'; style-src 'self'";
    
    # Limit file types
    location ~* \.(jpg|jpeg|png|gif|ico|svg|webp|pdf|txt)$ {
        # Allow these file types
    }
    
    # Block other file types
    location ~* \.(php|exe|sh|bat)$ {
        deny all;
    }
}

# Versioned static files (with hash in filename)
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
    # Long cache for versioned files
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # Enable compression
    gzip_static on;
}

# HTML files (no cache)
location ~* \.html$ {
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

---

### 2. Docker Volume Configuration

Update `docker-compose.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/static.conf:/etc/nginx/conf.d/static.conf:ro
      - ./static:/var/www/static:ro
      - ./media:/var/www/media:ro
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - gremlins-network
    restart: unless-stopped
```

---

### 3. FastAPI Static Files (Development Only)

Update `app/main.py`:

```python
"""
FastAPI Application with Static Files

Static files served by nginx in production.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static files in development only
if os.getenv("ENVIRONMENT") == "development":
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/media", StaticFiles(directory="media"), name="media")
```

---

### 4. Static File Upload Handler

Create `app/api/v1/endpoints/upload.py`:

```python
"""
File Upload Endpoints

Handle file uploads to media directory.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()

MEDIA_DIR = Path("media")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class UploadResponse(BaseModel):
    """File upload response."""
    filename: str
    url: str
    size: int


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file to media directory.
    
    Args:
        file: File to upload
    
    Returns:
        Upload response with file URL
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )
    
    # Read file
    contents = await file.read()
    
    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = MEDIA_DIR / unique_filename
    
    # Ensure media directory exists
    MEDIA_DIR.mkdir(exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Return URL
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    file_url = f"{base_url}/media/{unique_filename}"
    
    return UploadResponse(
        filename=unique_filename,
        url=file_url,
        size=len(contents)
    )
```

---

### 5. CDN Configuration (Optional)

Create `docs/deployment/CDN_SETUP.md`:

```markdown
# CDN Setup for Static Files

## CloudFlare Configuration

### 1. Add Domain to CloudFlare
- Sign up at cloudflare.com
- Add your domain
- Update nameservers

### 2. Configure Caching Rules

**Page Rule for Static Files:**
- URL: `*dryad.ai/static/*`
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 year

**Page Rule for Media Files:**
- URL: `*dryad.ai/media/*`
- Cache Level: Cache Everything
- Edge Cache TTL: 1 week
- Browser Cache TTL: 1 week

### 3. Enable Auto Minify
- Auto Minify: JavaScript, CSS, HTML
- Brotli Compression: Enabled

### 4. Purge Cache
```bash
# Purge all cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'

# Purge specific files
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://dryad.ai/static/app.js"]}'
```

## AWS CloudFront Configuration

### 1. Create S3 Bucket
```bash
aws s3 mb s3://dryad-static
aws s3 sync ./static s3://dryad-static/static/
```

### 2. Create CloudFront Distribution
- Origin: S3 bucket
- Viewer Protocol Policy: Redirect HTTP to HTTPS
- Compress Objects: Yes
- Default TTL: 31536000 (1 year)

### 3. Invalidate Cache
```bash
aws cloudfront create-invalidation \
  --distribution-id {distribution_id} \
  --paths "/static/*"
```
```

---

### 6. Static File Versioning

Create `scripts/build/version-assets.sh`:

```bash
#!/bin/bash
#
# Version Static Assets
#
# Adds content hash to filenames for cache busting

set -e

STATIC_DIR="static"
OUTPUT_DIR="static/dist"

echo "📦 Versioning static assets..."

# Create output directory
mkdir -p ${OUTPUT_DIR}

# Process CSS files
for file in ${STATIC_DIR}/*.css; do
    if [ -f "$file" ]; then
        hash=$(md5sum "$file" | cut -d' ' -f1 | cut -c1-8)
        filename=$(basename "$file" .css)
        cp "$file" "${OUTPUT_DIR}/${filename}.${hash}.css"
        echo "✅ ${filename}.css -> ${filename}.${hash}.css"
    fi
done

# Process JS files
for file in ${STATIC_DIR}/*.js; do
    if [ -f "$file" ]; then
        hash=$(md5sum "$file" | cut -d' ' -f1 | cut -c1-8)
        filename=$(basename "$file" .js)
        cp "$file" "${OUTPUT_DIR}/${filename}.${hash}.js"
        echo "✅ ${filename}.js -> ${filename}.${hash}.js"
    fi
done

echo "✅ Asset versioning complete"
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Nginx static file serving configured
- [ ] Caching headers set correctly
- [ ] Compression enabled
- [ ] File upload working
- [ ] CDN integration documented
- [ ] Asset versioning implemented
- [ ] Performance tested

---

## 🧪 TESTING

```bash
# Test static file serving
curl -I http://localhost/static/app.css

# Check cache headers
curl -I http://localhost/static/app.css | grep -i cache

# Check compression
curl -H "Accept-Encoding: gzip" -I http://localhost/static/app.js | grep -i encoding

# Test file upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.jpg"
```

---

## 📝 NOTES

- Use nginx for static files in production
- Set long cache times for versioned assets
- Use CDN for global distribution
- Implement asset versioning for cache busting
- Monitor CDN hit rates


