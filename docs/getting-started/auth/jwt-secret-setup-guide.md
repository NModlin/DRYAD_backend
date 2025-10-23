# JWT SECRET SYNCHRONIZATION GUIDE
## Dryad.AI Backend ↔ RADAR Frontend

**Date**: October 5, 2025  
**Purpose**: Secure JWT token sharing between backend and frontend

---

## 🔐 CURRENT SETUP

### Backend (Dryad.AI)
**Location**: `.env` file (line 97-98)
```bash
RADAR_JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
RADAR_JWT_ALGORITHM=HS256
```

### How Backend Uses It
- **File**: `app/core/radar_auth.py` (line 45-46)
- **Purpose**: Validates JWT tokens sent from RADAR frontend
- **Token Format**: 
  - Issuer: `radar-auth-service`
  - Audience: `radar-platform`
  - Algorithm: `HS256`

---

## 🎯 SOLUTION OPTIONS

### **OPTION 1: Environment Variables (RECOMMENDED)**

This is the **most secure** and **easiest** approach for development and production.

#### **On RADAR Frontend Machine:**

1. **Create/Update `.env` file** in your RADAR project root:
```bash
# RADAR Frontend Environment Variables

# Dryad.AI Backend Connection
DRYAD_BACKEND_URL=http://localhost:8000
DRYAD_API_BASE_URL=http://localhost:8000/api/v1/radar

# JWT Configuration (MUST MATCH BACKEND)
JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
JWT_ALGORITHM=HS256
JWT_ISSUER=radar-auth-service
JWT_AUDIENCE=radar-platform
JWT_EXPIRATION_HOURS=24
```

2. **In your RADAR auth service** (e.g., `services/auth/jwt.js` or `auth.service.ts`):
```javascript
// Load from environment
const JWT_SECRET = process.env.JWT_SECRET;
const JWT_ALGORITHM = process.env.JWT_ALGORITHM || 'HS256';
const JWT_ISSUER = process.env.JWT_ISSUER || 'radar-auth-service';
const JWT_AUDIENCE = process.env.JWT_AUDIENCE || 'radar-platform';

// Generate token
const jwt = require('jsonwebtoken');

function generateToken(user) {
  const payload = {
    sub: user.id,
    userId: user.id,
    email: user.email,
    username: user.username,
    role: user.role || 'user',
    department: user.department || 'IT Support',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60), // 24 hours
    aud: JWT_AUDIENCE,
    iss: JWT_ISSUER
  };
  
  return jwt.sign(payload, JWT_SECRET, { algorithm: JWT_ALGORITHM });
}
```

3. **Add to `.gitignore`**:
```bash
# Environment files
.env
.env.local
.env.*.local
```

---

### **OPTION 2: Configuration File (Alternative)**

If you prefer a configuration file approach:

#### **On RADAR Frontend Machine:**

1. **Create `config/jwt.config.js`**:
```javascript
module.exports = {
  backend: {
    url: process.env.DRYAD_BACKEND_URL || 'http://localhost:8000',
    apiBase: process.env.DRYAD_API_BASE_URL || 'http://localhost:8000/api/v1/radar'
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30',
    algorithm: process.env.JWT_ALGORITHM || 'HS256',
    issuer: 'radar-auth-service',
    audience: 'radar-platform',
    expirationHours: 24
  }
};
```

2. **Add to `.gitignore`**:
```bash
# Configuration files with secrets
config/jwt.config.js
config/*.local.js
```

3. **Create `config/jwt.config.example.js`** (for version control):
```javascript
module.exports = {
  backend: {
    url: 'http://localhost:8000',
    apiBase: 'http://localhost:8000/api/v1/radar'
  },
  jwt: {
    secret: 'YOUR_JWT_SECRET_HERE',  // Get from backend team
    algorithm: 'HS256',
    issuer: 'radar-auth-service',
    audience: 'radar-platform',
    expirationHours: 24
  }
};
```

---

### **OPTION 3: Secure Secrets Manager (Production)**

For production environments, use a secrets manager:

#### **AWS Secrets Manager**
```javascript
const AWS = require('aws-sdk');
const secretsManager = new AWS.SecretsManager({ region: 'us-east-1' });

async function getJWTSecret() {
  const data = await secretsManager.getSecretValue({ 
    SecretId: 'radar/jwt-secret' 
  }).promise();
  return JSON.parse(data.SecretString).JWT_SECRET;
}
```

#### **Azure Key Vault**
```javascript
const { SecretClient } = require('@azure/keyvault-secrets');
const { DefaultAzureCredential } = require('@azure/identity');

const client = new SecretClient(
  'https://your-vault.vault.azure.net',
  new DefaultAzureCredential()
);

async function getJWTSecret() {
  const secret = await client.getSecret('jwt-secret');
  return secret.value;
}
```

#### **HashiCorp Vault**
```javascript
const vault = require('node-vault')({
  endpoint: 'http://vault:8200',
  token: process.env.VAULT_TOKEN
});

async function getJWTSecret() {
  const result = await vault.read('secret/data/radar/jwt');
  return result.data.data.JWT_SECRET;
}
```

---

## 🔄 SYNCHRONIZATION PROCESS

