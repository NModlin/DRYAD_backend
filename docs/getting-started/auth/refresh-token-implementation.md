# REFRESH TOKEN IMPLEMENTATION GUIDE
## Seamless Authentication Without Manual Re-login

---

## 🎯 THE PROBLEM

**Current Setup:**
- JWT expires after 24 hours
- User has to manually log in again ❌
- Poor user experience

**Better Solution:**
- Short-lived access tokens (15 min - 1 hour)
- Long-lived refresh tokens (7-30 days)
- Automatic token refresh in background ✅
- User stays logged in seamlessly

---

## 🔧 RECOMMENDED CONFIGURATION

### **Backend `.env` (Already Updated):**

```bash
# Access Token (short-lived, used for API requests)
RADAR_JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
RADAR_JWT_ALGORITHM=HS256
RADAR_JWT_EXPIRATION_HOURS=1  # Short-lived: 1 hour

# Refresh Token (long-lived, used to get new access tokens)
RADAR_REFRESH_TOKEN_SECRET=<generate-different-secret>
RADAR_REFRESH_TOKEN_ALGORITHM=HS256
RADAR_REFRESH_TOKEN_EXPIRATION_DAYS=30  # Long-lived: 30 days
```

### **RADAR Frontend `.env`:**

```bash
# Access Token Configuration
JWT_SECRET=XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1  # Short-lived

# Refresh Token Configuration
REFRESH_TOKEN_SECRET=<same-as-backend>
REFRESH_TOKEN_ALGORITHM=HS256
REFRESH_TOKEN_EXPIRATION_DAYS=30  # Long-lived

# Auto-refresh settings
AUTO_REFRESH_ENABLED=true
REFRESH_BEFORE_EXPIRY_MINUTES=5  # Refresh 5 min before expiration
```

---

## 💻 IMPLEMENTATION

### **1. Backend: Add Refresh Token Endpoint**

Create a new endpoint in the backend to handle token refresh:

```python
# app/api/v1/endpoints/radar.py

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    refreshToken: str

class RefreshTokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int

@router.post("/api/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    This allows users to stay logged in without re-entering credentials.
    """
    try:
        # Verify refresh token
        refresh_secret = os.getenv("RADAR_REFRESH_TOKEN_SECRET", config.JWT_SECRET_KEY)
        payload = jwt.decode(
            request.refreshToken,
            refresh_secret,
            algorithms=["HS256"],
            audience="radar-platform",
            issuer="radar-auth-service"
        )
        
        # Generate new access token
        now = datetime.now(timezone.utc)
        access_expiration = now + timedelta(hours=1)
        
        access_payload = {
            "sub": payload["sub"],
            "userId": payload["userId"],
            "email": payload["email"],
            "username": payload["username"],
            "role": payload["role"],
            "department": payload.get("department", "IT Support"),
            "iat": int(now.timestamp()),
            "exp": int(access_expiration.timestamp()),
            "aud": "radar-platform",
            "iss": "radar-auth-service"
        }
        
        access_token = jwt.encode(
            access_payload,
            os.getenv("RADAR_JWT_SECRET"),
            algorithm="HS256"
        )
        
        # Generate new refresh token (optional: rotate refresh tokens)
        refresh_expiration = now + timedelta(days=30)
        refresh_payload = {
            **access_payload,
            "exp": int(refresh_expiration.timestamp()),
            "type": "refresh"
        }
        
        new_refresh_token = jwt.encode(
            refresh_payload,
            refresh_secret,
            algorithm="HS256"
        )
        
        return RefreshTokenResponse(
            accessToken=access_token,
            refreshToken=new_refresh_token,
            expiresIn=3600  # 1 hour in seconds
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

### **2. RADAR Frontend: Auto-Refresh Service**

```javascript
// services/tokenRefresh.service.js

class TokenRefreshService {
  constructor() {
    this.refreshTimer = null;
    this.isRefreshing = false;
  }

  /**
   * Start automatic token refresh
   */
  startAutoRefresh() {
    // Get token expiration
    const token = localStorage.getItem('accessToken');
    if (!token) return;

    const payload = this.decodeToken(token);
    const expiresAt = payload.exp * 1000; // Convert to milliseconds
    const now = Date.now();
    const timeUntilExpiry = expiresAt - now;
    
    // Refresh 5 minutes before expiration
    const refreshBeforeMs = 5 * 60 * 1000;
    const refreshIn = timeUntilExpiry - refreshBeforeMs;

    if (refreshIn > 0) {
      console.log(`Token will be refreshed in ${Math.floor(refreshIn / 1000 / 60)} minutes`);
      
      this.refreshTimer = setTimeout(() => {
        this.refreshToken();
      }, refreshIn);
    } else {
      // Token expires soon, refresh immediately
      this.refreshToken();
    }
  }

