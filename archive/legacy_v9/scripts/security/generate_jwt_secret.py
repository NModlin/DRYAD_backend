#!/usr/bin/env python3
"""
Generate a secure JWT secret key and update .env file
"""

import secrets
import os
import shutil
from datetime import datetime

def generate_secure_jwt_key():
    """Generate a cryptographically secure JWT key."""
    return secrets.token_urlsafe(48)

def backup_env_file():
    """Create a backup of the existing .env file."""
    if os.path.exists('.env'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'.env.backup.{timestamp}'
        shutil.copy('.env', backup_name)
        print(f"✅ Backed up .env to {backup_name}")
        return True
    return False

def update_env_file(jwt_secret):
    """Update the .env file with the new JWT secret."""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    # Read current .env content
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update JWT_SECRET_KEY line
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('JWT_SECRET_KEY='):
            lines[i] = f'JWT_SECRET_KEY="{jwt_secret}"\n'
            updated = True
            break
    
    # If JWT_SECRET_KEY wasn't found, add it
    if not updated:
        lines.append(f'\n# Secure JWT Secret Key (Generated {datetime.now().isoformat()})\n')
        lines.append(f'JWT_SECRET_KEY="{jwt_secret}"\n')
    
    # Write updated content back
    with open('.env', 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated JWT_SECRET_KEY in .env")
    print(f"   Key preview: {jwt_secret[:20]}...")
    return True

def add_optional_configs():
    """Add optional configuration settings to .env if they don't exist."""
    configs_to_add = [
        ("\n# Text-to-Speech Configuration", [
            "TTS_ENGINE=espeak",
            "TTS_VOICE=en",
            "TTS_SPEED=175"
        ]),
        ("\n# Enhanced Multimodal Processing", [
            "ENABLE_MULTIMODAL=true",
            "WHISPER_MODEL=base",
            "FFMPEG_PATH=/usr/bin/ffmpeg"
        ]),
        ("\n# Redis Configuration (Optional)", [
            "REDIS_HOST=localhost",
            "REDIS_PORT=6379"
        ])
    ]
    
    # Read current .env content
    with open('.env', 'r') as f:
        content = f.read()
    
    additions = []
    for section_comment, config_lines in configs_to_add:
        # Check if any of the config lines already exist
        if not any(line.split('=')[0] in content for line in config_lines):
            additions.append(section_comment)
            additions.extend(config_lines)
    
    if additions:
        with open('.env', 'a') as f:
            f.write('\n')
            for addition in additions:
                f.write(addition + '\n')
        print(f"✅ Added {len([a for a in additions if '=' in a])} optional configuration settings")

def main():
    print("🔐 DRYAD.AI JWT Secret Key Generator")
    print("=====================================")
    print()
    
    # Generate secure JWT key
    jwt_secret = generate_secure_jwt_key()
    print(f"🔑 Generated secure JWT key: {jwt_secret[:20]}...")
    
    # Backup existing .env
    backup_env_file()
    
    # Update .env file
    if update_env_file(jwt_secret):
        print("✅ JWT secret key updated successfully")
    else:
        print("❌ Failed to update JWT secret key")
        return
    
    # Add optional configurations
    add_optional_configs()
    
    print()
    print("🎉 Configuration Update Complete!")
    print()
    print("Next steps:")
    print("1. Install eSpeak: sudo apt install espeak espeak-data")
    print("2. Test the configuration:")
    print("   python -c 'from app.main import app; print(\"✅ No more JWT warnings!\")'")
    print()

if __name__ == "__main__":
    main()
