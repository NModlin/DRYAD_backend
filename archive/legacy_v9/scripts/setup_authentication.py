#!/usr/bin/env python3
"""
DRYAD.AI Authentication Setup Script
=====================================

This script helps configure secure authentication for the DRYAD.AI Backend.
It handles JWT secret generation, OAuth2 setup guidance, and security validation.

Usage:
    python setup_authentication.py [--generate-secrets] [--validate] [--setup-oauth]
"""

import os
import sys
import secrets
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

def generate_secure_jwt_secret(length: int = 48) -> str:
    """Generate a cryptographically secure JWT secret key."""
    return secrets.token_urlsafe(length)

def validate_current_config() -> Tuple[bool, List[str]]:
    """Validate current authentication configuration."""
    issues = []
    
    # Check JWT secret
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        issues.append("❌ JWT_SECRET_KEY is not set")
    elif len(jwt_secret) < 32:
        issues.append("⚠️  JWT_SECRET_KEY is shorter than recommended 32 characters")
    elif jwt_secret in ["your-super-secret-jwt-key-change-in-production", "change-me"]:
        issues.append("❌ JWT_SECRET_KEY is using insecure default value")
    else:
        print("✅ JWT_SECRET_KEY is properly configured")
    
    # Check OAuth2 configuration
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not google_client_id or not google_client_secret:
        issues.append("⚠️  Google OAuth2 credentials not configured (optional)")
    elif google_client_id.startswith("818968828866-") or "example" in google_client_id.lower():
        issues.append("❌ Google OAuth2 using example/test credentials - SECURITY RISK")
    else:
        print("✅ Google OAuth2 credentials configured")
    
    # Check algorithm
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if jwt_algorithm != "HS256":
        issues.append(f"⚠️  JWT_ALGORITHM is {jwt_algorithm}, recommended: HS256")
    else:
        print("✅ JWT algorithm is secure")
    
    # Check expiration
    jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    if jwt_expiration > 168:  # 1 week
        issues.append(f"⚠️  JWT expiration is {jwt_expiration} hours (very long)")
    else:
        print(f"✅ JWT expiration is reasonable: {jwt_expiration} hours")
    
    return len(issues) == 0, issues

