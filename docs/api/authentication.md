# DRYAD.AI API Authentication Guide

**Version:** 1.0  
**Last Updated:** 2025-10-13

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Methods](#authentication-methods)
3. [OAuth2 Flow](#oauth2-flow)
4. [JWT Tokens](#jwt-tokens)
5. [API Keys](#api-keys)
6. [Tenant Isolation](#tenant-isolation)
7. [Security Best Practices](#security-best-practices)
8. [Examples](#examples)

---

## Overview

DRYAD.AI uses a multi-layered authentication system to ensure secure access to the API:

- **OAuth2** for user authentication
- **JWT tokens** for session management
- **API keys** for service-to-service communication
- **Tenant isolation** for multi-tenancy support

---

## Authentication Methods

### 1. OAuth2 (Recommended for User Applications)

OAuth2 is the recommended authentication method for applications that require user login.

**Supported Flows:**
- Authorization Code Flow (web applications)
- Client Credentials Flow (service accounts)
- Refresh Token Flow (long-lived sessions)

**Endpoints:**
- Authorization: `GET /oauth/authorize`
- Token: `POST /oauth/token`
- Revoke: `POST /oauth/revoke`

### 2. JWT Tokens

After successful OAuth2 authentication, you receive a JWT token that must be included in all API requests.

**Token Structure:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scope": "read write"
}
```

**Token Payload:**
```json
{
  "sub": "user_id_123",
  "tenant_id": "tenant_abc",
  "email": "user@example.com",
  "roles": ["user", "admin"],
  "exp": 1699999999,
  "iat": 1699996399
}
```

### 3. API Keys

API keys are used for service-to-service communication and automated workflows.

**Key Format:**
```
dryad_sk_1234567890abcdef1234567890abcdef
```

**Key Prefixes:**
- `dryad_sk_` - Secret key (full access)
- `dryad_pk_` - Public key (read-only)
- `dryad_test_` - Test environment key

---

## OAuth2 Flow

### Authorization Code Flow

**Step 1: Redirect user to authorization endpoint**

```
GET https://api.dryad.ai/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://yourapp.com/callback&
  scope=read write&
  state=random_state_string
```

**Step 2: User authorizes application**

User is redirected to login page, authenticates, and authorizes your application.

**Step 3: Receive authorization code**

```
https://yourapp.com/callback?
  code=AUTHORIZATION_CODE&
  state=random_state_string
```

**Step 4: Exchange code for access token**

```bash
POST https://api.dryad.ai/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
redirect_uri=https://yourapp.com/callback
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scope": "read write"
}
```

### Client Credentials Flow

For service accounts and machine-to-machine communication:

```bash
POST https://api.dryad.ai/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
scope=read write
```

### Refresh Token Flow

To obtain a new access token without re-authentication:

```bash
POST https://api.dryad.ai/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=YOUR_REFRESH_TOKEN&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

---

## JWT Tokens

### Using JWT Tokens

Include the JWT token in the `Authorization` header of all API requests:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.dryad.ai/v1/agents
```

### Token Expiration

- **Access tokens:** Expire after 1 hour (3600 seconds)
- **Refresh tokens:** Expire after 30 days
- **API keys:** Never expire (but can be revoked)

### Token Validation

The API validates tokens on every request:

1. Signature verification
2. Expiration check
3. Tenant isolation check
4. Permission/scope validation

---

## API Keys

### Creating API Keys

```bash
POST https://api.dryad.ai/v1/api-keys
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "Production API Key",
  "scopes": ["read", "write"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "id": "key_123",
  "key": "dryad_sk_1234567890abcdef1234567890abcdef",
  "name": "Production API Key",
  "scopes": ["read", "write"],
  "created_at": "2025-10-13T10:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

⚠️ **Important:** The API key is only shown once. Store it securely!

### Using API Keys

```bash
curl -H "X-API-Key: dryad_sk_1234567890abcdef1234567890abcdef" \
  https://api.dryad.ai/v1/agents
```

### Revoking API Keys

```bash
DELETE https://api.dryad.ai/v1/api-keys/key_123
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Tenant Isolation

DRYAD.AI supports multi-tenancy with strict data isolation.

### Tenant ID

Every request is associated with a tenant:

- **JWT tokens:** Tenant ID is embedded in the token
- **API keys:** Tenant ID is associated with the key
- **Headers:** Can be overridden with `X-Tenant-ID` header (admin only)

### Tenant Switching

Admins can switch tenants using the `X-Tenant-ID` header:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "X-Tenant-ID: tenant_xyz" \
  https://api.dryad.ai/v1/agents
```

---

## Security Best Practices

### 1. Store Credentials Securely

- **Never** commit API keys or secrets to version control
- Use environment variables or secret management services
- Rotate API keys regularly

### 2. Use HTTPS Only

All API requests must use HTTPS. HTTP requests will be rejected.

### 3. Implement Token Refresh

Don't wait for tokens to expire. Refresh proactively:

```python
import time

def get_valid_token():
    if time.time() >= token_expires_at - 300:  # Refresh 5 min before expiry
        refresh_access_token()
    return access_token
```

### 4. Limit Token Scope

Request only the scopes you need:

- `read` - Read-only access
- `write` - Create and update resources
- `delete` - Delete resources
- `admin` - Administrative access

### 5. Monitor API Usage

Track API key usage and set up alerts for:
- Unusual request patterns
- Failed authentication attempts
- Rate limit violations

---

## Examples

### Python Example

```python
import requests
from datetime import datetime, timedelta

class DryadClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
    
    def authenticate(self):
        """Get access token using client credentials flow."""
        response = requests.post(
            'https://api.dryad.ai/oauth/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'read write'
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data['access_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=data['expires_in'])
    
    def get_headers(self):
        """Get headers with valid access token."""
        if not self.access_token or datetime.now() >= self.token_expires_at - timedelta(minutes=5):
            self.authenticate()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def list_agents(self):
        """List all agents."""
        response = requests.get(
            'https://api.dryad.ai/v1/agents',
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = DryadClient('your_client_id', 'your_client_secret')
agents = client.list_agents()
print(agents)
```

### cURL Example

```bash
# Get access token
TOKEN_RESPONSE=$(curl -X POST https://api.dryad.ai/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

# Make API request
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://api.dryad.ai/v1/agents
```

---

## Support

For authentication issues:
- **Documentation:** https://docs.dryad.ai
- **Support:** support@dryad.ai
- **Status:** https://status.dryad.ai

---

**Last Updated:** 2025-10-13  
**Next Review:** 2025-11-13

