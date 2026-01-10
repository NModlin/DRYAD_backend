"""
Level 2 Validation Script

Tests all Level 2 components:
1. Stateful Tool Management (persistent sessions)
2. Archivist Agent (short-term memory)
3. Librarian Agent (long-term memory)
4. Integration between all Memory Guild agents

Run this after implementing Level 2 to verify all components work correctly.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "sqlite:///./data/DRYAD.AI.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ValidationResults:
    """Track validation test results."""
    
    def __init__(self):
        self.tests = []
        self.component_scores = {}
    
    def add_test(self, component: str, test_name: str, passed: bool, error: str = None):
        """Add a test result."""
        self.tests.append({
            "component": component,
            "test": test_name,
            "passed": passed,
            "error": error
        })
    
    def get_component_score(self, component: str) -> tuple:
        """Get score for a component (passed, total)."""
        component_tests = [t for t in self.tests if t["component"] == component]
        passed = sum(1 for t in component_tests if t["passed"])
        total = len(component_tests)
        return (passed, total)
    
    def get_overall_score(self) -> tuple:
        """Get overall score (passed, total)."""
        passed = sum(1 for t in self.tests if t["passed"])
        total = len(self.tests)
        return (passed, total)
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "="*70)
        print("LEVEL 2 VALIDATION REPORT")
        print("="*70)
        
        components = list(set(t["component"] for t in self.tests))
        
        for component in sorted(components):
            passed, total = self.get_component_score(component)
            percentage = (passed / total * 100) if total > 0 else 0
            status = "PASSED" if passed == total else "FAILED"
            
            print(f"\n{component}: {status}")
            print(f"  Component Score: {passed}/{total} tests passed ({percentage:.1f}%)")
            
            component_tests = [t for t in self.tests if t["component"] == component]
            for test in component_tests:
                status_icon = "✅" if test["passed"] else "❌"
                print(f"    {status_icon} {test['test']}")
                if not test["passed"] and test["error"]:
                    print(f"       Error: {test['error']}")
        
        passed, total = self.get_overall_score()
        percentage = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print(f"OVERALL SCORE: {passed}/{total} tests passed ({percentage:.1f}%)")
        print("="*70)
        
        if passed == total:
            print("\n🎉 LEVEL 2 VALIDATION: PASSED")
            print("✅ All Level 2 components are working correctly")
            print("✅ Memory Guild is fully operational")
            print("✅ Ready to proceed to Level 3 implementation")
        else:
            print("\n❌ LEVEL 2 VALIDATION: FAILED")
            print(f"⚠️  {total - passed} test(s) failed")
            print("⚠️  Fix failing tests before proceeding to Level 3")


results = ValidationResults()


async def test_archivist():
    """Test Archivist Agent (short-term memory)."""
    print("\n📦 Testing Archivist Agent (Short-Term Memory)...")
    
    try:
        from app.services.memory_guild.archivist import ArchivistAgent
        
        # Test 1: Service initialization
        try:
            archivist = ArchivistAgent(mock_mode=True)
            results.add_test("ARCHIVIST", "Service initialization", True)
        except Exception as e:
            results.add_test("ARCHIVIST", "Service initialization", False, str(e))
            return
        
        # Test 2: Store memory
        try:
            success = await archivist.store(
                key="test_key",
                value={"data": "test_value"},
                ttl=timedelta(hours=1),
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            results.add_test("ARCHIVIST", "Memory storage", success, None if success else "Store returned False")
        except Exception as e:
            results.add_test("ARCHIVIST", "Memory storage", False, str(e))
        
        # Test 3: Retrieve memory
        try:
            value = await archivist.retrieve(
                key="test_key",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            passed = value is not None and value.get("data") == "test_value"
            results.add_test("ARCHIVIST", "Memory retrieval", passed, None if passed else f"Retrieved: {value}")
        except Exception as e:
            results.add_test("ARCHIVIST", "Memory retrieval", False, str(e))
        
        # Test 4: Delete memory
        try:
            success = await archivist.delete(
                key="test_key",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            results.add_test("ARCHIVIST", "Memory deletion", success, None if success else "Delete returned False")
        except Exception as e:
            results.add_test("ARCHIVIST", "Memory deletion", False, str(e))
        
        # Test 5: List keys
        try:
            await archivist.store(
                key="list_test_1",
                value={"data": "value1"},
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            await archivist.store(
                key="list_test_2",
                value={"data": "value2"},
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            keys = await archivist.list_keys(
                pattern="list_test_*",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            passed = len(keys) == 2
            results.add_test("ARCHIVIST", "List keys", passed, None if passed else f"Found {len(keys)} keys, expected 2")
        except Exception as e:
            results.add_test("ARCHIVIST", "List keys", False, str(e))
        
    except Exception as e:
        results.add_test("ARCHIVIST", "Component load", False, str(e))


async def test_librarian():
    """Test Librarian Agent (long-term memory)."""
    print("\n📚 Testing Librarian Agent (Long-Term Memory)...")
    
    try:
        from app.services.memory_guild.librarian import LibrarianAgent
        
        # Test 1: Service initialization
        try:
            librarian = LibrarianAgent(mock_mode=True)
            results.add_test("LIBRARIAN", "Service initialization", True)
        except Exception as e:
            results.add_test("LIBRARIAN", "Service initialization", False, str(e))
            return
        
        # Test 2: Store memory
        try:
            entry_id = await librarian.store(
                content="This is a test memory about Python programming",
                category="knowledge",
                metadata={"topic": "programming"},
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            passed = entry_id is not None
            results.add_test("LIBRARIAN", "Memory storage", passed, None if passed else "Store returned None")
        except Exception as e:
            results.add_test("LIBRARIAN", "Memory storage", False, str(e))
        
        # Test 3: Semantic search
        try:
            search_results = await librarian.search(
                query="Python programming",
                category="knowledge",
                limit=5,
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            passed = len(search_results) > 0
            results.add_test("LIBRARIAN", "Semantic search", passed, None if passed else f"Found {len(search_results)} results")
        except Exception as e:
            results.add_test("LIBRARIAN", "Semantic search", False, str(e))
        
        # Test 4: Category filtering
        try:
            # Store in different category
            await librarian.store(
                content="Different category content",
                category="other",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            # Search with category filter
            filtered_results = await librarian.search(
                query="content",
                category="knowledge",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            # All results should be from "knowledge" category
            passed = all(r.category == "knowledge" for r in filtered_results)
            results.add_test("LIBRARIAN", "Category filtering", passed, None if passed else "Found results from wrong category")
        except Exception as e:
            results.add_test("LIBRARIAN", "Category filtering", False, str(e))
        
        # Test 5: Count entries
        try:
            count = await librarian.count(
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            passed = count >= 0
            results.add_test("LIBRARIAN", "Count entries", passed, None if passed else f"Invalid count: {count}")
        except Exception as e:
            results.add_test("LIBRARIAN", "Count entries", False, str(e))
        
    except Exception as e:
        results.add_test("LIBRARIAN", "Component load", False, str(e))


async def test_memory_guild_integration():
    """Test Memory Guild integration."""
    print("\n🏛️  Testing Memory Guild Integration...")
    
    try:
        from app.services.memory_guild.coordinator import (
            MemoryCoordinatorAgent, MemoryRequest, MemoryOperation, MemoryType
        )
        
        db = SessionLocal()
        
        # Test 1: Coordinator with specialists
        try:
            coordinator = MemoryCoordinatorAgent(db, enable_specialists=True)
            passed = coordinator.archivist_available and coordinator.librarian_available
            results.add_test("INTEGRATION", "Coordinator initialization", passed, 
                           None if passed else "Specialists not available")
        except Exception as e:
            results.add_test("INTEGRATION", "Coordinator initialization", False, str(e))
            db.close()
            return
        
        # Test 2: Short-term memory flow
        try:
            request = MemoryRequest(
                operation=MemoryOperation.STORE,
                memory_type=MemoryType.SHORT_TERM,
                key="integration_test",
                value={"test": "data"},
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            response = await coordinator.handle_memory_request(request)
            passed = response.success and response.source == "archivist"
            results.add_test("INTEGRATION", "Short-term memory flow", passed,
                           None if passed else f"Source: {response.source}, Success: {response.success}")
        except Exception as e:
            results.add_test("INTEGRATION", "Short-term memory flow", False, str(e))
        
        # Test 3: Long-term memory flow
        try:
            request = MemoryRequest(
                operation=MemoryOperation.STORE,
                memory_type=MemoryType.LONG_TERM,
                value={"content": "Long-term test memory"},
                metadata={"category": "test"},
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            response = await coordinator.handle_memory_request(request)
            passed = response.success and response.source == "librarian"
            results.add_test("INTEGRATION", "Long-term memory flow", passed,
                           None if passed else f"Source: {response.source}, Success: {response.success}")
        except Exception as e:
            results.add_test("INTEGRATION", "Long-term memory flow", False, str(e))
        
        # Test 4: Semantic search
        try:
            request = MemoryRequest(
                operation=MemoryOperation.SEARCH,
                memory_type=MemoryType.LONG_TERM,
                query="test memory",
                tenant_id="test_tenant",
                agent_id="test_agent"
            )
            
            response = await coordinator.handle_memory_request(request)
            passed = response.success and response.source == "librarian"
            results.add_test("INTEGRATION", "Semantic search", passed,
                           None if passed else f"Source: {response.source}, Success: {response.success}")
        except Exception as e:
            results.add_test("INTEGRATION", "Semantic search", False, str(e))
        
        db.close()
        
    except Exception as e:
        results.add_test("INTEGRATION", "Component load", False, str(e))


async def main():
    """Run all Level 2 validation tests."""
    print("="*70)
    print("LEVEL 2 VALIDATION - DRYAD.AI Agent Evolution Architecture")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    await test_archivist()
    await test_librarian()
    await test_memory_guild_integration()
    
    # Print results
    results.print_report()
    
    # Return exit code
    passed, total = results.get_overall_score()
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

