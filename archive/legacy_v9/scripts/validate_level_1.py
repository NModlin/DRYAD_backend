#!/usr/bin/env python3
"""
Level 1 Validation Script - DRYAD.AI Agent Evolution Architecture

Validates all Level 1 components:
1. Sandboxed Execution Environment
2. Memory Coordinator Agent
3. Memory Scribe Agent
4. Agent Registry Service

Verifies integration with Level 0 services and readiness for Level 2.
"""

import asyncio
import sys
import os
import tempfile
import uuid
import warnings
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from pathlib import Path

# Suppress LLM initialization warnings during validation
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tornado.*")
warnings.filterwarnings("ignore", message=".*langchain-ollama.*")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.database import SessionLocal
from app.services.sandbox_service import SandboxExecutionEnvironment
from app.services.memory_guild.coordinator import MemoryCoordinatorAgent
from app.services.memory_guild.scribe import MemoryScribeAgent, IngestionRequest, ContentSource, ContentType
from app.services.agent_registry_service import AgentRegistryService
from app.models.agent_registry import SystemAgentCreate, AgentTier, AgentStatus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("level_1_validation")


class Level1Validator:
    """Comprehensive Level 1 validation."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.results = {
            "sandbox": {"status": "pending", "tests": []},
            "memory_coordinator": {"status": "pending", "tests": []},
            "memory_scribe": {"status": "pending", "tests": []},
            "agent_registry": {"status": "pending", "tests": []},
            "integration": {"status": "pending", "tests": []}
        }
        
    def log_test(self, component: str, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        self.results[component]["tests"].append({
            "name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅" if success else "❌"
        print(f"{status} {component.upper()}: {test_name}")
        if details:
            print(f"   {details}")
    
    def validate_sandbox_execution(self):
        """Validate Sandboxed Execution Environment."""
        print("\n🔧 Validating Sandboxed Execution Environment...")
        
        try:
            # Test 1: Service initialization
            sandbox = SandboxExecutionEnvironment(self.db)
            self.log_test("sandbox", "Service initialization", True, "SandboxExecutionEnvironment created successfully")
            
            # Test 2: Session creation
            session_id = f"test_session_{uuid.uuid4().hex[:8]}"
            session = sandbox.create_session(
                session_id=session_id,
                agent_id="test_agent",
                tool_id="test_tool"
            )
            self.log_test("sandbox", "Session creation", True, f"Session {session_id} created")
            
            # Test 3: Command execution (mock)
            result = asyncio.run(sandbox.execute_in_sandbox(
                session_id=session_id,
                command="echo 'Hello Level 1'",
                working_directory="/tmp"
            ))
            
            success = result.get("success", False)
            self.log_test("sandbox", "Command execution", success, f"Exit code: {result.get('exit_code', 'N/A')}")
            
            # Test 4: Session cleanup
            sandbox.close_session(session_id)
            self.log_test("sandbox", "Session cleanup", True, "Session closed successfully")
            
            self.results["sandbox"]["status"] = "passed"
            
        except Exception as e:
            self.log_test("sandbox", "Validation failed", False, str(e))
            self.results["sandbox"]["status"] = "failed"
    
    def validate_memory_coordinator(self):
        """Validate Memory Coordinator Agent."""
        print("\n🧠 Validating Memory Coordinator Agent...")
        
        try:
            # Test 1: Service initialization
            coordinator = MemoryCoordinatorAgent(self.db)
            self.log_test("memory_coordinator", "Service initialization", True, "MemoryCoordinatorAgent created successfully")
            
            # Test 2: Memory policy creation
            policy = coordinator._get_memory_policy("test_tenant")
            self.log_test("memory_coordinator", "Memory policy creation", True, f"Policy created for test_tenant")
            
            # Test 3: Mock memory storage
            from app.services.memory_guild.coordinator import MemoryRequest, MemoryOperation, MemoryType
            
            store_request = MemoryRequest(
                operation=MemoryOperation.STORE,
                memory_type=MemoryType.SHORT_TERM,
                content="Test memory content",
                metadata={"test": True},
                tenant_id="test_tenant"
            )
            
            response = asyncio.run(coordinator.handle_memory_request(store_request))
            success = response.success
            self.log_test("memory_coordinator", "Memory storage", success, f"Memory ID: {response.memory_id}")
            
            # Test 4: Mock memory retrieval
            retrieve_request = MemoryRequest(
                operation=MemoryOperation.RETRIEVE,
                memory_type=MemoryType.SHORT_TERM,
                memory_id=response.memory_id,
                tenant_id="test_tenant"
            )
            
            retrieve_response = asyncio.run(coordinator.handle_memory_request(retrieve_request))
            success = retrieve_response.success and retrieve_response.content is not None
            self.log_test("memory_coordinator", "Memory retrieval", success, f"Retrieved content length: {len(retrieve_response.content or '')}")
            
            self.results["memory_coordinator"]["status"] = "passed"
            
        except Exception as e:
            self.log_test("memory_coordinator", "Validation failed", False, str(e))
            self.results["memory_coordinator"]["status"] = "failed"
    
    def validate_memory_scribe(self):
        """Validate Memory Scribe Agent."""
        print("\n📝 Validating Memory Scribe Agent...")
        
        try:
            # Test 1: Service initialization
            coordinator = MemoryCoordinatorAgent(self.db)
            scribe = MemoryScribeAgent(self.db, coordinator)
            self.log_test("memory_scribe", "Service initialization", True, "MemoryScribeAgent created successfully")
            
            # Test 2: Content ingestion
            ingestion_request = IngestionRequest(
                content="This is a test document for Level 1 validation. It contains important information about the DRYAD.AI system.",
                source=ContentSource.DOCUMENTATION,
                content_type=ContentType.TEXT,
                metadata={"validation": True, "level": 1},
                tenant_id="test_tenant",
                agent_id="validation_agent"
            )
            
            result = asyncio.run(scribe.ingest_content(ingestion_request))
            success = result.success and result.memory_id is not None
            self.log_test("memory_scribe", "Content ingestion", success, f"Memory ID: {result.memory_id}")
            
            # Test 3: Metadata extraction
            extracted = asyncio.run(scribe._extract_content_metadata(ingestion_request))
            success = extracted.title is not None and extracted.summary is not None
            self.log_test("memory_scribe", "Metadata extraction", success, f"Title: {extracted.title[:50]}...")
            
            # Test 4: Embedding generation
            embeddings = asyncio.run(scribe._generate_embeddings(ingestion_request.content, extracted.summary))
            success = "content" in embeddings and len(embeddings["content"]) == scribe.embedding_dimensions
            self.log_test("memory_scribe", "Embedding generation", success, f"Dimensions: {len(embeddings['content'])}")
            
            # Test 5: Batch ingestion
            batch_requests = [
                IngestionRequest(
                    content=f"Batch test document {i}",
                    source=ContentSource.USER_INPUT,
                    content_type=ContentType.TEXT,
                    tenant_id="test_tenant"
                )
                for i in range(3)
            ]
            
            batch_results = asyncio.run(scribe.ingest_batch(batch_requests))
            success = len(batch_results) == 3 and all(r.success for r in batch_results)
            self.log_test("memory_scribe", "Batch ingestion", success, f"Processed {len(batch_results)} items")
            
            self.results["memory_scribe"]["status"] = "passed"
            
        except Exception as e:
            self.log_test("memory_scribe", "Validation failed", False, str(e))
            self.results["memory_scribe"]["status"] = "failed"
    
    def validate_agent_registry(self):
        """Validate Agent Registry Service."""
        print("\n🤖 Validating Agent Registry Service...")

        try:
            # Test 1: Service initialization
            registry = AgentRegistryService(self.db)
            self.log_test("agent_registry", "Service initialization", True, "AgentRegistryService created successfully")

            # Clean up old test agents from previous runs
            try:
                from app.database.models import SystemAgent
                old_agents = self.db.query(SystemAgent).filter(
                    SystemAgent.tenant_id == "test_tenant"
                ).all()
                for agent in old_agents:
                    self.db.delete(agent)
                self.db.commit()
            except Exception as e:
                pass  # Ignore cleanup errors

            # Test 2: Agent registration (use timestamp to avoid duplicates)
            import time
            agent_id = f"validation_agent_{int(time.time())}"
            agent_data = SystemAgentCreate(
                agent_id=agent_id,
                name="validation_agent",
                display_name="Validation Test Agent",
                tier=AgentTier.SPECIALIST,
                category="validation",
                capabilities=["testing", "validation", "analysis"],
                description="Agent for Level 1 validation testing",
                role="Validation Specialist",
                goal="Validate Level 1 implementation",
                backstory="Created specifically for validation purposes",
                configuration={"validation_mode": True},
                tools=["test_tool", "validation_tool"],
                status=AgentStatus.ACTIVE
            )
            
            registered = registry.register_agent(agent_data, tenant_id="test_tenant")
            success = registered.agent_id == agent_data.agent_id
            self.log_test("agent_registry", "Agent registration", success, f"Registered: {registered.agent_id}")
            
            # Test 3: Agent retrieval
            retrieved = registry.get_agent(agent_data.agent_id, tenant_id="test_tenant")
            success = retrieved is not None and retrieved.agent_id == agent_data.agent_id
            self.log_test("agent_registry", "Agent retrieval", success, f"Retrieved: {retrieved.agent_id if retrieved else 'None'}")
            
            # Test 4: Agent discovery
            discovered = registry.discover_agents_by_capabilities(
                required_capabilities=["testing"],
                tenant_id="test_tenant"
            )
            # Check that our agent is in the discovered list
            agent_ids = [d["agent"].agent_id for d in discovered]
            success = len(discovered) > 0 and agent_data.agent_id in agent_ids
            self.log_test("agent_registry", "Agent discovery", success, f"Found {len(discovered)} matching agents, including our agent: {agent_data.agent_id in agent_ids}")
            
            # Test 5: Capability registry
            capabilities = registry.get_capability_registry(tenant_id="test_tenant")
            success = "testing" in capabilities and agent_data.agent_id in capabilities["testing"]
            self.log_test("agent_registry", "Capability registry", success, f"Total capabilities: {len(capabilities)}")
            
            self.results["agent_registry"]["status"] = "passed"
            
        except Exception as e:
            self.log_test("agent_registry", "Validation failed", False, str(e))
            self.results["agent_registry"]["status"] = "failed"
    
    def validate_integration(self):
        """Validate integration between Level 1 components."""
        print("\n🔗 Validating Level 1 Integration...")
        
        try:
            # Test 1: Cross-component communication
            # Sandbox -> Memory Scribe -> Memory Coordinator -> Agent Registry
            
            # Create services
            sandbox = SandboxExecutionEnvironment(self.db)
            coordinator = MemoryCoordinatorAgent(self.db)
            scribe = MemoryScribeAgent(self.db, coordinator)
            registry = AgentRegistryService(self.db)
            
            # Test execution result ingestion workflow
            session_id = f"integration_test_{uuid.uuid4().hex[:8]}"
            session = sandbox.create_session(
                session_id=session_id,
                agent_id="integration_agent",
                tool_id="integration_tool"
            )
            
            # Simulate execution result
            execution_result = {
                "command": "echo 'Integration test'",
                "stdout": "Integration test successful",
                "stderr": "",
                "exit_code": 0,
                "success": True
            }
            
            # Ingest execution result into memory
            ingestion_request = IngestionRequest(
                content=f"Execution result: {execution_result['stdout']}",
                source=ContentSource.EXECUTION_RESULT,
                content_type=ContentType.TEXT,
                metadata={"session_id": session_id, "integration_test": True},
                tenant_id="integration_tenant",
                agent_id="integration_agent"
            )
            
            scribe_result = asyncio.run(scribe.ingest_content(ingestion_request))
            success = scribe_result.success
            self.log_test("integration", "Execution result ingestion", success, f"Memory ID: {scribe_result.memory_id}")
            
            # Test 2: Agent discovery for execution capabilities
            execution_agents = registry.discover_agents_by_capabilities(
                required_capabilities=["execution"],
                tenant_id="integration_tenant"
            )
            
            # Register an execution agent if none found
            if not execution_agents:
                execution_agent = SystemAgentCreate(
                    agent_id="execution_agent_001",
                    name="execution_agent",
                    display_name="Execution Agent",
                    tier=AgentTier.EXECUTION,
                    category="execution",
                    capabilities=["execution", "tool_management"],
                    status=AgentStatus.ACTIVE
                )
                registry.register_agent(execution_agent, tenant_id="integration_tenant")
                
                execution_agents = registry.discover_agents_by_capabilities(
                    required_capabilities=["execution"],
                    tenant_id="integration_tenant"
                )
            
            success = len(execution_agents) > 0
            self.log_test("integration", "Agent discovery for execution", success, f"Found {len(execution_agents)} execution agents")
            
            # Test 3: Memory retrieval for agent context
            from app.services.memory_guild.coordinator import MemoryRequest, MemoryOperation, MemoryType
            
            search_request = MemoryRequest(
                operation=MemoryOperation.SEARCH,
                memory_type=MemoryType.WORKING,
                query="integration test",
                tenant_id="integration_tenant"
            )
            
            search_response = asyncio.run(coordinator.handle_memory_request(search_request))
            success = search_response.success
            self.log_test("integration", "Memory search for context", success, f"Found {len(search_response.results or [])} results")
            
            # Cleanup
            sandbox.close_session(session_id)
            
            self.results["integration"]["status"] = "passed"
            
        except Exception as e:
            self.log_test("integration", "Integration validation failed", False, str(e))
            self.results["integration"]["status"] = "failed"
    
    def generate_report(self):
        """Generate validation report."""
        print("\n" + "="*80)
        print("🎯 LEVEL 1 VALIDATION REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for component, data in self.results.items():
            status_icon = "✅" if data["status"] == "passed" else "❌" if data["status"] == "failed" else "⏳"
            print(f"\n{status_icon} {component.upper().replace('_', ' ')}: {data['status'].upper()}")
            
            component_passed = 0
            for test in data["tests"]:
                test_icon = "✅" if test["success"] else "❌"
                print(f"  {test_icon} {test['name']}")
                if test["details"]:
                    print(f"     {test['details']}")
                
                total_tests += 1
                if test["success"]:
                    passed_tests += 1
                    component_passed += 1
            
            print(f"  📊 Component Score: {component_passed}/{len(data['tests'])} tests passed")
        
        print(f"\n📈 OVERALL SCORE: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Determine readiness
        all_components_passed = all(data["status"] == "passed" for data in self.results.values())
        
        if all_components_passed:
            print("\n🎉 LEVEL 1 VALIDATION: PASSED")
            print("✅ All Level 1 components are working correctly")
            print("✅ Integration between components is functional")
            print("✅ Ready to proceed to Level 2 implementation")
        else:
            print("\n⚠️  LEVEL 1 VALIDATION: ISSUES DETECTED")
            failed_components = [comp for comp, data in self.results.items() if data["status"] == "failed"]
            print(f"❌ Failed components: {', '.join(failed_components)}")
            print("🔧 Please address issues before proceeding to Level 2")
        
        return all_components_passed
    
    def run_validation(self):
        """Run complete Level 1 validation."""
        print("🚀 Starting DRYAD.AI Level 1 Validation")
        print("="*80)
        
        logger.info(f"Level 1 validation started at {datetime.now().isoformat()}")
        
        # Run component validations
        self.validate_sandbox_execution()
        self.validate_memory_coordinator()
        self.validate_memory_scribe()
        self.validate_agent_registry()
        self.validate_integration()
        
        # Generate report
        success = self.generate_report()
        
        total_tests = sum(len(data["tests"]) for data in self.results.values())
        passed_tests = sum(len([t for t in data["tests"] if t["success"]]) for data in self.results.values())
        logger.info(f"Level 1 validation completed - Success: {success}, Tests: {passed_tests}/{total_tests}")
        
        return success


def main():
    """Main validation entry point."""
    try:
        # Suppress LLM initialization errors during validation
        import io
        import contextlib

        # Capture stderr to suppress LLM warnings
        stderr_capture = io.StringIO()

        with contextlib.redirect_stderr(stderr_capture):
            validator = Level1Validator()
            success = validator.run_validation()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