### **Step 1: Copy Secret from Backend**

On the **backend machine**, get the secret:
```bash
# Windows PowerShell
cd "C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend"
type .env | findstr RADAR_JWT_SECRET

# Output:
# RADAR_JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
```

### **Step 2: Add to RADAR Frontend**

On the **RADAR frontend machine**, create/update `.env`:
```bash
# Copy the secret value
JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
```

### **Step 3: Verify Synchronization**

Test that tokens work between both systems:

```bash
# On RADAR frontend, generate a test token
node -e "
const jwt = require('jsonwebtoken');
const token = jwt.sign({
  sub: 'test-user',
  userId: 'test-user',
  email: 'test@rehrig.com',
  username: 'testuser',
  role: 'admin',
  department: 'IT Support',
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 86400,
  aud: 'radar-platform',
  iss: 'radar-auth-service'
}, 'XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30', { algorithm: 'HS256' });
console.log(token);
"

# Test the token against backend
curl -X POST http://localhost:8000/api/v1/radar/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

---

## 🔒 SECURITY BEST PRACTICES

### **1. Never Commit Secrets to Git**
```bash
# Always add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "config/jwt.config.js" >> .gitignore
```

### **2. Use Different Secrets for Different Environments**
```bash
# Development
JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30

# Production (generate a new one!)
JWT_SECRET=<generate-new-secret-for-production>
```

### **3. Rotate Secrets Regularly**
- Development: Every 90 days
- Production: Every 30 days
- After any security incident: Immediately

### **4. Generate Strong Secrets**
```bash
# Generate a new secret (64 characters)
node -e "console.log(require('crypto').randomBytes(48).toString('base64').replace(/[+/=]/g, ''))"

# Or using OpenSSL
openssl rand -base64 48 | tr -d '+/=' | cut -c1-64
```

### **5. Limit Secret Access**
- Only authorized developers should have access
- Use environment-specific secrets
- Never log or display secrets in application output

---

## 📋 CHECKLIST

### **Backend Setup** ✅
- [x] JWT secret configured in `.env`
- [x] Secret loaded in `app/core/radar_auth.py`
- [x] Token validation working
- [x] `.env` added to `.gitignore`

### **Frontend Setup** (Your Tasks)
- [ ] Create `.env` file in RADAR project root
- [ ] Copy `JWT_SECRET` from backend `.env`
- [ ] Configure JWT generation in auth service
- [ ] Add `.env` to `.gitignore`
- [ ] Test token generation
- [ ] Verify token works with backend

---

## 🧪 TESTING

### **Test 1: Generate Token on Frontend**
```javascript
const jwt = require('jsonwebtoken');

const token = jwt.sign({
  sub: 'dryad-test-user',
  userId: 'dryad-test-user',
  email: 'dryadtest@rehrig.com',
  username: 'dryadtest',
  role: 'admin',
  department: 'IT Support',
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 86400,
  aud: 'radar-platform',
  iss: 'radar-auth-service'
}, process.env.JWT_SECRET, { algorithm: 'HS256' });

console.log('Generated Token:', token);
```

### **Test 2: Validate with Backend**
```bash
curl -X GET http://localhost:8000/api/v1/radar/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Test 3: Full Integration Test**
```bash
curl -X POST http://localhost:8000/api/v1/radar/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from RADAR!",
    "context": {
      "userId": "test-user",
      "username": "testuser",
      "department": "IT Support"
    }
  }'
```

---

## 🚨 TROUBLESHOOTING

### **Error: "Invalid token signature"**
**Cause**: JWT secrets don't match between frontend and backend

**Solution**:
1. Verify secrets match exactly (no extra spaces/newlines)
2. Check algorithm is `HS256` on both sides
3. Ensure no encoding issues (use plain text, not base64)

### **Error: "Token expired"**
**Cause**: Token `exp` claim is in the past

**Solution**:
1. Check system clocks are synchronized
2. Increase expiration time (currently 24 hours)
3. Regenerate token with correct timestamp

### **Error: "Invalid issuer/audience"**
**Cause**: Token claims don't match expected values

**Solution**:
1. Ensure `iss` is `radar-auth-service`
2. Ensure `aud` is `radar-platform`
3. Check backend validation in `app/core/radar_auth.py`

---

## 📞 SUPPORT

If you encounter issues:

1. **Check backend logs** for validation errors
2. **Verify secret synchronization** using the checklist above
3. **Test with the provided token** from `test_radar_connection.py`
4. **Contact backend team** if issues persist

---

## 🎯 QUICK REFERENCE

### **Current JWT Secret**
```
XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
```

### **Token Requirements**
- **Algorithm**: HS256
- **Issuer**: radar-auth-service
- **Audience**: radar-platform
- **Expiration**: 24 hours (86400 seconds)
- **Required Claims**: sub, userId, email, username, role, iat, exp, aud, iss

### **Backend Endpoints**
- Health: `GET /api/v1/radar/health` (no auth)
- Chat: `POST /api/v1/radar/api/chat/message` (auth required)
- Conversations: `GET /api/v1/radar/api/chat/conversations` (auth required)

---

*Last Updated: October 5, 2025*  
*Backend Team - Dryad.AI*

