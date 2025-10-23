#!/usr/bin/env python3
"""
Level 0 Validation Script

Validates that all Level 0 components are correctly implemented and functional.
"""

import sys
import subprocess
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text:^80}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print_success(f"File exists: {filepath}")
        return True
    else:
        print_error(f"File missing: {filepath}")
        return False


def run_tests(test_path: str) -> bool:
    """Run pytest for a specific path."""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short", "--no-cov"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_success(f"All tests passed: {test_path}")
            return True
        else:
            print_error(f"Tests failed: {test_path}")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print_error("pytest not found. Install with: pip install pytest pytest-asyncio")
        return False


def validate_tool_registry() -> bool:
    """Validate Tool Registry Service implementation."""
    print_header("Validating Tool Registry Service (Level 0, Component 1)")
    
    all_valid = True
    
    # Check core files
    print_info("Checking core service files...")
    files = [
        "app/services/tool_registry/__init__.py",
        "app/services/tool_registry/models.py",
        "app/services/tool_registry/schemas.py",
        "app/services/tool_registry/service.py",
        "app/services/tool_registry/exceptions.py",
    ]
    for file in files:
        if not check_file_exists(file):
            all_valid = False
    
    # Check API endpoint
    print_info("\nChecking API endpoint...")
    if not check_file_exists("app/api/v1/endpoints/tool_registry.py"):
        all_valid = False
    
    # Check migration
    print_info("\nChecking database migration...")
    if not check_file_exists("alembic/versions/2025_01_10_create_tool_registry_tables.py"):
        all_valid = False
    
    # Check test files
    print_info("\nChecking test files...")
    test_files = [
        "tests/services/tool_registry/__init__.py",
        "tests/services/tool_registry/conftest.py",
        "tests/services/tool_registry/test_models.py",
        "tests/services/tool_registry/test_service.py",
    ]
    for file in test_files:
        if not check_file_exists(file):
            all_valid = False
    
    # Run tests
    print_info("\nRunning tests...")
    if not run_tests("tests/services/tool_registry/"):
        all_valid = False
    
    return all_valid


def validate_memory_database() -> bool:
    """Validate Memory Guild Database Schema implementation."""
    print_header("Validating Memory Guild Database Schema (Level 0, Component 2)")

    all_valid = True

    # Check core files
    print_info("Checking core model files...")
    files = [
        "app/services/memory_guild/__init__.py",
        "app/services/memory_guild/models.py",
    ]
    for file in files:
        if not check_file_exists(file):
            all_valid = False

    # Check migration
    print_info("\nChecking database migration...")
    if not check_file_exists("alembic/versions/2025_01_10_create_memory_guild_tables.py"):
        all_valid = False

    # Check test files
    print_info("\nChecking test files...")
    test_files = [
        "tests/services/memory_guild/__init__.py",
        "tests/services/memory_guild/conftest.py",
        "tests/services/memory_guild/test_models.py",
    ]
    for file in test_files:
        if not check_file_exists(file):
            all_valid = False

    # Run tests
    print_info("\nRunning tests...")
    if not run_tests("tests/services/memory_guild/"):
        all_valid = False

    return all_valid


def validate_structured_logging() -> bool:
    """Validate Structured Logging Service implementation."""
    print_header("Validating Structured Logging Service (Level 0, Component 3)")

    all_valid = True

    # Check core files
    print_info("Checking core service files...")
    files = [
        "app/services/logging/__init__.py",
        "app/services/logging/models.py",
        "app/services/logging/schemas.py",
        "app/services/logging/logger.py",
        "app/services/logging/query_service.py",
    ]
    for file in files:
        if not check_file_exists(file):
            all_valid = False

    # Check API endpoint
    print_info("\nChecking API endpoint...")
    if not check_file_exists("app/api/v1/endpoints/logging.py"):
        all_valid = False

    # Check migration
    print_info("\nChecking database migration...")
    if not check_file_exists("alembic/versions/2025_01_10_create_logging_tables.py"):
        all_valid = False

    # Check test files
    print_info("\nChecking test files...")
    test_files = [
        "tests/services/structured_logging/__init__.py",
        "tests/services/structured_logging/conftest.py",
        "tests/services/structured_logging/test_models.py",
        "tests/services/structured_logging/test_logger.py",
        "tests/services/structured_logging/test_query.py",
    ]
    for file in test_files:
        if not check_file_exists(file):
            all_valid = False

    # Run tests
    print_info("\nRunning tests...")
    if not run_tests("tests/services/structured_logging/"):
        all_valid = False

    return all_valid


def main():
    """Main validation function."""
    print_header("DRYAD.AI Level 0 Validation")
    print_info("Validating Foundation Services (Level 0)")
    print_info("Components: Tool Registry, Memory Database, Structured Logging\n")
    
    results = {
        "Tool Registry Service": validate_tool_registry(),
        "Memory Guild Database Schema": validate_memory_database(),
        "Structured Logging Service": validate_structured_logging(),
    }
    
    # Print summary
    print_header("Validation Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for component, result in results.items():
        if result:
            print_success(f"{component}: PASSED")
        else:
            print_error(f"{component}: FAILED")
    
    print(f"\n{BLUE}{'─' * 80}{RESET}")
    print(f"Total Components: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print(f"{BLUE}{'─' * 80}{RESET}\n")
    
    if passed == total:
        print_success("✨ Level 0 Complete - All components validated!")
        print_info("You can now proceed to Level 1 (Execution & Memory Agents)")
        return 0
    else:
        print_error("❌ Level 0 Incomplete - Fix failing components before proceeding")
        print_info(f"Progress: {passed}/{total} components complete ({passed/total*100:.1f}%)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

