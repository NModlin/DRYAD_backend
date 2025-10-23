#!/usr/bin/env python3
"""
OAuth Setup Validation Script for DRYAD.AI

This script validates that Google OAuth is properly configured for both
backend and frontend components.

Usage:
    python scripts/validate_oauth_setup.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_success(text):
    """Print success message."""
    print(f"✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"✗ {text}")

def print_warning(text):
    """Print warning message."""
    print(f"⚠ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")

def check_env_file():
    """Check if .env file exists and is readable."""
    print_header("Checking Environment Configuration")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error(".env file not found")
        print_info("Copy .env.example to .env and configure it:")
        print_info("  cp .env.example .env")
        return False
    
    print_success(".env file exists")
    return True

def check_google_credentials():
    """Check Google OAuth credentials."""
    print_header("Checking Google OAuth Credentials")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    issues = []
    
    if not client_id:
        print_error("GOOGLE_CLIENT_ID is not set")
        issues.append("GOOGLE_CLIENT_ID")
    elif client_id == "your-google-client-id-here":
        print_error("GOOGLE_CLIENT_ID is still set to placeholder value")
        issues.append("GOOGLE_CLIENT_ID")
    else:
        print_success(f"GOOGLE_CLIENT_ID is set: {client_id[:20]}...")
    
    if not client_secret:
        print_error("GOOGLE_CLIENT_SECRET is not set")
        issues.append("GOOGLE_CLIENT_SECRET")
    elif client_secret == "your-google-client-secret-here":
        print_error("GOOGLE_CLIENT_SECRET is still set to placeholder value")
        issues.append("GOOGLE_CLIENT_SECRET")
    else:
        print_success("GOOGLE_CLIENT_SECRET is set")
    
    if issues:
        print_info("\nTo fix these issues:")
        print_info("1. Go to https://console.cloud.google.com/")
        print_info("2. Create OAuth 2.0 credentials")
        print_info("3. Add the credentials to your .env file")
        print_info("4. See GOOGLE_OAUTH_SETUP.md for detailed instructions")
        return False
    
    return True

def check_jwt_secret():
    """Check JWT secret key configuration."""
    print_header("Checking JWT Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if not jwt_secret:
        if environment in ["production", "staging"]:
            print_error("JWT_SECRET_KEY is not set (REQUIRED for production)")
            print_info("Generate a secure key:")
            print_info("  python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
            return False
        else:
            print_warning("JWT_SECRET_KEY is not set (will use temporary key)")
            print_info("For consistent tokens, set JWT_SECRET_KEY in .env")
    else:
        # Check if it's a placeholder
        insecure_values = [
            "your-secret-key-change-in-production",
            "your-super-secret-jwt-key-change-in-production",
            "test-jwt-secret-key-for-testing-only",
            "development-jwt-secret",
            "jwt-secret-key"
        ]
        
        if jwt_secret in insecure_values:
            print_error("JWT_SECRET_KEY is set to an insecure default value")
            print_info("Generate a secure key:")
            print_info("  python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
            return False
        
        if len(jwt_secret) < 32:
            print_warning(f"JWT_SECRET_KEY is short ({len(jwt_secret)} chars, recommend 48+)")
        else:
            print_success(f"JWT_SECRET_KEY is set ({len(jwt_secret)} chars)")
    
    return True

def check_frontend_url():
    """Check frontend URL configuration."""
    print_header("Checking Frontend URL Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    environment = os.getenv("ENVIRONMENT", "development")
    
    print_info(f"FRONTEND_URL: {frontend_url}")
    print_info(f"ENVIRONMENT: {environment}")
    
    if environment in ["production", "staging"]:
        if "localhost" in frontend_url:
            print_warning("Using localhost URL in production environment")
            print_info("Set FRONTEND_URL to your production domain")
            return False
        if not frontend_url.startswith("https://"):
            print_warning("Production frontend URL should use HTTPS")
            return False
    
    print_success("Frontend URL configuration looks good")
    return True

async def check_backend_server():
    """Check if backend server is running and OAuth is configured."""
    print_header("Checking Backend Server")
    
    try:
        import httpx
        
        # Try to connect to backend
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print_success("Backend server is running")
                else:
                    print_warning(f"Backend server returned status {response.status_code}")
            except httpx.ConnectError:
                print_error("Cannot connect to backend server at http://localhost:8000")
                print_info("Start the backend server:")
                print_info("  python start.py")
                return False
            
            # Check OAuth config endpoint
            try:
                response = await client.get("http://localhost:8000/api/v1/auth/config")
                if response.status_code == 200:
                    config = response.json()
                    print_success("OAuth config endpoint is accessible")
                    print_info(f"  Client ID: {config.get('google_client_id', 'N/A')[:20]}...")
                    print_info(f"  Redirect URI: {config.get('redirect_uri', 'N/A')}")
                    return True
                elif response.status_code == 500:
                    print_error("OAuth is not configured on backend")
                    print_info("Set GOOGLE_CLIENT_ID in .env file")
                    return False
                else:
                    print_warning(f"OAuth config endpoint returned status {response.status_code}")
                    return False
            except Exception as e:
                print_error(f"Failed to check OAuth config: {e}")
                return False
                
    except ImportError:
        print_warning("httpx not installed, skipping backend server check")
        print_info("Install with: pip install httpx")
        return True

def check_frontend_config():
    """Check frontend configuration."""
    print_header("Checking Frontend Configuration")
    
    frontend_path = Path("frontend/writer-portal")
    if not frontend_path.exists():
        print_warning("Frontend directory not found")
        return True
    
    env_local = frontend_path / ".env.local"
    env_example = frontend_path / ".env.local.example"
    
    if not env_local.exists():
        print_warning(".env.local not found in frontend directory")
        if env_example.exists():
            print_info("Copy the example file:")
            print_info(f"  cp {env_example} {env_local}")
        else:
            print_info("Create .env.local with:")
            print_info("  NEXT_PUBLIC_API_BASE=http://localhost:8000")
            print_info("  NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id")
        return False
    
    print_success("Frontend .env.local exists")
    
    # Try to read and validate
    try:
        with open(env_local) as f:
            content = f.read()
            
        if "NEXT_PUBLIC_API_BASE" not in content:
            print_warning("NEXT_PUBLIC_API_BASE not set in frontend .env.local")
        else:
            print_success("NEXT_PUBLIC_API_BASE is configured")
            
        if "NEXT_PUBLIC_GOOGLE_CLIENT_ID" not in content:
            print_warning("NEXT_PUBLIC_GOOGLE_CLIENT_ID not set in frontend .env.local")
        else:
            print_success("NEXT_PUBLIC_GOOGLE_CLIENT_ID is configured")
            
    except Exception as e:
        print_error(f"Failed to read frontend .env.local: {e}")
        return False
    
    return True

def print_summary(results):
    """Print validation summary."""
    print_header("Validation Summary")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for check, result in results.items():
        if result:
            print_success(check)
        else:
            print_error(check)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if passed == total:
        print_success("\n🎉 All checks passed! OAuth should be working correctly.")
        print_info("\nNext steps:")
        print_info("1. Start the backend: python start.py")
        print_info("2. Start the frontend: cd frontend/writer-portal && npm run dev")
        print_info("3. Open http://localhost:3000 and test Google Sign-In")
    else:
        print_error("\n❌ Some checks failed. Please fix the issues above.")
        print_info("\nFor detailed setup instructions, see:")
        print_info("  GOOGLE_OAUTH_SETUP.md")

async def main():
    """Run all validation checks."""
    print_header("DRYAD.AI OAuth Setup Validation")
    print_info("This script will validate your Google OAuth configuration")
    
    results = {}
    
    # Run checks
    results["Environment file exists"] = check_env_file()
    results["Google credentials configured"] = check_google_credentials()
    results["JWT secret configured"] = check_jwt_secret()
    results["Frontend URL configured"] = check_frontend_url()
    results["Backend server accessible"] = await check_backend_server()
    results["Frontend configuration"] = check_frontend_config()
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

