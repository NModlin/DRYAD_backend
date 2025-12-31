#!/usr/bin/env python3
"""
DRYAD.AI Backend Setup Script
Automated setup for different deployment modes.
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_requirements():
    """Check if required tools are installed."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if Docker is available (optional)
    try:
        result = run_command("docker --version", check=False)
        if result.returncode == 0:
            print("✅ Docker available")
        else:
            print("⚠️ Docker not available (optional for local development)")
    except:
        print("⚠️ Docker not available (optional for local development)")
    
    return True

def setup_basic_mode():
    """Set up basic mode (no external services)."""
    print("\n🚀 Setting up Basic Mode...")
    
    # Create virtual environment
    if not os.path.exists(".venv"):
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv .venv")
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = ".venv\\Scripts\\activate"
        pip_cmd = ".venv\\Scripts\\pip"
        python_cmd = ".venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        activate_script = ".venv/bin/activate"
        pip_cmd = ".venv/bin/pip"
        python_cmd = ".venv/bin/python"
    
    # Install minimal dependencies
    print("Installing minimal dependencies...")
    run_command(f"{pip_cmd} install -r requirements-minimal.txt")
    
    # Set up environment file
    if not os.path.exists(".env"):
        print("Creating .env file...")
        shutil.copy(".env.example", ".env")
        
        # Update .env for basic mode
        with open(".env", "a") as f:
            f.write("\n# Basic Mode Configuration\n")
            f.write("BASIC_MODE=true\n")
            f.write("DATABASE_URL=sqlite:///./gremlins.db\n")
    
    # Initialize database
    print("Initializing database...")
    run_command(f"{python_cmd} -c \"from alembic.config import Config; from alembic import command; alembic_cfg = Config('alembic.ini'); command.upgrade(alembic_cfg, 'head')\"")
    
    print("\n✅ Basic mode setup complete!")
    print("\nTo start the server:")
    print(f"1. Activate virtual environment: {activate_script}")
    print("2. Run: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
    print("3. Open: http://localhost:8000/docs")

def setup_docker_basic():
    """Set up Docker basic mode."""
    print("\n🐳 Setting up Docker Basic Mode...")
    
    # Build and run basic Docker setup
    run_command("docker-compose -f docker-compose.basic.yml build")
    run_command("docker-compose -f docker-compose.basic.yml up -d")
    
    print("\n✅ Docker basic mode setup complete!")
    print("Server running at: http://localhost:8000/docs")
    print("To stop: docker-compose -f docker-compose.basic.yml down")

def setup_docker_full():
    """Set up Docker full mode with all services."""
    print("\n🐳 Setting up Docker Full Mode...")
    
    # Build and run full Docker setup
    run_command("docker-compose -f docker-compose.full.yml build")
    run_command("docker-compose -f docker-compose.full.yml up -d")
    
    print("\n✅ Docker full mode setup complete!")
    print("Services running:")
    print("- Backend: http://localhost:8000/docs")
    print("- Weaviate: http://localhost:8080")
    print("- Redis: localhost:6379")
    print("- Ollama: http://localhost:11434")
    print("\nTo stop: docker-compose -f docker-compose.full.yml down")

def setup_development():
    """Set up full development environment."""
    print("\n🛠️ Setting up Development Environment...")
    
    # Create virtual environment
    if not os.path.exists(".venv"):
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv .venv")
    
    # Determine pip command
    pip_cmd = ".venv\\Scripts\\pip" if os.name == 'nt' else ".venv/bin/pip"
    python_cmd = ".venv\\Scripts\\python" if os.name == 'nt' else ".venv/bin/python"
    
    # Install full dependencies
    print("Installing full dependencies...")
    run_command(f"{pip_cmd} install -r requirements.txt")
    
    # Set up environment file
    if not os.path.exists(".env"):
        print("Creating .env file...")
        shutil.copy(".env.example", ".env")
    
    # Initialize database
    print("Initializing database...")
    run_command(f"{python_cmd} -c \"from alembic.config import Config; from alembic import command; alembic_cfg = Config('alembic.ini'); command.upgrade(alembic_cfg, 'head')\"")
    
    print("\n✅ Development environment setup complete!")
    print("\nNext steps:")
    print("1. Configure external services (Weaviate, Redis, Ollama)")
    print("2. Update .env with service URLs and API keys")
    print("3. Run: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="DRYAD.AI Backend Setup")
    parser.add_argument("mode", choices=["basic", "docker-basic", "docker-full", "development"], 
                       help="Setup mode")
    
    args = parser.parse_args()
    
    print("🧙‍♂️ DRYAD.AI Backend Setup")
    print("=" * 40)
    
    if not check_requirements():
        sys.exit(1)
    
    if args.mode == "basic":
        setup_basic_mode()
    elif args.mode == "docker-basic":
        setup_docker_basic()
    elif args.mode == "docker-full":
        setup_docker_full()
    elif args.mode == "development":
        setup_development()
    
    print("\n🎉 Setup complete!")

if __name__ == "__main__":
    main()
