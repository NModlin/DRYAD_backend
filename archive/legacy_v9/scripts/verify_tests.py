#!/usr/bin/env python3
"""
Test verification script for DRYAD.AI Backend.
Creates a test report file instead of relying on terminal output.
"""

import sys
import os
import traceback
import json
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def write_report(content):
    """Write content to test report file."""
    with open("test_report.txt", "a", encoding="utf-8") as f:
        f.write(content + "\n")

def run_test(test_name, test_func):
    """Run a test and record the result."""
    write_report(f"\n🔍 Running {test_name}...")
    try:
        result = test_func()
        if result:
            write_report(f"✅ {test_name}: PASS")
            return True
        else:
            write_report(f"❌ {test_name}: FAIL")
            return False
    except Exception as e:
        write_report(f"❌ {test_name}: ERROR - {str(e)}")
        write_report(f"   Traceback: {traceback.format_exc()}")
        return False

def test_imports():
    """Test core imports."""
    try:
        from app.main import app
        from app.core.agent import agent_graph_app
        from app.core.llm_config import get_llm_info
        return True
    except Exception:
        return False

def test_fastapi_app():
    """Test FastAPI app creation."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/health/status")
        return response.status_code == 200
    except Exception:
        return False

def test_api_docs():
    """Test API documentation."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/docs")
        return response.status_code == 200
    except Exception:
        return False

def test_openapi_schema():
    """Test OpenAPI schema."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/openapi.json")
        data = response.json()
        return response.status_code == 200 and "openapi" in data
    except Exception:
        return False

def test_llm_config():
    """Test LLM configuration."""
    try:
        from app.core.llm_config import get_llm_info, get_llm_health_status
        
        llm_info = get_llm_info()
        health_status = get_llm_health_status()
        
        write_report(f"   LLM Provider: {llm_info.get('provider', 'Unknown')}")
        write_report(f"   LLM Model: {llm_info.get('model_name', 'Unknown')}")
        write_report(f"   LLM Available: {llm_info.get('available', False)}")
        write_report(f"   Health Status: {health_status.get('status', 'Unknown')}")
        
        return True
    except Exception:
        return False

def test_agent_system():
    """Test agent system."""
    try:
        from app.core.agent import agent_graph_app
        from langchain_core.messages import HumanMessage
        
        inputs = {"messages": [HumanMessage(content="Hello, test query")]}
        result = agent_graph_app.invoke(inputs)
        
        write_report(f"   Agent response keys: {list(result.keys()) if result else 'None'}")
        return result is not None
    except Exception:
        return False

def count_api_endpoints():
    """Count actual API endpoints."""
    try:
        from app.main import app
        
        endpoint_count = 0
        for route in app.routes:
            if hasattr(route, 'methods'):
                endpoint_count += len(route.methods) - 1  # Exclude HEAD/OPTIONS
        
        write_report(f"   Total API endpoints found: {endpoint_count}")
        return True
    except Exception:
        return False

def main():
    """Main test runner."""
    # Clear previous report
    if os.path.exists("test_report.txt"):
        os.remove("test_report.txt")
    
    write_report("🚀 DRYAD.AI Backend Test Verification")
    write_report("=" * 50)
    write_report(f"Timestamp: {datetime.now().isoformat()}")
    write_report(f"Python Version: {sys.version}")
    write_report(f"Working Directory: {os.getcwd()}")
    
    tests = [
        ("Core Imports", test_imports),
        ("FastAPI App", test_fastapi_app),
        ("API Documentation", test_api_docs),
        ("OpenAPI Schema", test_openapi_schema),
        ("LLM Configuration", test_llm_config),
        ("Agent System", test_agent_system),
        ("API Endpoint Count", count_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = run_test(test_name, test_func)
        results.append((test_name, result))
    
    # Summary
    write_report("\n" + "=" * 50)
    write_report("📊 TEST SUMMARY")
    write_report("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        write_report(f"{status} - {test_name}")
    
    write_report(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        write_report("🎉 All tests passed! Basic functionality is working.")
        success = True
    else:
        write_report(f"⚠️  {total - passed} tests failed. Check details above.")
        success = False
    
    write_report(f"\nTest completed at: {datetime.now().isoformat()}")
    
    # Also create a JSON report
    json_report = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "tests": [{"name": name, "passed": result} for name, result in results],
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success": success
        }
    }
    
    with open("test_report.json", "w") as f:
        json.dump(json_report, f, indent=2)
    
    print(f"Test verification complete. Results written to test_report.txt and test_report.json")
    print(f"Summary: {passed}/{total} tests passed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
