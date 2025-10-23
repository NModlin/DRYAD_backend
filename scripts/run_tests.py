#!/usr/bin/env python3
# Make the script executable
import stat
"""
DRYAD.AI Backend Test Runner

Comprehensive test runner for the DRYAD.AI Backend test suite.
Supports running different test categories and provides detailed reporting
with comprehensive logging to timestamped log files.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --e2e              # Run only end-to-end tests
    python run_tests.py --performance      # Run only performance tests
    python run_tests.py --fast             # Run fast tests only (exclude slow/performance)

    # New Endpoint Test Categories:
    python run_tests.py --endpoints        # Run all new endpoint tests
    python run_tests.py --multi-agent      # Run multi-agent orchestrator tests
    python run_tests.py --documents        # Run document management tests
    python run_tests.py --orchestrator     # Run task orchestrator tests
    python run_tests.py --realtime         # Run real-time API tests
    python run_tests.py --multimodal       # Run multi-modal processing tests
    python run_tests.py --graphql          # Run GraphQL API tests
    python run_tests.py --security         # Run security and input sanitization tests
    python run_tests.py --websocket        # Run WebSocket communication tests

    # Options:
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --logs             # Show recent log files
    python run_tests.py --no-logging       # Disable logging to file
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Add tests directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "tests"))

try:
    from tests.utils.logging_utils import TestLogger, get_test_category_from_args
except ImportError:
    # Fallback if logging utils not available
    print("Warning: Logging utilities not available. Running without comprehensive logging.")
    TestLogger = None
    get_test_category_from_args = lambda args: "general"


def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["PYTHONPATH"] = str(Path.cwd())
    
    # Load test environment variables
    env_test_file = Path(".env.test")
    if env_test_file.exists():
        print("Loading test environment variables from .env.test")
        with open(env_test_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    
    # Ensure test data directory exists
    Path("data").mkdir(exist_ok=True)
    
    print("Test environment setup complete")


def show_log_summary(logger: 'TestLogger') -> None:
    """Show summary of recent log files."""
    print("\n" + "="*60)
    print("DRYAD.AI TEST LOGS SUMMARY")
    print("="*60)

    summary = logger.get_log_summary()

    print(f"Logs Directory: {summary['logs_directory']}")
    print(f"Total Log Files: {summary['total_logs']}")

    if summary['recent_logs']:
        print(f"\nRecent Log Files (last {len(summary['recent_logs'])}):")
        print("-" * 60)
        for log in summary['recent_logs']:
            print(f"📄 {log['filename']}")
            print(f"   Path: {log['path']}")
            print(f"   Size: {log['size_kb']} KB")
            print(f"   Modified: {log['modified']}")
            print()
    else:
        print("\nNo log files found.")

    print("="*60)


def run_pytest_command(args: List[str], logger: 'TestLogger' = None,
                      test_category: str = "general") -> Dict[str, Any]:
    """Run pytest with given arguments and return results with optional logging."""
    cmd = ["python", "-m", "pytest"] + args

    if logger:
        # Use comprehensive logging
        print(f"🔍 Test Category: {test_category}")
        result = logger.run_command_with_logging(cmd, test_category)
        return result
    else:
        # Fallback to original method
        print(f"Running command: {' '.join(cmd)}")
        print("-" * 80)

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=False,  # Show output in real-time
                text=True,
                cwd=Path.cwd()
            )

            end_time = time.time()
            duration = end_time - start_time

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration": duration,
                "command": " ".join(cmd)
            }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            print(f"Error running tests: {e}")
            return {
                "success": False,
                "return_code": -1,
                "duration": duration,
                "error": str(e),
                "command": " ".join(cmd)
            }


def run_unit_tests(verbose: bool = False, coverage: bool = False,
                  logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run unit tests."""
    print("\n🧪 Running Unit Tests")
    print("=" * 50)

    args = ["tests/unit/", "-m", "unit"]

    if verbose:
        args.append("-v")

    if coverage:
        args.extend(["--cov=app", "--cov-report=term-missing"])

    return run_pytest_command(args, logger, "unit")


