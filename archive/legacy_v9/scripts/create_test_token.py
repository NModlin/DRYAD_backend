"""
Create Test Token for Automated Testing

Generates a valid JWT token for testing purposes without requiring OAuth2 flow.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import User, create_access_token


def create_test_token():
    """Create a test token for automated testing."""
    
    # Create a test user
    test_user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        picture=None,
        email_verified=True,
        roles=["user", "admin"],
        permissions=["read", "write", "delete", "admin"],
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow(),
        is_active=True
    )
    
    # Create access token
    token = create_access_token(
        user=test_user,
        client_ip="127.0.0.1",
        user_agent="Test Script"
    )
    
    return token


if __name__ == "__main__":
    token = create_test_token()
    print(token)

