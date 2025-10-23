# Google OAuth - Quick Start Guide

## TL;DR

Your Google OAuth is **already configured** and ready to use!

## Start the System

### 1. Start Backend
```bash
python start.py
```

### 2. Start Frontend (new terminal)
```bash
cd frontend/writer-portal
npm run dev
```

### 3. Test
Open http://localhost:3000 and click "Sign in with Google"

## Verify Configuration

```bash
python test_oauth_config.py
```

Expected output:
```
✓ GOOGLE_CLIENT_ID: 818968828866-...
✓ GOOGLE_CLIENT_SECRET: GOCSPX-7Ry...
✓ JWT_SECRET_KEY: kJ8mN2pQ4r...
✓ FRONTEND_URL: http://localhost:3000
✓ API_BASE_URL: http://localhost:8000
```

## Test OAuth Endpoint

```bash
curl http://localhost:8000/api/v1/auth/config
```

Expected response:
```json
{
  "google_client_id": "818968828866-uqn5cog63sntgjapn45uotsnld3rsc0o.apps.googleusercontent.com",
  "redirect_uri": "http://localhost:3000/auth/callback",
  "scopes": ["openid", "email", "profile"]
}
```

## What Was Fixed

1. ✅ Hardcoded redirect URI → Now uses `FRONTEND_URL`
2. ✅ CORS credentials disabled → Now enabled for cookies
3. ✅ Missing security context → Now includes client IP/user agent
4. ✅ Environment config → All variables properly set
5. ✅ Frontend config → `.env.local` created

## Files Changed

### Backend
- `app/api/v1/endpoints/auth.py` - Fixed redirect URI and token creation
- `app/main.py` - Enabled CORS credentials
- `.env` - Updated OAuth configuration

### Frontend
- `frontend/writer-portal/.env.local` - Created with proper config

## New Tools

```bash
# Quick config check
python test_oauth_config.py

# Full validation
python scripts/validate_oauth_setup.py

# Test OAuth flow
python scripts/test_oauth_flow.py

# Interactive setup (if needed)
python scripts/setup_google_oauth.py
```

## Documentation

- **`OAUTH_COMPLETE_FIX.md`** - Complete fix summary
- **`GOOGLE_OAUTH_SETUP.md`** - Detailed setup guide
- **`OAUTH_FIX_SUMMARY.md`** - Technical details

## Troubleshooting

### Backend won't start
```bash
# Check configuration
python test_oauth_config.py

# Check for errors
python start.py
```

### Frontend can't connect
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend config
cat frontend/writer-portal/.env.local
```

### OAuth fails
```bash
# Run validation
python scripts/validate_oauth_setup.py

# Check Google Console
# https://console.cloud.google.com/
# Verify redirect URIs:
# - http://localhost:3000/auth/callback
# - http://localhost:8000/api/v1/auth/google/callback
```

## Common Commands

```bash
# Start backend
python start.py

# Start frontend
cd frontend/writer-portal && npm run dev

# Check config
python test_oauth_config.py

# Validate setup
python scripts/validate_oauth_setup.py

# Test OAuth
python scripts/test_oauth_flow.py

# View logs
tail -f logs/gremlins_app.log
```

## OAuth Flow

```
1. User clicks "Sign in with Google"
2. Google Sign-In popup appears
3. User authenticates with Google
4. Google returns ID token
5. Frontend sends token to backend
6. Backend verifies token with Google
7. Backend creates/updates user
8. Backend returns JWT access token
9. User is authenticated
```

## Success Indicators

✅ Backend starts without errors
✅ OAuth config endpoint works
✅ Frontend loads Google SDK
✅ Sign in button appears
✅ OAuth flow completes
✅ User info displays
✅ API requests work

## Need Help?

1. Run validation: `python scripts/validate_oauth_setup.py`
2. Check logs: `logs/gremlins_app.log`
3. Read docs: `GOOGLE_OAUTH_SETUP.md`
4. Check browser console (F12)

## Production Deployment

See `GOOGLE_OAUTH_SETUP.md` section "Production Deployment" for:
- Production environment configuration
- HTTPS setup
- Security best practices
- Google Console production setup

---

**Status: ✅ Ready to Use**

Your OAuth is configured and working. Just start the backend and frontend!

