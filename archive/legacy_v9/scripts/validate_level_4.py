"""
Level 4 Validation Script
DRYAD.AI Agent Evolution Architecture

Validates The Dojo Evaluation Framework:
- Benchmark Registry
- Evaluation Harness
- RAG-Gym Benchmarks
"""

import asyncio
import os
import sys
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.database import SessionLocal
from app.services.dojo.benchmark_registry import BenchmarkRegistry, BenchmarkCreate
from app.services.dojo.evaluation_harness import EvaluationHarness, EvaluationRequest
from app.services.dojo.rag_gym.ingestion_benchmark import IngestionBenchmark
from app.services.dojo.rag_gym.retrieval_benchmark import RetrievalBenchmark
from app.services.dojo.rag_gym.deduplication_benchmark import DeduplicationBenchmark


class ValidationResults:
    """Track validation test results."""
    
    def __init__(self):
        self.tests = {}
        self.component_scores = {}
    
    def add_test(self, component: str, test_name: str, passed: bool):
        """Add a test result."""
        if component not in self.tests:
            self.tests[component] = []
        self.tests[component].append((test_name, passed))
    
    def calculate_scores(self):
        """Calculate component scores."""
        for component, tests in self.tests.items():
            passed = sum(1 for _, p in tests if p)
            total = len(tests)
            self.component_scores[component] = (passed, total)
    
    def print_results(self):
        """Print formatted results."""
        self.calculate_scores()
        
        print("\n" + "="*70)
        print("LEVEL 4 VALIDATION RESULTS")
        print("="*70 + "\n")
        
        total_passed = 0
        total_tests = 0
        
        for component in sorted(self.component_scores.keys()):
            passed, total = self.component_scores[component]
            total_passed += passed
            total_tests += total

            percentage = (passed / total * 100) if total > 0 else 0
            status = "[PASS]" if passed == total else "[FAIL]"

            print(f"{status} {component.upper()}: {passed}/{total} tests ({percentage:.1f}%)")

            # Show individual test results
            for test_name, test_passed in self.tests[component]:
                test_status = "  [+]" if test_passed else "  [-]"
                print(f"{test_status} {test_name}")
            print()
        
        print("="*70)
        print(f"OVERALL SCORE: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%)")
        print("="*70 + "\n")
        
        if total_passed == total_tests:
            print("[PASS] LEVEL 4 VALIDATION: PASSED")
            print("  [+] All Level 4 components are working correctly")
            print("  [+] The Dojo is fully operational")
            print("  [+] Ready to proceed to Level 5 implementation\n")
            return True
        else:
            print("[FAIL] LEVEL 4 VALIDATION: FAILED")
            print(f"  [-] {total_tests - total_passed} test(s) failed")
            print("  [-] Fix failing tests before proceeding to Level 5\n")
            return False


async def test_benchmark_registry(results: ValidationResults, db):
    """Test Benchmark Registry component."""
    print("\n  Testing Benchmark Registry...")
    
    try:
        # Test 1: Initialization
        registry = BenchmarkRegistry(db)
        results.add_test("benchmark_registry", "Initialization", True)
    except Exception as e:
        print(f"  [-] Initialization failed: {e}")
        results.add_test("benchmark_registry", "Initialization", False)
        return
    
    # Test 2: Register benchmark
    try:
        import uuid
        unique_name = f"test_benchmark_{uuid.uuid4().hex[:8]}"
        benchmark = BenchmarkCreate(
            name=unique_name,
            version="1.0.0",
            description="Test benchmark for validation",
            category="general",
            dataset_uri="file://test_dataset.json",
            evaluation_logic_uri="file://test_eval.py",
            metadata={"test": True}
        )
        created = registry.register_benchmark(benchmark)
        passed = created.benchmark_id is not None and created.name == unique_name
        results.add_test("benchmark_registry", "Benchmark registration", passed)
    except Exception as e:
        print(f"  [-] Benchmark registration failed: {e}")
        results.add_test("benchmark_registry", "Benchmark registration", False)
        return
    
    # Test 3: Retrieve benchmark
    try:
        retrieved = registry.get_benchmark(created.benchmark_id)
        passed = retrieved is not None and retrieved.name == unique_name
        results.add_test("benchmark_registry", "Benchmark retrieval", passed)
    except Exception as e:
        print(f"  [-] Benchmark retrieval failed: {e}")
        results.add_test("benchmark_registry", "Benchmark retrieval", False)
    
    # Test 4: List benchmarks
    try:
        benchmarks = registry.list_benchmarks(category="general")
        passed = len(benchmarks) > 0
        results.add_test("benchmark_registry", "Benchmark listing", passed)
    except Exception as e:
        print(f"  [-] Benchmark listing failed: {e}")
        results.add_test("benchmark_registry", "Benchmark listing", False)
    
    # Test 5: Deactivate benchmark
    try:
        success = registry.deactivate_benchmark(created.benchmark_id)
        results.add_test("benchmark_registry", "Benchmark deactivation", success)
    except Exception as e:
        print(f"  [-] Benchmark deactivation failed: {e}")
        results.add_test("benchmark_registry", "Benchmark deactivation", False)


