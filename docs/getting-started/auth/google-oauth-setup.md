# Google OAuth Setup Guide for DRYAD.AI

This guide will help you set up Google OAuth authentication for the DRYAD.AI Backend and frontend.

## Prerequisites

- Google Cloud Platform account
- DRYAD.AI Backend and frontend installed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google+ API"
3. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** user type (or Internal if using Google Workspace)
3. Fill in the required information:
   - **App name**: DRYAD.AI
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users (for development):
   - Add your email address
6. Click **Save and Continue**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Web application**
4. Configure the OAuth client:
   - **Name**: DRYAD.AI Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:3000` (development)
     - `http://localhost:8000` (backend)
     - Add your production URLs
   - **Authorized redirect URIs**:
     - `http://localhost:3000/auth/callback` (frontend)
     - `http://localhost:8000/api/v1/auth/google/callback` (backend)
     - Add your production URLs
5. Click **Create**
6. **IMPORTANT**: Copy the **Client ID** and **Client Secret** - you'll need these!

## Step 5: Configure Backend Environment

1. Open or create `.env` file in the backend root directory:

```bash
# Copy from .env.example if it doesn't exist
cp .env.example .env
```

2. Add your Google OAuth credentials:

```bash
# OAuth2 Configuration (Google)
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# JWT Secret Key (generate a secure key)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET_KEY=your-generated-secret-key-here

# Frontend URL (for CORS and redirects)
FRONTEND_URL=http://localhost:3000

# Environment
ENVIRONMENT=development
```

3. **Generate a secure JWT secret key**:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output and paste it as your `JWT_SECRET_KEY`.

## Step 6: Configure Frontend Environment

1. Navigate to the frontend directory:

```bash
cd frontend/writer-portal
```

2. Create `.env.local` file:

```bash
# Copy from example
cp .env.local.example .env.local
```

3. Add your configuration:

```bash
# API Base URL
NEXT_PUBLIC_API_BASE=http://localhost:8000

# Google OAuth Client ID (same as backend)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com

# Environment
NEXT_PUBLIC_ENVIRONMENT=development
```

## Step 7: Verify Configuration

1. Start the backend:

```bash
# From backend root directory
python start.py
```

2. Check the logs for OAuth configuration:
   - Should see: "OAuth2 security system initialized"
   - Should NOT see: "GOOGLE_CLIENT_ID not set" warnings

3. Test the auth config endpoint:

```bash
curl http://localhost:8000/api/v1/auth/config
```

Expected response:
```json
{
  "google_client_id": "your-client-id.apps.googleusercontent.com",
  "redirect_uri": "http://localhost:3000/auth/callback",
  "scopes": ["openid", "email", "profile"]
}
```

4. Start the frontend:

```bash
cd frontend/writer-portal
npm run dev
```

5. Open browser to `http://localhost:3000`
6. Click "Sign in with Google"
7. Complete the OAuth flow

## Step 8: Test Authentication

1. After signing in, check browser console for any errors
2. Verify you see your user information
3. Check that API requests include the Authorization header
4. Test protected endpoints

## Troubleshooting

### "OAuth2 not configured" Error

**Problem**: Backend returns 500 error with "OAuth2 not configured"

**Solution**: 
- Verify `GOOGLE_CLIENT_ID` is set in backend `.env`
- Restart the backend server
- Check for typos in the client ID

### "Invalid token" Error

**Problem**: Token verification fails

**Solutions**:
- Verify `GOOGLE_CLIENT_SECRET` is set correctly
- Check that the Client ID matches between frontend and backend
- Ensure redirect URIs are configured correctly in Google Console
- Verify JWT_SECRET_KEY is set and consistent

### "CORS Error" in Browser

**Problem**: Browser shows CORS policy error

**Solutions**:
- Verify `FRONTEND_URL` is set in backend `.env`
- Check that CORS origins include your frontend URL
- Ensure `allow_credentials=True` in CORS middleware
- Restart backend after changing CORS configuration

### "Redirect URI Mismatch" Error

**Problem**: Google shows "redirect_uri_mismatch" error

**Solutions**:
- Verify redirect URIs in Google Console match exactly:
  - Frontend: `http://localhost:3000/auth/callback`
  - Backend: `http://localhost:8000/api/v1/auth/google/callback`
- Check for trailing slashes (should not have them)
- Verify protocol (http vs https)
- For production, use HTTPS URLs

### Token Expires Immediately

**Problem**: User gets logged out immediately after login

**Solutions**:
- Check JWT_SECRET_KEY is set and not changing
- Verify token expiration settings in `.env`:
  ```bash
  JWT_EXPIRATION_HOURS=1
  REFRESH_TOKEN_EXPIRATION_DAYS=7
  ```
- Check browser console for token validation errors

### "Failed to load Google SDK" Error

**Problem**: Frontend can't load Google Sign-In library

**Solutions**:
- Check internet connection
- Verify Google Client ID is correct
- Check browser console for blocked scripts
- Try clearing browser cache

## Production Deployment

### Backend Configuration

1. Update `.env` for production:

```bash
# Environment
ENVIRONMENT=production

# OAuth2 Configuration
GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-production-client-secret

# JWT Secret (use a different key for production!)
JWT_SECRET_KEY=your-production-secret-key-here

# Frontend URL (your production domain)
FRONTEND_URL=https://app.yourdomain.com

# API Base URL
API_BASE_URL=https://api.yourdomain.com

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

2. Update Google Console redirect URIs:
   - Add production frontend callback: `https://app.yourdomain.com/auth/callback`
   - Add production backend callback: `https://api.yourdomain.com/api/v1/auth/google/callback`

### Frontend Configuration

1. Update `.env.local` for production:

```bash
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
NEXT_PUBLIC_ENVIRONMENT=production
```

2. Build and deploy:

```bash
npm run build
npm start
```

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `.env` and `.env.local` to `.gitignore`
   - Use environment variables or secrets management

2. **Use different credentials for development and production**
   - Create separate OAuth clients in Google Console
   - Use different JWT secret keys

3. **Enable HTTPS in production**
   - Use SSL/TLS certificates
   - Update all URLs to use `https://`
   - Set `secure=True` for cookies

4. **Rotate secrets regularly**
   - Change JWT_SECRET_KEY periodically
   - Rotate OAuth client secrets
   - Invalidate old tokens when rotating

5. **Monitor authentication logs**
   - Check for failed login attempts
   - Monitor token validation errors
   - Set up alerts for suspicious activity

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Websites](https://developers.google.com/identity/gsi/web)
- [DRYAD.AI OAuth2 Setup Guide](docs/OAUTH2_SETUP_GUIDE.md)

## Support

If you encounter issues not covered in this guide:

1. Check the backend logs: `logs/gremlins_app.log`
2. Check the frontend console in browser DevTools
3. Review the [Troubleshooting Guide](TROUBLESHOOTING.md)
4. Open an issue on GitHub with:
   - Error messages
   - Configuration (without secrets!)
   - Steps to reproduce

