#!/usr/bin/env python3
"""
Interactive Google OAuth Setup Script for DRYAD.AI

This script helps you set up Google OAuth authentication by:
1. Checking existing configuration
2. Guiding you through Google Cloud Console setup
3. Updating environment files
4. Validating the configuration

Usage:
    python scripts/setup_google_oauth.py
"""

import os
import sys
import secrets
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(number, text):
    """Print a step number."""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)

def print_success(text):
    """Print success message."""
    print(f"✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"✗ {text}")

def print_info(text):
    """Print info message."""
    print(f"  {text}")

def check_existing_config():
    """Check if OAuth is already configured."""
    print_header("Checking Existing Configuration")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error(".env file not found")
        return None
    
    # Read existing .env
    config = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key] = value.strip('"').strip("'")
    
    # Check OAuth config
    has_client_id = bool(config.get("GOOGLE_CLIENT_ID"))
    has_client_secret = bool(config.get("GOOGLE_CLIENT_SECRET"))
    has_jwt_secret = bool(config.get("JWT_SECRET_KEY"))
    
    if has_client_id:
        print_success(f"GOOGLE_CLIENT_ID is set: {config['GOOGLE_CLIENT_ID'][:20]}...")
    else:
        print_error("GOOGLE_CLIENT_ID is not set")
    
    if has_client_secret:
        print_success("GOOGLE_CLIENT_SECRET is set")
    else:
        print_error("GOOGLE_CLIENT_SECRET is not set")
    
    if has_jwt_secret:
        print_success("JWT_SECRET_KEY is set")
    else:
        print_error("JWT_SECRET_KEY is not set")
    
    return config

def guide_google_console_setup():
    """Guide user through Google Console setup."""
    print_header("Google Cloud Console Setup Guide")
    
    print("You need to create OAuth 2.0 credentials in Google Cloud Console.")
    print("\nFollow these steps:\n")
    
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google+ API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google+ API'")
    print("   - Click 'Enable'")
    print("\n4. Configure OAuth consent screen:")
    print("   - Go to 'APIs & Services' > 'OAuth consent screen'")
    print("   - Select 'External' user type")
    print("   - Fill in app name: 'DRYAD.AI'")
    print("   - Add your email addresses")
    print("   - Add scopes: openid, email, profile")
    print("   - Add test users (your email)")
    print("\n5. Create OAuth 2.0 credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Select 'Web application'")
    print("   - Name: 'DRYAD.AI Web Client'")
    print("   - Authorized JavaScript origins:")
    print("     * http://localhost:3000")
    print("     * http://localhost:8000")
    print("   - Authorized redirect URIs:")
    print("     * http://localhost:3000/auth/callback")
    print("     * http://localhost:8000/api/v1/auth/google/callback")
    print("   - Click 'Create'")
    print("\n6. Copy the Client ID and Client Secret")
    
    input("\nPress Enter when you have completed these steps...")

def get_oauth_credentials():
    """Get OAuth credentials from user."""
    print_header("Enter OAuth Credentials")
    
    print("Paste your Google OAuth credentials below:")
    print("(You can find these in Google Cloud Console > Credentials)\n")
    
    client_id = input("Google Client ID: ").strip()
    if not client_id:
        print_error("Client ID cannot be empty")
        return None, None
    
    client_secret = input("Google Client Secret: ").strip()
    if not client_secret:
        print_error("Client Secret cannot be empty")
        return None, None
    
    # Validate format
    if not client_id.endswith(".apps.googleusercontent.com"):
        print_error("Client ID should end with .apps.googleusercontent.com")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return None, None
    
    return client_id, client_secret

def generate_jwt_secret():
    """Generate a secure JWT secret."""
    print_header("Generating JWT Secret Key")
    
    secret = secrets.token_urlsafe(48)
    print_success(f"Generated secure JWT secret key ({len(secret)} characters)")
    print_info("This key will be used to sign authentication tokens")
    
    return secret

