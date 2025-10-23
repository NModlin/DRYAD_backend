#!/usr/bin/env python3
"""
DRYAD.AI Setup Validation Script

Quick validation script to check if DRYAD.AI is properly configured
and ready to use with real LLM capabilities.
"""

import os
import sys
import requests
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found")
        print("💡 Copy .env.example to .env and configure your LLM provider")
        return False
    
    print("✅ .env file found")
    
    # Check for LLM configuration
    llm_configs = [
        ("OLLAMA_BASE_URL", "Ollama"),
        ("OPENAI_API_KEY", "OpenAI"), 
        ("USE_HUGGINGFACE", "HuggingFace")
    ]
    
    configured_providers = []
    for var, provider in llm_configs:
        if os.getenv(var):
            configured_providers.append(provider)
            print(f"✅ {provider} configuration found")
    
    if not configured_providers:
        print("❌ No LLM provider configured")
        print("💡 Set up at least one LLM provider in your .env file")
        return False
    
    return True

def check_ollama():
    """Check if Ollama is available and has models."""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print(f"✅ Ollama running with {len(models)} models")
                return True
            else:
                print("⚠️  Ollama running but no models installed")
                print("💡 Run: ollama pull llama3.2:3b")
                return False
        else:
            print("❌ Ollama service not responding")
            return False
    except Exception:
        print("❌ Cannot connect to Ollama")
        print("💡 Start Ollama with: ollama serve")
        return False

def check_weaviate():
    """Check if Weaviate is available and configured."""
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")

    try:
        response = requests.get(f"{weaviate_url}/v1/meta", timeout=5)
        if response.status_code == 200:
            meta = response.json()
            print(f"✅ Weaviate running (version: {meta.get('version', 'unknown')})")
            return True
        else:
            print("❌ Weaviate service not responding")
            return False
    except Exception:
        print("❌ Cannot connect to Weaviate")
        print("💡 Start Weaviate with: python scripts/setup_weaviate.py")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 Checking dependencies...")

    required_deps = [
        ("fastapi", "FastAPI"),
        ("langchain", "LangChain"),
        ("sqlalchemy", "SQLAlchemy"),
        ("weaviate", "Weaviate Client"),
        ("sentence_transformers", "Sentence Transformers")
    ]

    optional_deps = [
        ("clip", "CLIP (for multimodal)"),
        ("torch", "PyTorch (for CLIP)")
    ]

    missing_deps = []
    for dep, name in required_deps:
        try:
            __import__(dep)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} missing")
            missing_deps.append(dep)

    for dep, name in optional_deps:
        try:
            __import__(dep)
            print(f"✅ {name}")
        except ImportError:
            print(f"⚪ {name} (optional)")

    if missing_deps:
        print(f"💡 Install missing dependencies: pip install {' '.join(missing_deps)}")
        return False

    return True

def test_llm_functionality():
    """Test basic LLM functionality."""
    print("\n🔍 Testing LLM functionality...")
    
    try:
        from app.core.llm_config import get_llm_info, get_llm_health_status
        
        llm_info = get_llm_info()
        health_status = get_llm_health_status()
        
        print(f"Provider: {llm_info['provider']}")
        print(f"Model: {llm_info['model_name']}")
        print(f"Available: {llm_info['available']}")
        print(f"Health: {health_status['status']}")
        
        if llm_info['available'] and health_status['status'] != 'error':
            print("✅ LLM functionality working")
            return True
        else:
            print("❌ LLM functionality not working")
            if health_status.get('issues'):
                for issue in health_status['issues']:
                    print(f"   - {issue}")
            return False
            
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

def main():
    """Run validation checks."""
    print("=" * 60)
    print("🧙‍♂️ DRYAD.AI Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Dependencies", check_dependencies),
        ("LLM Functionality", test_llm_functionality)
    ]

    # Add Ollama check if configured
    if os.getenv("OLLAMA_BASE_URL"):
        checks.insert(-1, ("Ollama Service", check_ollama))

    # Add Weaviate check if configured
    if os.getenv("WEAVIATE_URL"):
        checks.insert(-1, ("Weaviate Vector Database", check_weaviate))
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<35} {status}")
    
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! DRYAD.AI is ready to use.")
        print("💡 Start the server with: uvicorn app.main:app --reload")
    elif passed >= len(results) // 2:
        print("\n⚠️  Some checks failed. DRYAD.AI may work with limited functionality.")
        print("💡 Fix the failing checks for full functionality.")
    else:
        print("\n❌ Multiple checks failed. DRYAD.AI needs setup.")
        print("💡 Run: python scripts/setup_local_llm.py")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