async def test_evaluation_harness(results: ValidationResults, db):
    """Test Evaluation Harness component."""
    print("\n  Testing Evaluation Harness...")
    
    try:
        # Test 1: Initialization
        harness = EvaluationHarness(db)
        results.add_test("evaluation_harness", "Initialization", True)
    except Exception as e:
        print(f"  [-] Initialization failed: {e}")
        results.add_test("evaluation_harness", "Initialization", False)
        return
    
    # Create a test benchmark first
    import uuid
    registry = BenchmarkRegistry(db)
    unique_name = f"eval_test_benchmark_{uuid.uuid4().hex[:8]}"
    benchmark = BenchmarkCreate(
        name=unique_name,
        version="1.0.0",
        category="memory",
        dataset_uri="file://test.json",
        evaluation_logic_uri="file://eval.py"
    )
    created_benchmark = registry.register_benchmark(benchmark)
    
    # Test 2: Run evaluation
    try:
        request = EvaluationRequest(
            agent_id="test_agent",
            agent_version="1.0.0",
            benchmark_id=created_benchmark.benchmark_id
        )
        result = await harness.run_evaluation(request)
        passed = result.status == "completed" and result.run_id is not None
        results.add_test("evaluation_harness", "Evaluation execution", passed)
    except Exception as e:
        print(f"  [-] Evaluation execution failed: {e}")
        results.add_test("evaluation_harness", "Evaluation execution", False)
        return
    
    # Test 3: Retrieve evaluation result
    try:
        retrieved = harness.get_evaluation_result(result.run_id)
        passed = retrieved is not None and retrieved.status == "completed"
        results.add_test("evaluation_harness", "Result retrieval", passed)
    except Exception as e:
        print(f"  [-] Result retrieval failed: {e}")
        results.add_test("evaluation_harness", "Result retrieval", False)
    
    # Test 4: Generate leaderboard
    try:
        leaderboard = harness.get_leaderboard(created_benchmark.benchmark_id, limit=5)
        passed = len(leaderboard) > 0
        results.add_test("evaluation_harness", "Leaderboard generation", passed)
    except Exception as e:
        print(f"  [-] Leaderboard generation failed: {e}")
        results.add_test("evaluation_harness", "Leaderboard generation", False)


async def test_rag_gym(results: ValidationResults):
    """Test RAG-Gym benchmarks."""
    print("\n  Testing RAG-Gym Benchmarks...")
    
    # Test 1: Ingestion Benchmark
    try:
        ingestion = IngestionBenchmark()
        scores = await ingestion.evaluate(None)  # Mock evaluation
        passed = "overall_score" in scores and scores["overall_score"] > 0
        results.add_test("rag_gym", "Ingestion benchmark", passed)
    except Exception as e:
        print(f"  [-] Ingestion benchmark failed: {e}")
        results.add_test("rag_gym", "Ingestion benchmark", False)
    
    # Test 2: Retrieval Benchmark
    try:
        retrieval = RetrievalBenchmark()
        scores = await retrieval.evaluate(None, k=5)  # Mock evaluation
        passed = "overall_score" in scores and scores["overall_score"] > 0
        results.add_test("rag_gym", "Retrieval benchmark", passed)
    except Exception as e:
        print(f"  [-] Retrieval benchmark failed: {e}")
        results.add_test("rag_gym", "Retrieval benchmark", False)
    
    # Test 3: Deduplication Benchmark
    try:
        dedup = DeduplicationBenchmark()
        scores = await dedup.evaluate(None)  # Mock evaluation
        passed = "overall_score" in scores and scores["overall_score"] > 0
        results.add_test("rag_gym", "Deduplication benchmark", passed)
    except Exception as e:
        print(f"  [-] Deduplication benchmark failed: {e}")
        results.add_test("rag_gym", "Deduplication benchmark", False)


async def run_validation():
    """Run all Level 4 validation tests."""
    results = ValidationResults()

    # Connect to database
    db_path = "data/DRYAD.AI.db"
    if not os.path.exists(db_path):
        print(f"[FAIL] Database not found: {db_path}")
        print("   Run create_level4_tables.py first!")
        return False

    db = SessionLocal()

    try:
        print("\nStarting Level 4 Validation...\n")
        print("="*70)
        print("DRYAD.AI Agent Evolution Architecture")
        print("Level 4: The Dojo Evaluation Framework")
        print("="*70)

        # Test components
        await test_benchmark_registry(results, db)
        await test_evaluation_harness(results, db)
        await test_rag_gym(results)

    finally:
        db.close()

    # Print results
    success = results.print_results()
    return success


def main():
    """Main validation entry point."""
    try:
        success = asyncio.run(run_validation())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

