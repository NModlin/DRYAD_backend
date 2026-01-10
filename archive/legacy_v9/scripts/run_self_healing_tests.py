"""
Comprehensive test runner for Self-Healing System
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_tests(test_file=None, verbose=True):
    """
    Run self-healing tests.
    
    Args:
        test_file: Specific test file to run (None for all)
        verbose: Show verbose output
    """
    if test_file:
        test_files = [test_file]
    else:
        # All self-healing test files
        test_files = [
            "tests/test_guardian.py",
            "tests/test_teams_notifier.py",
            "tests/test_self_healing_worker.py",
            "tests/test_self_healing_api.py",
            "tests/test_self_healing_integration.py"
        ]
    
    print("🧪 Running Self-Healing System Tests")
    print("=" * 60)
    
    all_passed = True
    results = {}
    
    for test_file in test_files:
        test_path = Path(test_file)
        
        if not test_path.exists():
            print(f"\n⚠️  Test file not found: {test_file}")
            continue
        
        print(f"\n📝 Running: {test_file}")
        print("-" * 60)
        
        # Build pytest command
        cmd = ["pytest", str(test_path), "-v" if verbose else "-q"]
        
        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Store result
        results[test_file] = {
            "passed": result.returncode == 0,
            "output": result.stdout
        }
        
        # Print output
        print(result.stdout)
        
        if result.returncode != 0:
            all_passed = False
            print(f"❌ Tests failed in {test_file}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        else:
            print(f"✅ All tests passed in {test_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed_count = sum(1 for r in results.values() if r["passed"])
    total_count = len(results)
    
    for test_file, result in results.items():
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status} - {test_file}")
    
    print(f"\nTotal: {passed_count}/{total_count} test files passed")
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1


def run_coverage():
    """Run tests with coverage report."""
    print("🧪 Running Tests with Coverage")
    print("=" * 60)
    
    cmd = [
        "pytest",
        "tests/test_guardian.py",
        "tests/test_teams_notifier.py",
        "tests/test_self_healing_worker.py",
        "tests/test_self_healing_api.py",
        "tests/test_self_healing_integration.py",
        "--cov=app.core.guardian",
        "--cov=app.integrations.teams_notifier",
        "--cov=app.workers.self_healing_worker",
        "--cov=app.api.v1.endpoints.self_healing",
        "--cov-report=html",
        "--cov-report=term"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Coverage report generated in htmlcov/index.html")
    
    return result.returncode


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            # Run all tests
            return run_tests()
        
        elif command == "guardian":
            # Run Guardian tests only
            return run_tests("tests/test_guardian.py")
        
        elif command == "teams":
            # Run Teams notifier tests only
            return run_tests("tests/test_teams_notifier.py")
        
        elif command == "worker":
            # Run Worker tests only
            return run_tests("tests/test_self_healing_worker.py")
        
        elif command == "api":
            # Run API tests only
            return run_tests("tests/test_self_healing_api.py")
        
        elif command == "integration":
            # Run integration tests only
            return run_tests("tests/test_self_healing_integration.py")
        
        elif command == "coverage":
            # Run with coverage
            return run_coverage()
        
        elif command == "quick":
            # Quick test (no verbose)
            return run_tests(verbose=False)
        
        else:
            print(f"Unknown command: {command}")
            print_usage()
            return 1
    else:
        # Default: run all tests
        return run_tests()


def print_usage():
    """Print usage information."""
    print("\nUsage: python scripts/run_self_healing_tests.py [command]")
    print("\nCommands:")
    print("  all          - Run all self-healing tests (default)")
    print("  guardian     - Run Guardian tests only")
    print("  teams        - Run Teams notifier tests only")
    print("  worker       - Run Worker tests only")
    print("  api          - Run API tests only")
    print("  integration  - Run integration tests only")
    print("  coverage     - Run tests with coverage report")
    print("  quick        - Run all tests (no verbose output)")
    print("\nExamples:")
    print("  python scripts/run_self_healing_tests.py")
    print("  python scripts/run_self_healing_tests.py guardian")
    print("  python scripts/run_self_healing_tests.py coverage")


if __name__ == "__main__":
    sys.exit(main())

