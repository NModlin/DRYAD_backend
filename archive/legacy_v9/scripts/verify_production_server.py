"""
Verify Production Server Endpoints
Quick script to test all production API endpoints
"""

import requests
import json
import sys


def test_endpoint(url, name):
    """Test a single endpoint."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)[:150]}...")
            return True
        else:
            print(f"❌ {name}: FAIL (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False


def main():
    """Test all endpoints."""
    print("\n" + "="*70)
    print("PRODUCTION API SERVER VERIFICATION")
    print("="*70 + "\n")
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        (f"{base_url}/", "Root Endpoint"),
        (f"{base_url}/health", "Health Check"),
        (f"{base_url}/metrics", "Metrics (JSON)"),
        (f"{base_url}/api/v1/system/status", "System Status"),
    ]
    
    results = []
    for url, name in endpoints:
        print(f"\nTesting: {name}")
        print("-" * 70)
        results.append(test_endpoint(url, name))
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"\nEndpoints Tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All endpoints are operational!")
        return 0
    else:
        print(f"\n❌ {total - passed} endpoint(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

