#!/usr/bin/env python3
"""
Start the DRYAD.AI server with OAuth2 support.
"""

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("🚀 Starting DRYAD.AI server with OAuth2 support...")
    print("📋 OAuth2 endpoints available:")
    print("   - GET  /api/v1/auth/config")
    print("   - POST /api/v1/auth/token")
    print("   - GET  /api/v1/auth/me")
    print("   - GET  /api/v1/auth/verify")
    print("   - POST /api/v1/auth/logout")
    print("\n🌐 Server will be available at:")
    print("   - API: http://localhost:8000")
    print("   - Docs: http://localhost:8000/docs")
    print("   - OAuth2 Config: http://localhost:8000/api/v1/auth/config")
    print("\n🔐 Ready for Google OAuth2 testing!")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
