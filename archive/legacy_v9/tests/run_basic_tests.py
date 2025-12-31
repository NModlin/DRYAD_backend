#!/usr/bin/env python3
"""
Basic test runner for DRYAD.AI Backend.
Runs essential tests to verify core functionality.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_environment():
    """Check if the environment is set up correctly."""
    logger.info("🔍 Checking environment...")
    
    # Check Python version
    returncode, stdout, stderr = run_command("python --version")
    if returncode == 0:
        logger.info(f"✅ Python: {stdout.strip()}")
    else:
        logger.error(f"❌ Python check failed: {stderr}")
        return False
    
    # Check if pytest is available
    returncode, stdout, stderr = run_command("python -c \"import pytest; print(f'pytest {pytest.__version__}')\"")
    if returncode == 0:
        logger.info(f"✅ {stdout.strip()}")
    else:
        logger.error(f"❌ pytest not available: {stderr}")
        return False
    
    # Check if FastAPI can be imported
    returncode, stdout, stderr = run_command("python -c \"from app.main import app; print('FastAPI app imported successfully')\"")
    if returncode == 0:
        logger.info(f"✅ {stdout.strip()}")
    else:
        logger.error(f"❌ FastAPI import failed: {stderr}")
        return False
    
    return True

def run_basic_tests():
    """Run basic functionality tests."""
    logger.info("🧪 Running basic functionality tests...")
    
    test_commands = [
        ("Health Check Test", "python -c \"from fastapi.testclient import TestClient; from app.main import app; client = TestClient(app); response = client.get('/api/v1/health/status'); print(f'Health check: {response.status_code}'); assert response.status_code == 200\""),
        ("API Docs Test", "python -c \"from fastapi.testclient import TestClient; from app.main import app; client = TestClient(app); response = client.get('/docs'); print(f'API docs: {response.status_code}'); assert response.status_code == 200\""),
        ("OpenAPI Schema Test", "python -c \"from fastapi.testclient import TestClient; from app.main import app; client = TestClient(app); response = client.get('/openapi.json'); print(f'OpenAPI schema: {response.status_code}'); assert response.status_code == 200\""),
    ]
    
    passed = 0
    total = len(test_commands)
    
    for test_name, cmd in test_commands:
        logger.info(f"Running {test_name}...")
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            logger.info(f"✅ {test_name}: {stdout.strip()}")
            passed += 1
        else:
            logger.error(f"❌ {test_name} failed: {stderr}")
    
    return passed, total

def run_pytest_tests():
    """Try to run pytest tests."""
    logger.info("🧪 Attempting to run pytest tests...")
    
    # Try to run the basic functionality test
    returncode, stdout, stderr = run_command("python -m pytest tests/functional/test_basic_functionality.py::TestBasicFunctionality::test_api_health_check -v")
    
    if returncode == 0:
        logger.info("✅ pytest test passed")
        logger.info(stdout)
        return True
    else:
        logger.error("❌ pytest test failed")
        logger.error(stderr)
        return False

def main():
    """Main test runner."""
    logger.info("🚀 Starting DRYAD.AI Backend Test Suite")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    # Run basic tests
    passed, total = run_basic_tests()
    
    # Try pytest
    pytest_success = run_pytest_tests()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Basic tests: {passed}/{total} passed")
    logger.info(f"Pytest tests: {'✅ PASS' if pytest_success else '❌ FAIL'}")
    
    overall_success = (passed == total) and pytest_success
    
    if overall_success:
        logger.info("🎉 All tests passed!")
    else:
        logger.error("⚠️ Some tests failed")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
