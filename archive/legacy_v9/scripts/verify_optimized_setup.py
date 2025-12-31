#!/usr/bin/env python3
"""
Quick verification script for the optimized llama-cpp-python setup.
This script verifies that all optimizations are properly implemented.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '.')

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking Dependencies...")
    
    dependencies = {
        'llama_cpp': 'llama-cpp-python',
        'langchain_community': 'langchain-community',
        'psutil': 'psutil'
    }
    
    available = {}
    for module, package in dependencies.items():
        try:
            __import__(module)
            available[package] = True
            print(f"   ✅ {package}: Available")
        except ImportError:
            available[package] = False
            print(f"   ❌ {package}: Missing")
    
    return available

def check_configuration():
    """Check if configuration is properly optimized."""
    print("\n🔧 Checking Configuration...")
    
    try:
        from app.core.config import config
        
        # Check default provider
        if config.LLM_PROVIDER == "llamacpp":
            print("   ✅ Default LLM provider: llamacpp (optimized)")
        else:
            print(f"   ❌ Default LLM provider: {config.LLM_PROVIDER} (should be llamacpp)")
            return False
        
        # Check model configuration
        expected_model = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        if config.LLAMACPP_MODEL == expected_model:
            print(f"   ✅ Default model: {expected_model}")
        else:
            print(f"   ⚠️  Default model: {config.LLAMACPP_MODEL} (expected {expected_model})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration check failed: {e}")
        return False

def check_model_registry():
    """Check if model registry has optimized models."""
    print("\n📚 Checking Model Registry...")
    
    try:
        from app.core.model_manager import model_manager
        
        models = model_manager.registry.models
        expected_models = [
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "llama-2-7b-chat.Q4_K_M.gguf",
            "llama-2-13b-chat.Q4_K_M.gguf"
        ]
        
        for model_name in expected_models:
            if model_name in models:
                model_info = models[model_name]
                size_mb = model_info.size_bytes / (1024**2)
                quality = model_info.performance_metrics.get('quality_score', 0)
                print(f"   ✅ {model_name}: {size_mb:.0f}MB, quality={quality}")
            else:
                print(f"   ❌ Missing model: {model_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model registry check failed: {e}")
        return False

def check_performance_features():
    """Check if performance optimization features are available."""
    print("\n⚡ Checking Performance Features...")
    
    try:
        # Check CPU optimizer
        from app.core.performance_optimizer import performance_optimizer
        
        if hasattr(performance_optimizer, 'cpu_optimizer'):
            print("   ✅ CPU optimizer: Available")
        else:
            print("   ❌ CPU optimizer: Missing")
            return False
        
        # Check response cache
        if hasattr(performance_optimizer, 'response_cache'):
            print("   ✅ Response cache: Available")
        else:
            print("   ❌ Response cache: Missing")
            return False
        
        # Check request queue
        if hasattr(performance_optimizer, 'request_queue'):
            print("   ✅ Request queue: Available")
        else:
            print("   ❌ Request queue: Missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance features check failed: {e}")
        return False

def check_connection_pooling():
    """Check if enhanced connection pooling is working."""
    print("\n🏊 Checking Connection Pooling...")
    
    try:
        from app.core.llm_config import LLMPool
        
        # Test pool creation
        pool = LLMPool(pool_size=2, agent_type="test")
        
        # Check enhanced features
        if hasattr(pool, 'instance_health'):
            print("   ✅ Health tracking: Available")
        else:
            print("   ❌ Health tracking: Missing")
            return False
        
        if hasattr(pool, '_health_check'):
            print("   ✅ Health check method: Available")
        else:
            print("   ❌ Health check method: Missing")
            return False
        
        if hasattr(pool, 'failed_requests'):
            print("   ✅ Failure tracking: Available")
        else:
            print("   ❌ Failure tracking: Missing")
            return False
        
        print(f"   ✅ Optimized pool size: {pool.pool_size}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Connection pooling check failed: {e}")
        return False

def check_model_files():
    """Check if model files exist."""
    print("\n📁 Checking Model Files...")
    
    models_dir = Path("./models")
    if not models_dir.exists():
        print("   ⚠️  Models directory doesn't exist (will be created on first use)")
        return True
    
    expected_files = [
        "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    ]
    
    found_files = 0
    for file_name in expected_files:
        file_path = models_dir / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024**2)
            print(f"   ✅ {file_name}: {size_mb:.0f}MB")
            found_files += 1
        else:
            print(f"   ⚠️  {file_name}: Not downloaded (will download on first use)")
    
    if found_files > 0:
        print(f"   ✅ {found_files} model file(s) ready")
    else:
        print("   ⚠️  No model files found (will download on first use)")
    
    return True

def main():
    """Run all verification checks."""
    print("🚀 OPTIMIZED LLAMA-CPP-PYTHON SETUP VERIFICATION")
    print("=" * 60)
    
    checks = [
        check_dependencies,
        check_configuration,
        check_model_registry,
        check_performance_features,
        check_connection_pooling,
        check_model_files
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Check {check.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (check, result) in enumerate(zip(checks, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {check.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if passed == total:
        print("🎉 All optimizations are properly implemented!")
        print("💡 To complete setup:")
        print("   1. Install missing dependencies: pip install llama-cpp-python langchain-community")
        print("   2. Run the application - models will download automatically")
        print("   3. Test with: python test_optimized_llamacpp.py")
    elif passed >= total * 0.8:
        print("✅ Most optimizations are working!")
        print("💡 Minor issues detected - check failed items above")
    else:
        print("⚠️  Several optimization issues detected")
        print("💡 Review the failed checks and fix configuration issues")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