def run_integration_tests(verbose: bool = False, logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run integration tests."""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)

    args = ["tests/integration/", "-m", "integration"]

    if verbose:
        args.append("-v")

    return run_pytest_command(args, logger, "integration")


def run_e2e_tests(verbose: bool = False, logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run end-to-end tests."""
    print("\n🎯 Running End-to-End Tests")
    print("=" * 50)

    args = ["tests/e2e/", "-m", "e2e"]

    if verbose:
        args.append("-v")

    return run_pytest_command(args, logger, "e2e")


def run_performance_tests(verbose: bool = False, logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run performance tests."""
    print("\n⚡ Running Performance Tests")
    print("=" * 50)

    args = ["tests/performance/", "-m", "performance"]

    if verbose:
        args.append("-v")

    return run_pytest_command(args, logger, "performance")


def run_fast_tests(verbose: bool = False, coverage: bool = False,
                  logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run fast tests (exclude slow and performance tests)."""
    print("\n🚀 Running Fast Tests")
    print("=" * 50)

    args = ["tests/", "-m", "not slow and not performance"]

    if verbose:
        args.append("-v")

    if coverage:
        args.extend(["--cov=app", "--cov-report=term-missing"])

    return run_pytest_command(args, logger, "fast")


def run_all_tests(verbose: bool = False, coverage: bool = False,
                  logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run all traditional tests (excluding new endpoint tests to avoid duplication)."""
    print("\n🎪 Running Traditional Test Suite")
    print("=" * 50)

    # Exclude the new endpoint test files to avoid duplication when running complete suite
    args = ["tests/",
            "--ignore=tests/integration/test_multi_agent_endpoints.py",
            "--ignore=tests/integration/test_document_endpoints.py",
            "--ignore=tests/integration/test_orchestrator_endpoints.py",
            "--ignore=tests/integration/test_realtime_endpoints.py",
            "--ignore=tests/integration/test_multimodal_endpoints.py",
            "--ignore=tests/integration/test_graphql_endpoints.py",
            "--ignore=tests/integration/test_security_endpoints.py",
            "--ignore=tests/integration/test_websocket_endpoints.py"]

    if verbose:
        args.append("-v")

    if coverage:
        args.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])

    return run_pytest_command(args, logger, "traditional")


# New Endpoint Test Functions
def run_endpoint_test_category(category: str, verbose: bool = False, coverage: bool = False,
                              logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run a specific endpoint test category."""

    # Define test categories and their corresponding files
    test_categories = {
        "multi-agent": {
            "files": ["tests/integration/test_multi_agent_endpoints.py"],
            "markers": ["integration", "orchestrator"],
            "description": "Multi-Agent Orchestrator Tests"
        },
        "documents": {
            "files": ["tests/integration/test_document_endpoints.py"],
            "markers": ["integration", "document"],
            "description": "Document Management Tests"
        },
        "orchestrator": {
            "files": ["tests/integration/test_orchestrator_endpoints.py"],
            "markers": ["integration", "orchestrator"],
            "description": "Task Orchestrator Tests"
        },
        "realtime": {
            "files": ["tests/integration/test_realtime_endpoints.py"],
            "markers": ["integration", "realtime"],
            "description": "Real-time API Tests"
        },
        "multimodal": {
            "files": ["tests/integration/test_multimodal_endpoints.py"],
            "markers": ["integration", "multimodal"],
            "description": "Multi-modal Processing Tests"
        },
        "graphql": {
            "files": ["tests/integration/test_graphql_endpoints.py"],
            "markers": ["integration", "graphql"],
            "description": "GraphQL API Tests"
        },
        "security": {
            "files": ["tests/integration/test_security_endpoints.py"],
            "markers": ["integration", "security"],
            "description": "Security and Input Sanitization Tests"
        },
        "websocket": {
            "files": ["tests/integration/test_websocket_endpoints.py"],
            "markers": ["integration", "websocket"],
            "description": "WebSocket Communication Tests"
        }
    }

    if category not in test_categories:
        print(f"❌ Unknown test category: {category}")
        return {
            "command": f"endpoint-{category}",
            "success": False,
            "return_code": 1,
            "duration": 0.0,
            "error": f"Unknown test category: {category}"
        }

    test_info = test_categories[category]

    print(f"\n🧪 Running {test_info['description']}")
    print("=" * 50)

    # Check if test files exist
    missing_files = []
    for test_file in test_info["files"]:
        if not Path(test_file).exists():
            missing_files.append(test_file)

    if missing_files:
        print(f"⚠️  Missing test files: {', '.join(missing_files)}")
        return {
            "command": f"endpoint-{category}",
            "success": False,
            "return_code": 1,
            "duration": 0.0,
            "error": f"Missing test files: {', '.join(missing_files)}"
        }

    # Build pytest arguments
    args = test_info["files"].copy()

    # Add markers using OR logic
    if test_info["markers"]:
        marker_expr = " or ".join(test_info["markers"])
        args.extend(["-m", marker_expr])

    if verbose:
        args.extend(["-v", "-s"])

    if coverage:
        args.extend(["--cov=app", "--cov-report=term-missing", "--cov-fail-under=0"])

    return run_pytest_command(args, logger, f"endpoint-{category}")


def run_multi_agent_tests(verbose: bool = False, coverage: bool = False,
                         logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run multi-agent orchestrator tests."""
    return run_endpoint_test_category("multi-agent", verbose, coverage, logger)


def run_documents_tests(verbose: bool = False, coverage: bool = False,
                       logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run document management tests."""
    return run_endpoint_test_category("documents", verbose, coverage, logger)


def run_orchestrator_tests(verbose: bool = False, coverage: bool = False,
                          logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run task orchestrator tests."""
    return run_endpoint_test_category("orchestrator", verbose, coverage, logger)


def run_realtime_tests(verbose: bool = False, coverage: bool = False,
                      logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run real-time API tests."""
    return run_endpoint_test_category("realtime", verbose, coverage, logger)


def run_multimodal_tests(verbose: bool = False, coverage: bool = False,
                        logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run multi-modal processing tests."""
    return run_endpoint_test_category("multimodal", verbose, coverage, logger)


def run_graphql_tests(verbose: bool = False, coverage: bool = False,
                     logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run GraphQL API tests."""
    return run_endpoint_test_category("graphql", verbose, coverage, logger)


def run_security_tests(verbose: bool = False, coverage: bool = False,
                      logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run security and input sanitization tests."""
    return run_endpoint_test_category("security", verbose, coverage, logger)


def run_websocket_tests(verbose: bool = False, coverage: bool = False,
                       logger: 'TestLogger' = None) -> Dict[str, Any]:
    """Run WebSocket communication tests."""
    return run_endpoint_test_category("websocket", verbose, coverage, logger)


def run_all_endpoint_tests(verbose: bool = False, coverage: bool = False,
                          logger: 'TestLogger' = None) -> List[Dict[str, Any]]:
    """Run all new endpoint tests."""
    print("\n🧪 Running All New Endpoint Tests")
    print("=" * 50)

    endpoint_categories = ["multi-agent", "documents", "orchestrator", "realtime",
                          "multimodal", "graphql", "security", "websocket"]

    results = []
    for category in endpoint_categories:
        results.append(run_endpoint_test_category(category, verbose, coverage, logger))

    return results


def print_test_summary(results: List[Dict[str, Any]]):
    """Print a summary of test results."""
    print("\n" + "=" * 80)
    print("🏁 TEST SUMMARY")
    print("=" * 80)

    total_duration = sum(r["duration"] for r in results)
    successful_runs = [r for r in results if r["success"]]
    failed_runs = [r for r in results if not r["success"]]

    print(f"Total test runs: {len(results)}")
    print(f"Successful runs: {len(successful_runs)}")
    print(f"Failed runs: {len(failed_runs)}")
    print(f"Total duration: {total_duration:.2f} seconds")

    # Show log files if available
    log_files = [r.get("log_file") for r in results if r.get("log_file")]
    if log_files:
        print(f"\n📄 Log files created:")
        for log_file in log_files:
            print(f"  - {log_file}")

    if successful_runs:
        print("\n✅ Successful test runs:")
        for result in successful_runs:
            duration_str = f"({result['duration']:.2f}s)"
            log_str = f" -> {result['log_file']}" if result.get('log_file') else ""
            print(f"  - {result['command']} {duration_str}{log_str}")

    if failed_runs:
        print("\n❌ Failed test runs:")
        for result in failed_runs:
            duration_str = f"(exit code: {result['return_code']}, {result['duration']:.2f}s)"
            log_str = f" -> {result['log_file']}" if result.get('log_file') else ""
            print(f"  - {result['command']} {duration_str}{log_str}")
            if "error" in result:
                print(f"    Error: {result['error']}")

    # Overall status
    if failed_runs:
        print(f"\n❌ TESTS FAILED - {len(failed_runs)} test run(s) failed")
        return False
    else:
        print(f"\n✅ ALL TESTS PASSED - {len(successful_runs)} test run(s) successful")
        return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="DRYAD.AI Backend Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test category options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow/performance)")

    # New endpoint test category options
    parser.add_argument("--endpoints", action="store_true", help="Run all new endpoint tests")
    parser.add_argument("--multi-agent", action="store_true", help="Run multi-agent orchestrator tests")
    parser.add_argument("--documents", action="store_true", help="Run document management tests")
    parser.add_argument("--orchestrator", action="store_true", help="Run task orchestrator tests")
    parser.add_argument("--realtime", action="store_true", help="Run real-time API tests")
    parser.add_argument("--multimodal", action="store_true", help="Run multi-modal processing tests")
    parser.add_argument("--graphql", action="store_true", help="Run GraphQL API tests")
    parser.add_argument("--security", action="store_true", help="Run security and input sanitization tests")
    parser.add_argument("--websocket", action="store_true", help="Run WebSocket communication tests")
    
    # Options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-setup", action="store_true", help="Skip test environment setup")

    # Logging options
    parser.add_argument("--logs", action="store_true", help="Show recent log files and exit")
    parser.add_argument("--no-logging", action="store_true", help="Disable logging to file")

    args = parser.parse_args()

    # Initialize logger
    logger = TestLogger() if TestLogger and not args.no_logging else None

    # Handle logs command
    if args.logs:
        if logger:
            show_log_summary(logger)
        else:
            print("Logging utilities not available.")
        return
    
    # Setup test environment
    if not args.no_setup:
        setup_test_environment()
    
    # Determine which tests to run
    results = []

    # Check for endpoint test categories first
    endpoint_tests_run = False

    # Handle --endpoints flag (run all endpoint tests)
    if args.endpoints:
        endpoint_results = run_all_endpoint_tests(args.verbose, args.coverage, logger)
        results.extend(endpoint_results)
        endpoint_tests_run = True

    if getattr(args, 'multi_agent', False):
        results.append(run_multi_agent_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.documents:
        results.append(run_documents_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.orchestrator:
        results.append(run_orchestrator_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.realtime:
        results.append(run_realtime_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.multimodal:
        results.append(run_multimodal_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.graphql:
        results.append(run_graphql_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.security:
        results.append(run_security_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    if args.websocket:
        results.append(run_websocket_tests(args.verbose, args.coverage, logger))
        endpoint_tests_run = True

    # If no endpoint tests were specified, check for traditional test categories
    if not endpoint_tests_run:
        if args.unit:
            results.append(run_unit_tests(args.verbose, args.coverage, logger))
        elif args.integration:
            results.append(run_integration_tests(args.verbose, logger))
        elif args.e2e:
            results.append(run_e2e_tests(args.verbose, logger))
        elif args.performance:
            results.append(run_performance_tests(args.verbose, logger))
        elif args.fast:
            results.append(run_fast_tests(args.verbose, args.coverage, logger))
        else:
            # Run all tests by default (including new endpoint tests)
            print("\n🎪 Running Complete Test Suite (Traditional + New Endpoint Tests)")
            print("=" * 70)

            # Run traditional tests first
            results.append(run_all_tests(args.verbose, args.coverage, logger))

            # Then run all new endpoint tests
            endpoint_results = run_all_endpoint_tests(args.verbose, args.coverage, logger)
            results.extend(endpoint_results)
    
    # Print summary and exit with appropriate code
    success = print_test_summary(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