  /**
   * Stop automatic token refresh
   */
  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Refresh the access token
   */
  async refreshToken() {
    if (this.isRefreshing) return;
    
    this.isRefreshing = true;
    
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch('http://localhost:8000/api/v1/radar/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refreshToken })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      // Store new tokens
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      
      console.log('✅ Token refreshed successfully');
      
      // Schedule next refresh
      this.startAutoRefresh();
      
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      
      // Clear tokens and redirect to login
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
      
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Decode JWT token
   */
  decodeToken(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  }
}

// Export singleton instance
export const tokenRefreshService = new TokenRefreshService();
```

### **3. RADAR Frontend: Initialize on Login**

```javascript
// components/Login.jsx or auth.service.js

async function handleLogin(username, password) {
  try {
    const response = await fetch('http://localhost:8000/api/v1/radar/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    
    // Store both tokens
    localStorage.setItem('accessToken', data.accessToken);
    localStorage.setItem('refreshToken', data.refreshToken);
    
    // Start automatic token refresh
    tokenRefreshService.startAutoRefresh();
    
    // Redirect to dashboard
    window.location.href = '/dashboard';
    
  } catch (error) {
    console.error('Login failed:', error);
  }
}
```

### **4. RADAR Frontend: Initialize on App Load**

```javascript
// App.jsx or index.js

import { tokenRefreshService } from './services/tokenRefresh.service';

// On app initialization
window.addEventListener('load', () => {
  const token = localStorage.getItem('accessToken');
  
  if (token) {
    // User is logged in, start auto-refresh
    tokenRefreshService.startAutoRefresh();
  }
});

// On logout
function handleLogout() {
  tokenRefreshService.stopAutoRefresh();
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  window.location.href = '/login';
}
```

---

## 🎯 ALTERNATIVE: SIMPLER APPROACH (Keep 24-hour tokens)

If you don't want to implement refresh tokens right now, here are simpler options:

### **Option 1: Extend Token Lifetime**

```bash
# Backend .env
RADAR_JWT_EXPIRATION_HOURS=168  # 7 days

# RADAR Frontend .env
JWT_EXPIRATION_HOURS=168  # 7 days
```

**Pros:**
- ✅ Simple, no code changes
- ✅ Users stay logged in for a week

**Cons:**
- ❌ Less secure (longer exposure if token is stolen)
- ❌ Still need to log in weekly

### **Option 2: "Remember Me" Checkbox**

```javascript
// Login form
<input type="checkbox" id="rememberMe" />
<label for="rememberMe">Keep me logged in for 30 days</label>

// Generate token with longer expiration if checked
const expirationHours = rememberMe ? 720 : 24;  // 30 days or 24 hours
```

### **Option 3: Session Storage + Backend Session**

Instead of JWT, use traditional sessions:
- Backend maintains session in database/Redis
- Frontend stores session ID
- Session never expires as long as user is active
- More secure, easier to revoke

---

## 📊 COMPARISON

| Approach | User Experience | Security | Complexity |
|----------|----------------|----------|------------|
| **24-hour token** | ❌ Poor (manual re-login) | ⚠️ Medium | ✅ Simple |
| **7-day token** | ⚠️ OK (weekly re-login) | ❌ Lower | ✅ Simple |
| **Refresh tokens** | ✅ Excellent (seamless) | ✅ High | ⚠️ Medium |
| **Sessions** | ✅ Excellent (seamless) | ✅ High | ⚠️ Medium |

---

## 🎯 MY RECOMMENDATION

### **For Development (Right Now):**
**Extend token to 7 days** - Quick fix, good enough for testing

```bash
# Update both .env files
RADAR_JWT_EXPIRATION_HOURS=168  # 7 days
```

### **For Production (Later):**
**Implement refresh tokens** - Best user experience + security

---

## 🚀 QUICK FIX (5 Minutes)

Want to fix this right now? Just update the expiration:

### **Backend `.env`:**
```bash
RADAR_JWT_EXPIRATION_HOURS=168  # 7 days instead of 24 hours
```

### **RADAR Frontend `.env`:**
```bash
JWT_EXPIRATION_HOURS=168  # 7 days instead of 24 hours
```

### **Restart both services:**
```bash
# Backend
# (Already running, will pick up new .env on next restart)

# RADAR Frontend
npm restart
```

**Now users stay logged in for 7 days instead of 24 hours!**

---

## 📞 NEED HELP IMPLEMENTING?

Let me know which approach you prefer:

1. **Quick fix**: Extend to 7 days (5 minutes)
2. **Better solution**: Implement refresh tokens (30 minutes)
3. **Alternative**: Switch to session-based auth (1 hour)

I can help implement any of these! 🚀

---

*Last Updated: October 5, 2025*  
*Backend Team - Dryad.AI*

