"""
RADAR Integration Diagnostics

Check what's causing the 500 errors.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(url, method="GET", headers=None, data=None):
    """Test an endpoint and show detailed error info."""
    print(f"\nTesting: {method} {url}")
    print("-" * 60)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            body = response.json()
            print(f"Body: {json.dumps(body, indent=2)}")
        except:
            print(f"Body (text): {response.text[:500]}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


print("="*60)
print("RADAR INTEGRATION DIAGNOSTICS")
print("="*60)

# Test 1: Main health (should work)
print("\n1. Testing main health endpoint...")
test_endpoint(f"{BASE_URL}/api/v1/health/status")

# Test 2: RADAR health without auth (should work)
print("\n2. Testing RADAR health endpoint (no auth)...")
test_endpoint(f"{BASE_URL}/api/v1/radar/health")

# Test 3: Check if RADAR router is registered
print("\n3. Testing root endpoint to see registered routers...")
test_endpoint(f"{BASE_URL}/")

# Test 4: Try RADAR health with auth
print("\n4. Testing RADAR health with auth header...")
import jwt
from datetime import datetime, timedelta

token = jwt.encode({
    "sub": "test-user-123",
    "userId": "test-user-123",
    "email": "test@rehrig.com",
    "username": "testuser",
    "role": "user",
    "iss": "radar-auth-service",
    "aud": "radar-platform",
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=1)
}, "kJ8mN2pQ4rT6wY9z", algorithm="HS256")

headers = {"Authorization": f"Bearer {token}"}
test_endpoint(f"{BASE_URL}/api/v1/radar/health", headers=headers)

# Test 5: Try a simple chat message
print("\n5. Testing chat message endpoint...")
data = {
    "conversationId": None,
    "message": "Hello, this is a test",
    "context": {
        "userId": "test-user-123",
        "username": "testuser"
    }
}
test_endpoint(f"{BASE_URL}/api/v1/radar/api/chat/message", method="POST", headers=headers, data=data)

print("\n" + "="*60)
print("DIAGNOSTICS COMPLETE")
print("="*60)
print("\nIf you see 500 errors, check the backend logs for the actual error.")
print("Look for the error IDs in the backend terminal output.")

