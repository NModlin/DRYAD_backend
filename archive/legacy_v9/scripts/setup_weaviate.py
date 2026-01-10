#!/usr/bin/env python3
"""
Weaviate Setup Script for DRYAD.AI

This script helps set up Weaviate vector database for DRYAD.AI.
It can start Weaviate using Docker and configure the schema.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is installed")
            
            # Check if Docker daemon is running
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running")
                print("💡 Start Docker Desktop or run: sudo systemctl start docker")
                return False
        else:
            print("❌ Docker is not installed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        print("💡 Install Docker from: https://docs.docker.com/get-docker/")
        return False

def check_weaviate_running():
    """Check if Weaviate is already running."""
    try:
        response = requests.get("http://localhost:8080/v1/meta", timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate is already running")
            return True
        else:
            return False
    except:
        return False

def start_weaviate():
    """Start Weaviate using Docker Compose."""
    print("🚀 Starting Weaviate with Docker...")
    
    # Create docker-compose.yml for Weaviate
    docker_compose_content = """version: '3.4'
services:
  weaviate:
    command:
    - --host
    - 0.0.0.0
    - --port
    - '8080'
    - --scheme
    - http
    image: semitechnologies/weaviate:1.24.1
    ports:
    - "8080:8080"
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-cohere,text2vec-huggingface,text2vec-palm,text2vec-openai,generative-openai,generative-cohere,generative-palm,ref2vec-centroid,reranker-cohere,qna-openai'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
volumes:
  weaviate_data:
"""
    
    # Write docker-compose.yml
    with open("docker-compose.weaviate.yml", "w") as f:
        f.write(docker_compose_content)
    
    try:
        # Start Weaviate
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.weaviate.yml", "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Weaviate container started")
            
            # Wait for Weaviate to be ready
            print("⏳ Waiting for Weaviate to be ready...")
            for i in range(30):
                if check_weaviate_running():
                    print("✅ Weaviate is ready!")
                    return True
                time.sleep(2)
                print(f"   Waiting... ({i+1}/30)")
            
            print("❌ Weaviate failed to start within 60 seconds")
            return False
        else:
            print(f"❌ Failed to start Weaviate: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Weaviate: {e}")
        return False

def test_weaviate_connection():
    """Test connection to Weaviate and create schema."""
    print("🔍 Testing Weaviate connection...")
    
    try:
        from app.core.vector_store import create_vector_store
        
        # Create vector store instance
        vector_store = create_vector_store()
        
        if vector_store.is_connected:
            print("✅ Successfully connected to Weaviate")
            
            # Get capabilities
            capabilities = vector_store.get_capabilities()
            print(f"📊 Capabilities:")
            for capability, available in capabilities.items():
                status = "✅" if available else "❌"
                print(f"   {status} {capability}")
            
            # Get collection info
            info = vector_store.get_collection_info()
            print(f"📋 Collection Info: {info}")
            
            return True
        else:
            print("❌ Failed to connect to Weaviate")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Weaviate: {e}")
        return False

def setup_environment():
    """Update .env file with Weaviate configuration."""
    print("🔧 Setting up environment configuration...")
    
    env_path = Path(".env")
    
    # Read existing .env if it exists
    existing_env = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Update with Weaviate settings
    existing_env.update({
        'WEAVIATE_URL': 'http://localhost:8080',
        'WEAVIATE_CLASS_NAME': 'GremlinsDocument',
        'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
        'USE_CLIP': 'true'
    })
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.write("# DRYAD.AI Configuration\n")
        f.write("# Updated by setup_weaviate.py\n\n")
        for key, value in existing_env.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Environment configuration saved to {env_path}")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🧙‍♂️ DRYAD.AI Weaviate Setup")
    print("=" * 60)
    
    # Step 1: Check Docker
    if not check_docker():
        return False
    
    # Step 2: Check if Weaviate is already running
    if not check_weaviate_running():
        # Step 3: Start Weaviate
        if not start_weaviate():
            return False
    
    # Step 4: Test connection and create schema
    if not test_weaviate_connection():
        return False
    
    # Step 5: Setup environment
    setup_environment()
    
    print("\n🎉 Weaviate setup complete!")
    print("💡 You can now use DRYAD.AI with vector search capabilities")
    print("🔗 Weaviate Console: http://localhost:8080/v1/meta")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
