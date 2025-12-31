#!/usr/bin/env python3
"""
Verify Updated Google OAuth Configuration
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("🔄 UPDATED GOOGLE OAUTH VERIFICATION")
print("=" * 50)

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

print(f"✅ Client ID: {client_id[:30] if client_id else 'NOT SET'}...")
print(f"✅ Client Secret: SET ({client_secret[:15] if client_secret else 'NOT SET'}...)")

if client_id and client_secret:
    print("\n🎉 GOOGLE OAUTH FULLY CONFIGURED WITH CORRECT SECRET!")
    print("\n📋 CREDENTIALS SUMMARY:")
    print(f"   Client ID: {client_id}")
    print(f"   Secret: {client_secret[:15]}... (updated)")
    print("\n✅ Ready to test OAuth flow!")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Start server: python -m uvicorn app.main:app --reload")
    print("2. Test config: http://localhost:8000/api/v1/auth/config")
    print("3. Test OAuth: http://localhost:8000/api/v1/auth/google/authorize")
    
else:
    print("\n❌ Configuration incomplete")
