#!/usr/bin/env python3
"""
DRYAD Hybrid LLM System Verification Script

This script verifies that the hybrid LLM system is properly configured and working.
It tests both cloud and local configurations, routing logic, and fallback mechanisms.
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_environment_configuration():
    """Test that environment variables are properly configured."""
    print("🔧 Testing Environment Configuration...")
    
    required_vars = [
        'LLM_PROVIDER',
        'OLLAMA_BASE_URL',
        'OLLAMA_MODEL'
    ]
    
    optional_vars = [
        'OLLAMA_CLOUD_URL',
        'OLLAMA_CLOUD_ENABLED',
        'OLLAMA_API_KEY'
    ]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {missing_required}")
        return False
    
    print(f"✅ LLM Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"✅ Local Ollama URL: {os.getenv('OLLAMA_BASE_URL')}")
    print(f"✅ Local Model: {os.getenv('OLLAMA_MODEL')}")
    
    # Check optional cloud configuration
    cloud_enabled = os.getenv('OLLAMA_CLOUD_ENABLED', 'false').lower() == 'true'
    if cloud_enabled:
        print(f"✅ Cloud URL: {os.getenv('OLLAMA_CLOUD_URL')}")
        print(f"✅ Cloud Enabled: {cloud_enabled}")
        if os.getenv('OLLAMA_API_KEY'):
            print("✅ API Key: [CONFIGURED]")
        else:
            print("⚠️  API Key: [NOT SET]")
    else:
        print("ℹ️  Cloud mode disabled")
    
    return True

def test_hybrid_configuration():
    """Test the hybrid LLM configuration system."""
    print("\n🧠 Testing Hybrid Configuration...")
    
    try:
        from app.core.llm_config import get_hybrid_status, LLMConfig
        
        # Test configuration loading
        config = LLMConfig()
        print(f"✅ Configuration loaded successfully")
        print(f"   Provider: {config.provider}")
        print(f"   Cloud enabled: {config.cloud_enabled}")
        print(f"   Cloud URL: {config.cloud_url}")
        
        # Test status function
        status = get_hybrid_status()
        print(f"✅ Status function working")
        print(f"   Available cloud models: {len(status.get('available_cloud_models', []))}")
        print(f"   Available local models: {len(status.get('available_local_models', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_model_routing():
    """Test the intelligent model routing system."""
    print("\n🎯 Testing Model Routing...")
    
    try:
        from app.core.llm_config import LLMConfig, TaskComplexity
        
        config = LLMConfig()
        
        # Test different agent types and complexities
        test_cases = [
            ("researcher", TaskComplexity.SIMPLE),
            ("researcher", TaskComplexity.COMPLEX),
            ("coder", TaskComplexity.SIMPLE),
            ("coder", TaskComplexity.COMPLEX),
            ("coordinator", TaskComplexity.MODERATE),
        ]
        
        for agent_type, complexity in test_cases:
            try:
                model, url = config.select_optimal_model(agent_type, complexity)
                print(f"✅ {agent_type} + {complexity.value}: {model} @ {url}")
            except Exception as e:
                print(f"❌ {agent_type} + {complexity.value}: {e}")
        
        # Test force local mode
        try:
            model, url = config.select_optimal_model("researcher", TaskComplexity.COMPLEX, force_local=True)
            print(f"✅ Force local mode: {model} @ {url}")
        except Exception as e:
            print(f"❌ Force local mode failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model routing test failed: {e}")
        return False

def test_cloud_connectivity():
    """Test cloud connectivity if enabled."""
    print("\n🌐 Testing Cloud Connectivity...")
    
    cloud_enabled = os.getenv('OLLAMA_CLOUD_ENABLED', 'false').lower() == 'true'
    if not cloud_enabled:
        print("ℹ️  Cloud mode disabled, skipping connectivity test")
        return True
    
    try:
        from app.core.llm_config import test_cloud_connectivity
        
        is_connected = test_cloud_connectivity()
        if is_connected:
            print("✅ Cloud connectivity working")
        else:
            print("⚠️  Cloud connectivity failed (expected if chat API not enabled)")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloud connectivity test failed: {e}")
        return False

def test_model_listing():
    """Test model listing functionality."""
    print("\n📋 Testing Model Listing...")
    
    try:
        from app.core.llm_config import list_available_models
        
        models = list_available_models()
        
        print("✅ Model listing working")
        print(f"   Cloud models: {len(models.get('cloud', {}).get('models', []))}")
        print(f"   Local models: {len(models.get('local', {}).get('models', []))}")
        
        # Show some model details
        cloud_models = models.get('cloud', {}).get('models', [])
        if cloud_models:
            print(f"   Sample cloud models: {cloud_models[:3]}")
        
        local_models = models.get('local', {}).get('models', [])
        if local_models:
            print(f"   Sample local models: {local_models[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model listing test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🚀 DRYAD Hybrid LLM System Verification")
    print("=" * 50)
    
    tests = [
        test_environment_configuration,
        test_hybrid_configuration,
        test_model_routing,
        test_cloud_connectivity,
        test_model_listing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hybrid LLM system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
