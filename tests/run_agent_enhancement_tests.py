"""
Test Runner for Agent Enhancement Tests

Runs all tests for the agent enhancement features and generates a report.
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all agent enhancement tests."""
    print("=" * 80)
    print("AGENT ENHANCEMENT TEST SUITE")
    print("=" * 80)
    print()
    
    # Test files to run
    test_files = [
        "tests/test_tool_registry.py",
        "tests/test_hitl_approvals.py",
        "tests/test_collaboration.py",
        "tests/test_guardrails.py",
        "tests/test_agent_architect.py",
        "tests/test_agent_enhancements_integration.py"
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for test_file in test_files:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print(f"{'=' * 80}\n")
        
        # Run pytest for this file
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        # Parse output
        output = result.stdout + result.stderr
        print(output)
        
        # Extract test counts
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")
        
        results[test_file] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "return_code": result.returncode
        }
        
        total_passed += passed
        total_failed += failed
        total_skipped += skipped
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    for test_file, result in results.items():
        status = "✅ PASS" if result["return_code"] == 0 else "❌ FAIL"
        print(f"{status} {Path(test_file).name}")
        print(f"     Passed: {result['passed']}, Failed: {result['failed']}, Skipped: {result['skipped']}")
    
    print()
    print("=" * 80)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print("=" * 80)
    
    # Return exit code
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())

