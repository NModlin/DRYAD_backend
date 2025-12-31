"""
Level 3 Validation Script

Tests all Level 3 components:
1. Orchestration (Complexity Scorer, Decision Engine, Task Force Manager, Orchestrator)
2. HITL (State Manager, Consultation Manager)

Run after implementing Level 3 components.
"""

import sys
import os
import asyncio
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestration.complexity_scorer import ComplexityScorer
from app.services.orchestration.decision_engine import DecisionEngine
from app.services.orchestration.task_force_manager import TaskForceManager
from app.services.orchestration.orchestrator import HybridOrchestrator, OrchestrationRequest
from app.services.hitl.state_manager import AgentStateManager, AgentState
from app.services.hitl.consultation_manager import ConsultationManager


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
        print("LEVEL 3 VALIDATION RESULTS")
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
        overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"OVERALL SCORE: {total_passed}/{total_tests} tests passed ({overall_percentage:.1f}%)")
        print("="*70 + "\n")

        if total_passed == total_tests:
            print("[PASS] LEVEL 3 VALIDATION: PASSED")
            return True
        else:
            print("[FAIL] LEVEL 3 VALIDATION: FAILED")
            return False


async def test_complexity_scorer(results: ValidationResults):
    """Test Complexity Scorer component."""
    print("Testing Complexity Scorer...")
    
    try:
        scorer = ComplexityScorer()
        results.add_test("COMPLEXITY_SCORER", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("COMPLEXITY_SCORER", "Initialization", False)
        return
    
    # Test simple task scoring
    try:
        score = scorer.score_task("Update user profile")
        passed = (
            score.total_score < 0.55 and
            not score.requires_collaboration and
            len(score.dimensions) == 5
        )
        results.add_test("COMPLEXITY_SCORER", "Simple task scoring", passed)
    except Exception as e:
        print(f"  ❌ Simple task scoring failed: {e}")
        results.add_test("COMPLEXITY_SCORER", "Simple task scoring", False)

    # Test complex task scoring
    try:
        score = scorer.score_task(
            "Implement comprehensive security audit across multiple database systems with testing",
            {"num_subtasks": 5, "required_skills": ["security", "database", "testing"]}
        )
        passed = (
            score.total_score > 0.55 and
            score.requires_collaboration
        )
        results.add_test("COMPLEXITY_SCORER", "Complex task scoring", passed)
    except Exception as e:
        print(f"  [-] Complex task scoring failed: {e}")
        results.add_test("COMPLEXITY_SCORER", "Complex task scoring", False)
    
    # Test dimension scoring
    try:
        score = scorer.score_task("Research and investigate unclear requirements")
        passed = score.dimensions.get("uncertainty", 0) > 0.3
        results.add_test("COMPLEXITY_SCORER", "Dimension scoring", passed)
    except Exception as e:
        print(f"  ❌ Dimension scoring failed: {e}")
        results.add_test("COMPLEXITY_SCORER", "Dimension scoring", False)


async def test_decision_engine(results: ValidationResults, db):
    """Test Decision Engine component."""
    print("Testing Decision Engine...")
    
    try:
        engine = DecisionEngine(db)
        results.add_test("DECISION_ENGINE", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("DECISION_ENGINE", "Initialization", False)
        return
    
    # Test sequential decision
    try:
        decision = await engine.make_decision(
            task_id="task_001",
            task_description="Simple update task"
        )
        passed = decision.decision_type == "sequential"
        results.add_test("DECISION_ENGINE", "Sequential decision", passed)
    except Exception as e:
        print(f"  ❌ Sequential decision failed: {e}")
        results.add_test("DECISION_ENGINE", "Sequential decision", False)
    
    # Test task force decision
    try:
        decision = await engine.make_decision(
            task_id="task_002",
            task_description="Implement comprehensive security audit across multiple database systems with testing",
            context={"num_subtasks": 5, "required_skills": ["security", "database", "testing"]}
        )
        passed = decision.decision_type == "task_force"
        results.add_test("DECISION_ENGINE", "Task force decision", passed)
    except Exception as e:
        print(f"  [-] Task force decision failed: {e}")
        results.add_test("DECISION_ENGINE", "Task force decision", False)
    
    # Test decision persistence
    try:
        stats = engine.get_decision_stats()
        passed = stats.get("total_decisions", 0) >= 2
        results.add_test("DECISION_ENGINE", "Decision persistence", passed)
    except Exception as e:
        print(f"  ❌ Decision persistence failed: {e}")
        results.add_test("DECISION_ENGINE", "Decision persistence", False)


async def test_task_force_manager(results: ValidationResults, db):
    """Test Task Force Manager component."""
    print("Testing Task Force Manager...")
    
    try:
        manager = TaskForceManager(db)
        results.add_test("TASK_FORCE_MANAGER", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("TASK_FORCE_MANAGER", "Initialization", False)
        return
    
    # Test task force creation
    try:
        task_force = await manager.create_task_force(
            objective="Build secure API",
            orchestrator_id="orchestrator_001",
            agent_roles=["api_specialist", "security_specialist"]
        )
        passed = (
            task_force.status == "active" and
            len(task_force.members) == 2
        )
        results.add_test("TASK_FORCE_MANAGER", "Task force creation", passed)
        
        # Store for later tests
        test_task_force_id = task_force.task_force_id
    except Exception as e:
        print(f"  ❌ Task force creation failed: {e}")
        results.add_test("TASK_FORCE_MANAGER", "Task force creation", False)
        return
    
    # Test message sending
    try:
        message = await manager.send_message(
            task_force_id=test_task_force_id,
            agent_id="agent_api_specialist",
            message_type="proposal",
            content={"proposal": "Use REST API design"}
        )
        passed = message.message_type == "proposal"
        results.add_test("TASK_FORCE_MANAGER", "Message sending", passed)
    except Exception as e:
        print(f"  ❌ Message sending failed: {e}")
        results.add_test("TASK_FORCE_MANAGER", "Message sending", False)
    
    # Test message retrieval
    try:
        messages = await manager.get_messages(test_task_force_id)
        passed = len(messages) >= 1
        results.add_test("TASK_FORCE_MANAGER", "Message retrieval", passed)
    except Exception as e:
        print(f"  ❌ Message retrieval failed: {e}")
        results.add_test("TASK_FORCE_MANAGER", "Message retrieval", False)
    
    # Test task force resolution
    try:
        success = await manager.resolve_task_force(
            task_force_id=test_task_force_id,
            result={"api_design": "REST", "security": "OAuth2"}
        )
        results.add_test("TASK_FORCE_MANAGER", "Task force resolution", success)
    except Exception as e:
        print(f"  ❌ Task force resolution failed: {e}")
        results.add_test("TASK_FORCE_MANAGER", "Task force resolution", False)


async def test_orchestrator(results: ValidationResults, db):
    """Test Hybrid Orchestrator component."""
    print("Testing Hybrid Orchestrator...")
    
    try:
        orchestrator = HybridOrchestrator(db)
        results.add_test("ORCHESTRATOR", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("ORCHESTRATOR", "Initialization", False)
        return
    
    # Test sequential orchestration
    try:
        request = OrchestrationRequest(
            task_id="orch_task_001",
            task_description="Simple data update",
            agent_id="agent_001"
        )
        result = await orchestrator.orchestrate(request)
        passed = result.decision_type == "sequential"
        results.add_test("ORCHESTRATOR", "Sequential orchestration", passed)
    except Exception as e:
        print(f"  ❌ Sequential orchestration failed: {e}")
        results.add_test("ORCHESTRATOR", "Sequential orchestration", False)
    
    # Test task force orchestration
    try:
        request = OrchestrationRequest(
            task_id="orch_task_002",
            task_description="Implement comprehensive security audit across multiple database systems with testing",
            agent_id="agent_002",
            context={"num_subtasks": 5, "required_skills": ["security", "database", "testing"]}
        )
        result = await orchestrator.orchestrate(request)
        passed = result.decision_type == "task_force" and result.task_force_id is not None
        results.add_test("ORCHESTRATOR", "Task force orchestration", passed)
    except Exception as e:
        print(f"  [-] Task force orchestration failed: {e}")
        results.add_test("ORCHESTRATOR", "Task force orchestration", False)
    
    # Test orchestration stats
    try:
        stats = await orchestrator.get_orchestration_stats()
        passed = "total_decisions" in stats
        results.add_test("ORCHESTRATOR", "Orchestration stats", passed)
    except Exception as e:
        print(f"  ❌ Orchestration stats failed: {e}")
        results.add_test("ORCHESTRATOR", "Orchestration stats", False)


async def test_state_manager(results: ValidationResults):
    """Test Agent State Manager component."""
    print("Testing Agent State Manager...")

    try:
        manager = AgentStateManager()
        results.add_test("STATE_MANAGER", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("STATE_MANAGER", "Initialization", False)
        return

    # Test state setting
    try:
        state = await manager.set_state(
            agent_id="agent_hitl_001",
            state=AgentState.ACTIVE,
            task_id="task_hitl_001"
        )
        passed = state.state == AgentState.ACTIVE
        results.add_test("STATE_MANAGER", "State setting", passed)
    except Exception as e:
        print(f"  ❌ State setting failed: {e}")
        results.add_test("STATE_MANAGER", "State setting", False)

    # Test pause for consultation
    try:
        state = await manager.pause_for_consultation(
            agent_id="agent_hitl_001",
            task_id="task_hitl_001",
            consultation_id="consult_001"
        )
        passed = state.state == AgentState.PAUSED_FOR_CONSULTATION
        results.add_test("STATE_MANAGER", "Pause for consultation", passed)
    except Exception as e:
        print(f"  ❌ Pause for consultation failed: {e}")
        results.add_test("STATE_MANAGER", "Pause for consultation", False)

    # Test resume from consultation
    try:
        state = await manager.resume_from_consultation(
            agent_id="agent_hitl_001",
            resolution={"decision": "approved"}
        )
        passed = state.state == AgentState.ACTIVE
        results.add_test("STATE_MANAGER", "Resume from consultation", passed)
    except Exception as e:
        print(f"  ❌ Resume from consultation failed: {e}")
        results.add_test("STATE_MANAGER", "Resume from consultation", False)

    # Test is_paused check
    try:
        await manager.pause_for_consultation("agent_002", "task_002", "consult_002")
        is_paused = await manager.is_paused("agent_002")
        results.add_test("STATE_MANAGER", "Is paused check", is_paused)
    except Exception as e:
        print(f"  ❌ Is paused check failed: {e}")
        results.add_test("STATE_MANAGER", "Is paused check", False)


async def test_consultation_manager(results: ValidationResults, db):
    """Test Consultation Manager component."""
    print("Testing Consultation Manager...")

    try:
        manager = ConsultationManager(db)
        results.add_test("CONSULTATION_MANAGER", "Initialization", True)
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Initialization", False)
        return

    # Test consultation request
    try:
        consultation = await manager.request_consultation(
            agent_id="agent_consult_001",
            task_id="task_consult_001",
            consultation_type="approval",
            context={"action": "delete_database", "impact": "high"}
        )
        passed = consultation.status == "pending"
        results.add_test("CONSULTATION_MANAGER", "Consultation request", passed)

        # Store for later tests
        test_consultation_id = consultation.consultation_id
    except Exception as e:
        print(f"  ❌ Consultation request failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Consultation request", False)
        return

    # Test message sending
    try:
        message = await manager.send_message(
            consultation_id=test_consultation_id,
            sender_type="agent",
            sender_id="agent_consult_001",
            content={"question": "Should I proceed with deletion?"}
        )
        passed = message.sender_type == "agent"
        results.add_test("CONSULTATION_MANAGER", "Message sending", passed)
    except Exception as e:
        print(f"  ❌ Message sending failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Message sending", False)

    # Test message retrieval
    try:
        messages = await manager.get_messages(test_consultation_id)
        passed = len(messages) >= 1
        results.add_test("CONSULTATION_MANAGER", "Message retrieval", passed)
    except Exception as e:
        print(f"  ❌ Message retrieval failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Message retrieval", False)

    # Test consultation resolution
    try:
        success = await manager.resolve_consultation(
            consultation_id=test_consultation_id,
            resolution={"decision": "approved", "notes": "Proceed with caution"}
        )
        results.add_test("CONSULTATION_MANAGER", "Consultation resolution", success)
    except Exception as e:
        print(f"  ❌ Consultation resolution failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Consultation resolution", False)

    # Test pending consultations
    try:
        pending = await manager.get_pending_consultations()
        passed = isinstance(pending, list)
        results.add_test("CONSULTATION_MANAGER", "Pending consultations", passed)
    except Exception as e:
        print(f"  ❌ Pending consultations failed: {e}")
        results.add_test("CONSULTATION_MANAGER", "Pending consultations", False)


async def run_validation():
    """Run all Level 3 validation tests."""
    results = ValidationResults()

    # Connect to database
    db_path = "data/DRYAD.AI.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   Run create_level3_tables.py first!")
        return False

    db = sqlite3.connect(db_path)

    try:
        # Test Orchestration components
        await test_complexity_scorer(results)
        await test_decision_engine(results, db)
        await test_task_force_manager(results, db)
        await test_orchestrator(results, db)

        # Test HITL components
        await test_state_manager(results)
        await test_consultation_manager(results, db)

    finally:
        db.close()

    # Print results
    success = results.print_results()
    return success


def main():
    """Main entry point."""
    print("\nStarting Level 3 Validation...\n")

    success = asyncio.run(run_validation())

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

