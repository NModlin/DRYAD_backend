"""Debug RADAR Token"""
import jwt
import os

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkcnlhZC10ZXN0LXVzZXIiLCJ1c2VySWQiOiJkcnlhZC10ZXN0LXVzZXIiLCJlbWFpbCI6ImRyeWFkdGVzdEByZWhyaWcuY29tIiwidXNlcm5hbWUiOiJkcnlhZHRlc3QiLCJyb2xlIjoiYWRtaW4iLCJkZXBhcnRtZW50IjoiSVQgU3VwcG9ydCIsImlhdCI6MTc1OTUzMzI0NSwiZXhwIjoxNzU5NjE5NjQ1LCJhdWQiOiJyYWRhci1wbGF0Zm9ybSIsImlzcyI6InJhZGFyLWF1dGgtc2VydmljZSJ9.4_8CFCBlPg14PviE4WfsjRFlziNVjd3BnCy-syRSSmU"

SECRET = "XTGc4v4CL5v2sHUtsgB-OO-Av-tMcleakCzK7p9b5EpvvilZN-T9HnLd4hGL3u30"

print("🔍 Decoding token...")
try:
    # Decode without verification first
    unverified = jwt.decode(TOKEN, options={"verify_signature": False})
    print(f"✅ Token payload (unverified):")
    for key, value in unverified.items():
        print(f"   {key}: {value}")
    
    # Now try with verification
    print(f"\n🔐 Verifying with secret...")
    verified = jwt.decode(
        TOKEN,
        SECRET,
        algorithms=["HS256"],
        audience="radar-platform",
        issuer="radar-auth-service"
    )
    print(f"✅ Token is VALID!")
    print(f"   User: {verified.get('username')}")
    print(f"   Email: {verified.get('email')}")
    
except jwt.ExpiredSignatureError:
    print(f"❌ Token is EXPIRED")
except jwt.InvalidAudienceError as e:
    print(f"❌ Invalid audience: {e}")
except jwt.InvalidIssuerError as e:
    print(f"❌ Invalid issuer: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n📋 Environment check:")
print(f"   RADAR_JWT_SECRET set: {bool(os.getenv('RADAR_JWT_SECRET'))}")
print(f"   Secret matches: {os.getenv('RADAR_JWT_SECRET') == SECRET}")