def update_env_file(updates: Dict[str, str]) -> bool:
    """Update .env file with new values."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Read current content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update lines
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key = line.split('=')[0].strip()
            if key in updates:
                updated_lines.append(f'{key}="{updates[key]}"\n')
                updated_keys.add(key)
            else:
                updated_lines.append(line + '\n')
        else:
            updated_lines.append(line + '\n')
    
    # Add any new keys that weren't found
    for key, value in updates.items():
        if key not in updated_keys:
            updated_lines.append(f'{key}="{value}"\n')
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Updated .env file with {len(updates)} changes")
    return True

def setup_oauth2_guidance():
    """Provide step-by-step OAuth2 setup guidance."""
    print("\n" + "="*60)
    print("🔐 GOOGLE OAUTH2 SETUP GUIDE")
    print("="*60)
    
    print("\n1. 📋 Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    
    print("\n2. 🏗️  Create or Select Project:")
    print("   - Create new project or select existing")
    print("   - Name: 'DRYAD.AI' or your preferred name")
    
    print("\n3. 🔌 Enable APIs:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Enable 'Google+ API'")
    print("   - Enable 'OAuth2 API'")
    
    print("\n4. 🛡️  Configure OAuth Consent Screen:")
    print("   - Go to 'APIs & Services' > 'OAuth consent screen'")
    print("   - Choose 'External' (for testing)")
    print("   - App name: 'DRYAD.AI'")
    print("   - User support email: your email")
    print("   - Authorized domains: localhost (for development)")
    print("   - Scopes: email, profile, openid")
    
    print("\n5. 🔑 Create OAuth2 Credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("   - Application type: 'Web application'")
    print("   - Name: 'DRYAD.AI Backend'")
    print("   - Authorized redirect URIs:")
    print("     * http://localhost:8000/api/v1/auth/google/callback")
    print("     * http://localhost:3000/auth/callback (for frontend)")
    
    print("\n6. 📝 Copy Credentials:")
    print("   - Copy 'Client ID' and 'Client Secret'")
    print("   - Update your .env file:")
    print("     GOOGLE_CLIENT_ID=\"your-client-id.apps.googleusercontent.com\"")
    print("     GOOGLE_CLIENT_SECRET=\"your-client-secret\"")
    
    print("\n7. 🧪 Test Configuration:")
    print("   - Run: python setup_authentication.py --validate")
    print("   - Test endpoint: http://localhost:8000/api/v1/auth/config")
    
    print("\n" + "="*60)
    print("⚠️  SECURITY NOTES:")
    print("- Never commit real OAuth2 credentials to version control")
    print("- Use environment variables or secure secret management")
    print("- For production, use HTTPS redirect URIs")
    print("- Regularly rotate JWT secrets")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Setup DRYAD.AI Authentication")
    parser.add_argument("--generate-secrets", action="store_true", 
                       help="Generate new secure JWT secret")
    parser.add_argument("--validate", action="store_true",
                       help="Validate current authentication configuration")
    parser.add_argument("--setup-oauth", action="store_true",
                       help="Show OAuth2 setup guidance")
    parser.add_argument("--fix-config", action="store_true",
                       help="Automatically fix common configuration issues")
    
    args = parser.parse_args()
    
    # Load environment variables from .env if it exists
    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded configuration from .env file")
    else:
        print("⚠️  No .env file found")
    
    if args.generate_secrets:
        print("\n🔐 GENERATING SECURE SECRETS")
        print("="*40)
        
        jwt_secret = generate_secure_jwt_secret()
        print(f"New JWT Secret: {jwt_secret}")
        print(f"Length: {len(jwt_secret)} characters")
        
        if input("\nUpdate .env file with new secret? (y/N): ").lower() == 'y':
            if update_env_file({"JWT_SECRET_KEY": jwt_secret, "SECRET_KEY": jwt_secret}):
                print("✅ JWT secret updated in .env file")
            else:
                print("❌ Failed to update .env file")
    
    if args.validate:
        print("\n🔍 VALIDATING AUTHENTICATION CONFIGURATION")
        print("="*50)
        
        is_valid, issues = validate_current_config()
        
        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"   {issue}")
        
        if is_valid:
            print("\n🎉 Authentication configuration is valid!")
        else:
            print(f"\n❌ Found {len(issues)} configuration issues")
            print("   Run with --fix-config to automatically fix common issues")
    
    if args.setup_oauth:
        setup_oauth2_guidance()
    
    if args.fix_config:
        print("\n🔧 FIXING CONFIGURATION ISSUES")
        print("="*40)
        
        updates = {}
        
        # Fix JWT secret if needed
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret or len(jwt_secret) < 32 or jwt_secret in ["your-super-secret-jwt-key-change-in-production"]:
            new_secret = generate_secure_jwt_secret()
            updates["JWT_SECRET_KEY"] = new_secret
            updates["SECRET_KEY"] = new_secret
            print("✅ Generated new secure JWT secret")
        
        # Fix algorithm if needed
        if os.getenv("JWT_ALGORITHM") != "HS256":
            updates["JWT_ALGORITHM"] = "HS256"
            print("✅ Set JWT algorithm to HS256")
        
        # Fix expiration if too long
        jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        if jwt_expiration > 168:
            updates["JWT_EXPIRATION_HOURS"] = "24"
            print("✅ Set JWT expiration to 24 hours")
        
        if updates:
            if update_env_file(updates):
                print(f"\n🎉 Fixed {len(updates)} configuration issues!")
                print("   Run --validate to confirm fixes")
            else:
                print("\n❌ Failed to update configuration")
        else:
            print("✅ No configuration issues to fix")
    
    if not any([args.generate_secrets, args.validate, args.setup_oauth, args.fix_config]):
        print("DRYAD.AI Authentication Setup")
        print("Usage: python setup_authentication.py --help")
        print("\nQuick commands:")
        print("  --validate      Check current configuration")
        print("  --fix-config    Fix common issues automatically")
        print("  --setup-oauth   Show OAuth2 setup guide")
        print("  --generate-secrets  Generate new JWT secret")

if __name__ == "__main__":
    main()
