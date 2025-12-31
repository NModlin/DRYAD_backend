"""
Level 5 Validation Script
DRYAD.AI Agent Evolution Architecture

Validates The Lyceum Self-Improvement Engine:
- Laboratory Sandbox (Environment Manager, Isolation Enforcer)
- Professor Agent (Research projects, experiments, proposals)
- Research Budgeting (Budget allocation and enforcement)
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.database import SessionLocal
from app.services.laboratory.environment_manager import EnvironmentManager
from app.services.laboratory.isolation_enforcer import IsolationEnforcer
from app.services.lyceum.professor_agent import ProfessorAgent
from app.services.lyceum.budget_manager import BudgetManager


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
        print("LEVEL 5 VALIDATION RESULTS")
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
            print("[PASS] LEVEL 5 VALIDATION: PASSED")
            print("  [+] All Level 5 components are working correctly")
            print("  [+] The Lyceum is fully operational")
            print("  [+] DRYAD.AI Agent Evolution Architecture is COMPLETE!\n")
            return True
        else:
            print("[FAIL] LEVEL 5 VALIDATION: FAILED")
            print(f"  [-] {total_tests - total_passed} test(s) failed")
            print("  [-] Fix failing tests before declaring completion\n")
            return False


def test_laboratory(results: ValidationResults):
    """Test Laboratory Sandbox components."""
    print("\n  Testing Laboratory Sandbox...")
    
    # Test 1: Environment Manager initialization
    try:
        env_manager = EnvironmentManager()
        results.add_test("laboratory", "Environment Manager initialization", True)
    except Exception as e:
        print(f"  [-] Environment Manager initialization failed: {e}")
        results.add_test("laboratory", "Environment Manager initialization", False)
        return
    
    # Test 2: Create environment
    try:
        env_config = env_manager.create_environment(
            experiment_id="test_exp_001",
            clone_production=False
        )
        passed = env_config.environment_id is not None and env_config.isolated
        results.add_test("laboratory", "Environment creation", passed)
    except Exception as e:
        print(f"  [-] Environment creation failed: {e}")
        results.add_test("laboratory", "Environment creation", False)
        return
    
    # Test 3: Environment isolation check
    try:
        is_isolated = env_manager.is_isolated(env_config.environment_id)
        results.add_test("laboratory", "Environment isolation", is_isolated)
    except Exception as e:
        print(f"  [-] Environment isolation check failed: {e}")
        results.add_test("laboratory", "Environment isolation", False)
    
    # Test 4: Destroy environment
    try:
        success = env_manager.destroy_environment(env_config.environment_id)
        results.add_test("laboratory", "Environment destruction", success)
    except Exception as e:
        print(f"  [-] Environment destruction failed: {e}")
        results.add_test("laboratory", "Environment destruction", False)
    
    # Test 5: Isolation Enforcer
    try:
        enforcer = IsolationEnforcer()
        
        # Test database access validation
        valid = enforcer.validate_database_access(
            "test_env",
            "data/laboratory/test_env/experiment.db"
        )
        
        # Test production database blocking
        blocked = not enforcer.validate_database_access(
            "test_env",
            "data/DRYAD.AI.db"
        )
        
        passed = valid and blocked
        results.add_test("laboratory", "Isolation enforcement", passed)
    except Exception as e:
        print(f"  [-] Isolation enforcement failed: {e}")
        results.add_test("laboratory", "Isolation enforcement", False)


async def test_professor_agent(results: ValidationResults, db):
    """Test Professor Agent component."""
    print("\n  Testing Professor Agent...")
    
    try:
        # Test 1: Initialization
        professor = ProfessorAgent(db, agent_id="test_professor")
        results.add_test("professor_agent", "Initialization", True)
    except Exception as e:
        print(f"  [-] Initialization failed: {e}")
        results.add_test("professor_agent", "Initialization", False)
        return
    
    # Test 2: Start research project
    try:
        project = await professor.start_research_project(
            hypothesis="Optimizing prompt templates can improve accuracy by 10%",
            target_component="memory_scribe"
        )
        passed = project.project_id is not None and project.status == "analyzing"
        results.add_test("professor_agent", "Research project creation", passed)
    except Exception as e:
        print(f"  [-] Research project creation failed: {e}")
        results.add_test("professor_agent", "Research project creation", False)
        return
    
    # Test 3: Run experiment
    try:
        experiment = await professor.run_experiment(
            project_id=project.project_id,
            experiment_type="prompt_optimization",
            configuration={"template": "improved_v2", "temperature": 0.7}
        )
        passed = experiment.experiment_id is not None and experiment.status == "completed"
        results.add_test("professor_agent", "Experiment execution", passed)
    except Exception as e:
        print(f"  [-] Experiment execution failed: {e}")
        results.add_test("professor_agent", "Experiment execution", False)
        return
    
    # Test 4: Submit proposal
    try:
        proposal = await professor.submit_proposal(
            project_id=project.project_id,
            experiment_id=experiment.experiment_id,
            title="Improved Prompt Template for Memory Scribe",
            description="New template shows 15% improvement in accuracy",
            implementation_details="Update prompt_templates.py with new template",
            validation_results={"improvement": 0.15, "p_value": 0.001, "effect_size": 0.8}
        )
        passed = proposal.proposal_id is not None and proposal.status == "pending_review"
        results.add_test("professor_agent", "Proposal submission", passed)
    except Exception as e:
        print(f"  [-] Proposal submission failed: {e}")
        results.add_test("professor_agent", "Proposal submission", False)
    
    # Test 5: Retrieve project
    try:
        retrieved = professor.get_project(project.project_id)
        passed = retrieved is not None and retrieved.project_id == project.project_id
        results.add_test("professor_agent", "Project retrieval", passed)
    except Exception as e:
        print(f"  [-] Project retrieval failed: {e}")
        results.add_test("professor_agent", "Project retrieval", False)


def test_budget_manager(results: ValidationResults, db):
    """Test Budget Manager component."""
    print("\n  Testing Budget Manager...")
    
    try:
        # Test 1: Initialization
        budget_mgr = BudgetManager(db)
        results.add_test("budget_manager", "Initialization", True)
    except Exception as e:
        print(f"  [-] Initialization failed: {e}")
        results.add_test("budget_manager", "Initialization", False)
        return
    
    # Test 2: Allocate budget
    try:
        budget = budget_mgr.allocate_budget(
            professor_agent_id="test_professor",
            compute_hours=100.0,
            period_days=30
        )
        passed = budget.budget_id is not None and budget.status == "active"
        results.add_test("budget_manager", "Budget allocation", passed)
    except Exception as e:
        print(f"  [-] Budget allocation failed: {e}")
        results.add_test("budget_manager", "Budget allocation", False)
        return
    
    # Test 3: Consume budget
    try:
        success = budget_mgr.consume_budget(
            professor_agent_id="test_professor",
            compute_hours=10.0
        )
        results.add_test("budget_manager", "Budget consumption", success)
    except Exception as e:
        print(f"  [-] Budget consumption failed: {e}")
        results.add_test("budget_manager", "Budget consumption", False)
    
    # Test 4: Get remaining budget
    try:
        remaining = budget_mgr.get_remaining_budget("test_professor")
        passed = remaining == 90.0  # 100 - 10
        results.add_test("budget_manager", "Remaining budget calculation", passed)
    except Exception as e:
        print(f"  [-] Remaining budget calculation failed: {e}")
        results.add_test("budget_manager", "Remaining budget calculation", False)
    
    # Test 5: Budget enforcement (insufficient budget)
    try:
        # Try to consume more than remaining
        success = budget_mgr.consume_budget(
            professor_agent_id="test_professor",
            compute_hours=200.0
        )
        passed = not success  # Should fail due to insufficient budget
        results.add_test("budget_manager", "Budget enforcement", passed)
    except Exception as e:
        print(f"  [-] Budget enforcement failed: {e}")
        results.add_test("budget_manager", "Budget enforcement", False)


async def run_validation():
    """Run all Level 5 validation tests."""
    results = ValidationResults()
    
    # Connect to database
    db_path = "data/DRYAD.AI.db"
    if not os.path.exists(db_path):
        print(f"[FAIL] Database not found: {db_path}")
        print("   Run create_level5_tables.py first!")
        return False
    
    db = SessionLocal()
    
    try:
        print("\nStarting Level 5 Validation...\n")
        print("="*70)
        print("DRYAD.AI Agent Evolution Architecture")
        print("Level 5: The Lyceum Self-Improvement Engine")
        print("="*70)
        
        # Test components
        test_laboratory(results)
        await test_professor_agent(results, db)
        test_budget_manager(results, db)
        
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

