#!/usr/bin/env python3
"""
DRYAD.AI Installation Profile Manager

Manages different installation profiles for DRYAD.AI Backend:
- minimal: Core functionality only
- standard: Includes vector database and multi-agent
- full: All features including multimodal processing

Usage:
    python scripts/installation_profiles.py --profile minimal
    python scripts/installation_profiles.py --profile standard  
    python scripts/installation_profiles.py --profile full
    python scripts/installation_profiles.py --list-profiles
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

PROFILES = {
    "minimal": {
        "name": "Minimal Installation",
        "description": "Core AI agent functionality with basic chat and search capabilities",
        "requirements": "requirements-minimal.txt",
        "features": [
            "FastAPI web server",
            "LangGraph AI agent",
            "DuckDuckGo search",
            "SQLite database",
            "Basic chat history",
            "Local LLM support (Ollama)"
        ],
        "size": "~200MB",
        "install_time": "2-3 minutes"
    },
    "standard": {
        "name": "Standard Installation", 
        "description": "Full-featured installation with vector database and multi-agent capabilities",
        "requirements": "requirements-standard.txt",
        "features": [
            "All minimal features",
            "Weaviate vector database",
            "Document management & RAG",
            "Multi-agent workflows (DRYAD built-in)",
            "Task orchestration (Celery)",
            "GraphQL API",
            "WebSocket real-time communication",
            "Advanced search capabilities"
        ],
        "size": "~800MB",
        "install_time": "5-7 minutes"
    },
    "full": {
        "name": "Full Installation",
        "description": "Complete installation with all multimodal processing capabilities",
        "requirements": "requirements-full.txt", 
        "features": [
            "All standard features",
            "Multimodal processing (audio, video, images)",
            "CLIP embeddings for cross-modal search",
            "Speech-to-text (Whisper)",
            "Text-to-speech conversion",
            "Computer vision (OpenCV)",
            "PyTorch machine learning",
            "Advanced AI model support"
        ],
        "size": "~3GB",
        "install_time": "10-15 minutes"
    }
}

def list_profiles():
    """List all available installation profiles."""
    print("🚀 DRYAD.AI Installation Profiles")
    print("=" * 60)
    
    for profile_id, profile in PROFILES.items():
        print(f"\n📦 {profile['name']} ({profile_id})")
        print(f"   {profile['description']}")
        print(f"   Size: {profile['size']} | Install time: {profile['install_time']}")
        print("   Features:")
        for feature in profile['features']:
            print(f"     • {feature}")

def install_profile(profile_id: str, upgrade: bool = False):
    """Install a specific profile."""
    if profile_id not in PROFILES:
        print(f"❌ Unknown profile: {profile_id}")
        print("Available profiles:", ", ".join(PROFILES.keys()))
        return False
        
    profile = PROFILES[profile_id]
    requirements_file = profile['requirements']
    
    print(f"🚀 Installing {profile['name']}")
    print("=" * 60)
    print(f"Description: {profile['description']}")
    print(f"Requirements file: {requirements_file}")
    print(f"Estimated size: {profile['size']}")
    print(f"Estimated time: {profile['install_time']}")
    
    # Check if requirements file exists
    if not Path(requirements_file).exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    # Install dependencies
    print(f"\n📦 Installing dependencies from {requirements_file}...")
    
    cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
    if upgrade:
        cmd.append("--upgrade")
        
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        
        # Run post-installation setup
        print("\n🔧 Running post-installation setup...")
        setup_success = run_post_install_setup(profile_id)
        
        if setup_success:
            print(f"\n🎉 {profile['name']} installed successfully!")
            print("\n📋 Next steps:")
            print("1. Copy .env.example to .env and configure your settings")
            print("2. Run: python scripts/validate_setup.py")
            print("3. Start the server: uvicorn app.main:app --reload")
            return True
        else:
            print("\n⚠️  Installation completed but setup had issues")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def run_post_install_setup(profile_id: str) -> bool:
    """Run post-installation setup tasks."""
    success = True
    
    # Initialize database
    try:
        print("  • Initializing database...")
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], 
                      check=True, capture_output=True)
        print("    ✅ Database initialized")
    except subprocess.CalledProcessError:
        print("    ⚠️  Database initialization failed (may need manual setup)")
        success = False
    
    # For standard and full profiles, check external services
    if profile_id in ["standard", "full"]:
        print("  • Checking external services...")
        try:
            # This will be handled by the setup scripts
            print("    💡 Run setup scripts for external services if needed")
        except Exception:
            pass
    
    return success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DRYAD.AI Installation Profile Manager")
    parser.add_argument("--profile", choices=list(PROFILES.keys()),
                       help="Installation profile to use")
    parser.add_argument("--list-profiles", action="store_true",
                       help="List all available profiles")
    parser.add_argument("--upgrade", action="store_true",
                       help="Upgrade existing packages")
    
    args = parser.parse_args()
    
    if args.list_profiles:
        list_profiles()
    elif args.profile:
        success = install_profile(args.profile, args.upgrade)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
