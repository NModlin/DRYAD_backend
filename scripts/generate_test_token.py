"""
Generate a test JWT token for Dryad API testing.
"""

import jwt
import secrets
from datetime import datetime, timedelta, timezone

# JWT secret from config (test environment)
JWT_SECRET = "kJ8mN2pQ4rT6wY9zB3eH5jL7nP0sV2xA4cF6hK8mN1pQ3rT5wY7zB9eH2jL4nP6s"
JWT_ALGORITHM = "HS256"

def generate_test_token():
    """Generate a test JWT token for API testing."""
    # Generate a unique token ID
    token_id = secrets.token_urlsafe(16)

    payload = {
        'sub': 'test-user-dryad',
        'user_id': 'test-user-dryad',
        'email': 'dryad@test.com',
        'username': 'dryadtest',
        'name': 'Dryad Test User',
        'role': 'user',
        'roles': ['user'],
        'permissions': ['read', 'write'],
        'iss': 'DRYAD.AI',
        'aud': 'DRYAD.AI-api',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'email_verified': True,
        'jti': token_id,  # JWT ID required by security manager
        'token_type': 'access'
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

if __name__ == "__main__":
    token = generate_test_token()
    print(f"\n🔑 Test JWT Token Generated:\n")
    print(token)
    print(f"\n✅ Token valid for 24 hours")
    print(f"\nUse in requests:")
    print(f'Authorization: Bearer {token}')

