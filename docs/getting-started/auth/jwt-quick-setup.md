# JWT SECRET - QUICK SETUP
## 5-Minute Configuration Guide

---

## 🎯 THE SECRET

Copy this **exact value** to your RADAR frontend:

```
XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
```

---

## 📝 RADAR FRONTEND SETUP

### **Step 1: Create `.env` file**

In your RADAR project root, create/update `.env`:

```bash
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

### **Step 2: Add to `.gitignore`**

```bash
.env
.env.local
.env.*.local
```

### **Step 3: Use in Your Auth Service**

```javascript
// auth.service.js or auth.service.ts
const jwt = require('jsonwebtoken');

function generateToken(user) {
  return jwt.sign({
    sub: user.id,
    userId: user.id,
    email: user.email,
    username: user.username,
    role: user.role || 'user',
    department: user.department || 'IT Support',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60),
    aud: 'radar-platform',
    iss: 'radar-auth-service'
  }, process.env.JWT_SECRET, { algorithm: 'HS256' });
}

module.exports = { generateToken };
```

---

## ✅ TEST IT

### **Generate a test token:**

```bash
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
```

### **Test against backend:**

```bash
curl -X GET http://localhost:8000/api/v1/radar/health \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "dryad": "connected",
  "llm": "available"
}
```

---

## 🚨 TROUBLESHOOTING

### **"Invalid token signature"**
→ Secret doesn't match. Copy the exact value above (no spaces/newlines)

### **"Token expired"**
→ Regenerate token with current timestamp

### **"Invalid issuer/audience"**
→ Check `iss` = `radar-auth-service` and `aud` = `radar-platform`

---

## 📞 NEED HELP?

1. Check `JWT_SECRET_SETUP_GUIDE.md` for detailed instructions
2. Verify backend is running: `http://localhost:8000/api/v1/radar/health`
3. Check backend logs for validation errors

---

**That's it! You're ready to go.** 🚀