def update_env_file(client_id, client_secret, jwt_secret):
    """Update .env file with OAuth configuration."""
    print_header("Updating Configuration Files")
    
    env_path = Path(".env")
    
    # Read existing .env
    lines = []
    if env_path.exists():
        with open(env_path) as f:
            lines = f.readlines()
    
    # Update or add OAuth config
    updated = {
        "GOOGLE_CLIENT_ID": False,
        "GOOGLE_CLIENT_SECRET": False,
        "JWT_SECRET_KEY": False,
        "FRONTEND_URL": False,
        "API_BASE_URL": False,
    }
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("GOOGLE_CLIENT_ID="):
            new_lines.append(f'GOOGLE_CLIENT_ID="{client_id}"\n')
            updated["GOOGLE_CLIENT_ID"] = True
        elif stripped.startswith("GOOGLE_CLIENT_SECRET="):
            new_lines.append(f'GOOGLE_CLIENT_SECRET="{client_secret}"\n')
            updated["GOOGLE_CLIENT_SECRET"] = True
        elif stripped.startswith("JWT_SECRET_KEY=") and jwt_secret:
            new_lines.append(f'JWT_SECRET_KEY="{jwt_secret}"\n')
            updated["JWT_SECRET_KEY"] = True
        elif stripped.startswith("FRONTEND_URL="):
            new_lines.append(line)
            updated["FRONTEND_URL"] = True
        elif stripped.startswith("API_BASE_URL="):
            new_lines.append(line)
            updated["API_BASE_URL"] = True
        else:
            new_lines.append(line)
    
    # Add missing config
    if not updated["GOOGLE_CLIENT_ID"]:
        new_lines.append(f'\nGOOGLE_CLIENT_ID="{client_id}"\n')
    if not updated["GOOGLE_CLIENT_SECRET"]:
        new_lines.append(f'GOOGLE_CLIENT_SECRET="{client_secret}"\n')
    if not updated["JWT_SECRET_KEY"] and jwt_secret:
        new_lines.append(f'JWT_SECRET_KEY="{jwt_secret}"\n')
    if not updated["FRONTEND_URL"]:
        new_lines.append('FRONTEND_URL="http://localhost:3000"\n')
    if not updated["API_BASE_URL"]:
        new_lines.append('API_BASE_URL="http://localhost:8000"\n')
    
    # Write updated .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print_success("Updated backend .env file")
    
    # Update frontend .env.local
    frontend_env = Path("frontend/writer-portal/.env.local")
    frontend_env.parent.mkdir(parents=True, exist_ok=True)
    
    with open(frontend_env, 'w') as f:
        f.write("# Frontend Environment Configuration\n")
        f.write("# Auto-generated by setup_google_oauth.py\n\n")
        f.write("NEXT_PUBLIC_API_BASE=http://localhost:8000\n")
        f.write(f'NEXT_PUBLIC_GOOGLE_CLIENT_ID={client_id}\n')
        f.write("NEXT_PUBLIC_ENVIRONMENT=development\n")
    
    print_success("Updated frontend .env.local file")

def print_next_steps():
    """Print next steps for user."""
    print_header("Setup Complete!")
    
    print("✓ OAuth credentials configured")
    print("✓ JWT secret key generated")
    print("✓ Environment files updated")
    
    print("\nNext steps:")
    print("\n1. Start the backend server:")
    print("   python start.py")
    
    print("\n2. In a new terminal, start the frontend:")
    print("   cd frontend/writer-portal")
    print("   npm install  # if not already done")
    print("   npm run dev")
    
    print("\n3. Open your browser:")
    print("   http://localhost:3000")
    
    print("\n4. Click 'Sign in with Google' and test the OAuth flow")
    
    print("\n5. Validate the setup:")
    print("   python scripts/validate_oauth_setup.py")
    
    print("\nFor troubleshooting, see: GOOGLE_OAUTH_SETUP.md")

def main():
    """Main setup flow."""
    print_header("DRYAD.AI Google OAuth Setup")
    print("This script will help you configure Google OAuth authentication")
    
    # Check existing config
    existing_config = check_existing_config()
    
    if existing_config and existing_config.get("GOOGLE_CLIENT_ID"):
        print("\nOAuth appears to be already configured.")
        reconfigure = input("Do you want to reconfigure? (y/n): ").lower()
        if reconfigure != 'y':
            print("\nSetup cancelled. Your existing configuration is unchanged.")
            return 0
    
    # Guide through Google Console
    guide_google_console_setup()
    
    # Get credentials
    client_id, client_secret = get_oauth_credentials()
    if not client_id or not client_secret:
        print_error("\nSetup cancelled. Invalid credentials.")
        return 1
    
    # Generate JWT secret if needed
    jwt_secret = None
    if not existing_config or not existing_config.get("JWT_SECRET_KEY"):
        jwt_secret = generate_jwt_secret()
    
    # Update configuration files
    update_env_file(client_id, client_secret, jwt_secret)
    
    # Print next steps
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)

