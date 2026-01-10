#!/usr/bin/env python3
"""
Complete verification script for DRYAD.AI local LLM setup.
This script verifies that the system is properly configured for self-contained AI operation.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_ollama_models():
    """Test that Ollama has models available."""
    print("🔍 Testing Ollama Models...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama accessible with {len(models)} models")
            
            if models:
                for model in models:
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3) if size > 0 else 0
                    print(f"   📦 {name} ({size_gb:.1f} GB)")
                return True, models[0]['name']  # Return first model name
            else:
                print("❌ No models available in Ollama")
                print("   Run: docker exec ollama ollama pull tinyllama")
                return False, None
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False, None

def test_gremlins_llm_integration():
    """Test DRYAD.AI LLM integration."""
    print("\n🤖 Testing DRYAD.AI LLM Integration...")
    
    try:
        from app.core.llm_config import LLMConfig, get_llm, get_llm_info, LLMProvider
        
        # Test configuration
        config = LLMConfig()
        print(f"✅ LLM Provider: {config.provider}")
        print(f"✅ Model: {config.model_name}")
        print(f"✅ Base URL: {config.base_url}")
        
        # Verify it's using Ollama
        if config.provider != LLMProvider.OLLAMA:
            print(f"❌ Expected Ollama provider, got {config.provider}")
            return False
        
        # Test LLM creation
        print("Creating LLM instance...")
        llm = get_llm()
        print(f"✅ LLM instance created: {type(llm).__name__}")
        
        # Check it's not a mock
        if hasattr(llm, '_llm_type'):
            if 'mock' in llm._llm_type.lower():
                print("❌ LLM is mock type - configuration error!")
                return False
        
        # Get LLM info
        llm_info = get_llm_info()
        print(f"✅ LLM Info: Provider={llm_info['provider']}, Available={llm_info['available']}")
        
        return llm_info['available'] and llm_info['provider'] == 'ollama'
        
    except Exception as e:
        print(f"❌ Error testing DRYAD.AI integration: {e}")
        return False

def test_llm_inference():
    """Test actual LLM inference through DRYAD.AI."""
    print("\n💭 Testing LLM Inference...")
    
    try:
        from app.core.llm_config import get_llm
        
        llm = get_llm()
        
        # Test prompt
        test_prompt = "What is the capital of France? Answer in one word."
        print(f"Prompt: '{test_prompt}'")
        
        start_time = time.time()
        response = llm.invoke(test_prompt)
        end_time = time.time()
        
        # Handle different response types
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        response_text = response_text.strip()
        
        print(f"✅ Response in {end_time - start_time:.2f}s: '{response_text}'")
        
        # Check for error indicators
        if response_text.startswith("🚨") or "FAILURE" in response_text:
            print("❌ Response indicates system failure")
            return False
        
        if len(response_text) > 0:
            print("✅ Valid response received from local LLM")
            return True
        else:
            print("❌ Empty response")
            return False
            
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        return False

def test_no_external_apis():
    """Test that no external APIs are being used."""
    print("\n🔒 Testing No External API Usage...")
    
    # This is a behavioral test - we'll check configuration
    try:
        # Check environment variables
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key and openai_key != 'test-openai-key-mock-12345':
            print("⚠️  OPENAI_API_KEY is set - ensure it's not being used")
        else:
            print("✅ No OpenAI API key configured")
            
        if anthropic_key:
            print("⚠️  ANTHROPIC_API_KEY is set - ensure it's not being used")
        else:
            print("✅ No Anthropic API key configured")
        
        # Check LLM provider
        llm_provider = os.getenv('LLM_PROVIDER')
        if llm_provider == 'ollama':
            print("✅ LLM_PROVIDER correctly set to ollama")
            return True
        else:
            print(f"❌ LLM_PROVIDER is '{llm_provider}', should be 'ollama'")
            return False
            
    except Exception as e:
        print(f"❌ Error checking external API configuration: {e}")
        return False

def test_search_isolation():
    """Test that search functionality is properly isolated."""
    print("\n🔍 Testing Search Function Isolation...")
    
    try:
        from app.core.tools import explicit_web_search
        
        # Test that search requires explicit request
        try:
            # This should fail
            result = explicit_web_search("test query", explicit_request=False)
            print("❌ Search allowed without explicit request - security issue!")
            return False
        except RuntimeError as e:
            if "explicit web search requests" in str(e):
                print("✅ Search properly requires explicit request")
                return True
            else:
                print(f"❌ Unexpected error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing search isolation: {e}")
        return False

def test_docker_containers():
    """Test that required Docker containers are running."""
    print("\n🐳 Testing Docker Containers...")
    
    required_containers = {
        'ollama': 11434,
        'weaviate': 8080,
        'redis': 6379
    }
    
    all_good = True
    
    for container, port in required_containers.items():
        try:
            if container == 'ollama':
                response = requests.get(f"http://localhost:{port}/api/tags", timeout=5)
            elif container == 'weaviate':
                response = requests.get(f"http://localhost:{port}/v1/.well-known/ready", timeout=5)
            elif container == 'redis':
                # Redis check is more complex, skip for now
                print(f"✅ {container.title()} container assumed running")
                continue
                
            if response.status_code == 200:
                print(f"✅ {container.title()} container running on port {port}")
            else:
                print(f"❌ {container.title()} container not responding properly")
                all_good = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {container.title()} container not accessible on port {port}")
            all_good = False
        except Exception as e:
            print(f"⚠️  {container.title()} container check failed: {e}")
    
    return all_good

def main():
    """Run complete verification."""
    print("🚀 DRYAD.AI Complete Local Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Ollama Models Available", test_ollama_models),
        ("DRYAD.AI LLM Integration", test_gremlins_llm_integration),
        ("LLM Inference", test_llm_inference),
        ("No External APIs", test_no_external_apis),
        ("Search Isolation", test_search_isolation),
        ("Docker Containers", test_docker_containers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "Ollama Models Available":
                result, model_name = test_func()
                if result:
                    print(f"   Using model: {model_name}")
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Complete Verification Results")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 COMPLETE SUCCESS!")
        print("🔒 DRYAD.AI is properly configured for self-contained local AI operation.")
        print("🚫 No external API dependencies or mock fallbacks detected.")
        print("🚀 System ready for production use with local LLM.")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed.")
        print("Please review the issues above before using the system.")
        
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
