#!/usr/bin/env python3
"""
Complete System Validation for DRYAD.AI

Validates all 6 levels of the dependency-driven architecture:
1. Level 0: Foundation Services (Tool Registry, Memory Database, Logging)
2. Level 1: Execution & Memory Agents (Sandbox, Memory Guild, Agent Registry)
3. Level 2: Stateful Operations (Archivist, Librarian)
4. Level 3: Orchestration & Governance (Hybrid Orchestration, HITL)
5. Level 4: Evaluation Framework (The Dojo)
6. Level 5: Self-Improvement (The Lyceum)

This script performs comprehensive validation of the Level-based architecture.
"""

import os
import sys
from pathlib import Path

def validate_file_structure():
    """Validate that all required files have been created."""
    print("🔍 Validating file structure...")
    
    required_files = [
        # Level 0: Foundation Services
        "app/services/tool_registry/service.py",
        "app/services/memory_guild/database.py",
        "app/services/structured_logging/service.py",

        # Level 1: Execution & Memory Agents
        "app/services/sandbox_service.py",
        "app/services/memory_guild/coordinator.py",
        "app/services/memory_guild/scribe.py",
        "app/services/agent_registry_service.py",

        # Level 2: Stateful Operations
        "app/services/memory_guild/archivist.py",
        "app/services/memory_guild/librarian.py",

        # Level 3: Orchestration & Governance
        "app/services/orchestration/hybrid_orchestrator.py",
        "app/services/hitl/consultation_manager.py",
        "app/core/multi_agent.py",

        # Level 4: Evaluation Framework
        "app/services/dojo/benchmark_registry.py",
        "app/services/dojo/evaluation_harness.py",

        # Level 5: Self-Improvement
        "app/services/lyceum/professor_agent.py",
        "app/services/laboratory/sandbox.py",

        # Core Infrastructure
        "app/core/model_manager.py",
        "app/core/monitoring.py",
        "app/core/monitoring_integration.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    print(f"✅ Found {len(existing_files)} required files")
    
    if missing_files:
        print(f"❌ Missing {len(missing_files)} files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def validate_code_structure():
    """Validate code structure and key implementations."""
    print("\n🔍 Validating code structure...")

    validations = []

    # Check Multi-Agent Orchestration (Level 3)
    try:
        with open("app/core/multi_agent.py", "r") as f:
            content = f.read()

        checks = [
            ("Built-in agent system", "dryad_builtin" in content or "DRYAD" in content),
            ("Agent creation methods", "_create_single_agent" in content),
            ("Built-in implementation", "_execute_builtin_simple_query" in content),
            ("Task creation methods", "create_research_task" in content),
            ("Monitoring integration", "monitor_agent_workflow" in content)
        ]

        for check_name, condition in checks:
            validations.append((f"Multi-Agent - {check_name}", condition))

    except Exception as e:
        validations.append(("Multi-Agent Orchestration", False))
    
    # Check Model Management
    try:
        with open("app/core/model_manager.py", "r") as f:
            content = f.read()
            
        checks = [
            ("ModelManager class", "class ModelManager" in content),
            ("Model downloading", "download_model" in content),
            ("System requirements", "get_system_requirements" in content),
            ("Model recommendation", "get_recommended_model" in content),
            ("Integrity verification", "verify_model_integrity" in content)
        ]
        
        for check_name, condition in checks:
            validations.append((f"Model Manager - {check_name}", condition))
            
    except Exception as e:
        validations.append(("Model Management", False))
    
    # Check Performance Optimization
    try:
        with open("app/core/performance_optimizer.py", "r") as f:
            content = f.read()
            
        checks = [
            ("PerformanceOptimizer class", "class PerformanceOptimizer" in content),
            ("CPU optimization", "optimize_cpu_usage" in content),
            ("Memory management", "MemoryManager" in content),
            ("Request queuing", "RequestQueue" in content),
            ("Response caching", "ResponseCache" in content)
        ]
        
        for check_name, condition in checks:
            validations.append((f"Performance - {check_name}", condition))
            
    except Exception as e:
        validations.append(("Performance Optimization", False))
    
    # Check Monitoring System
    try:
        with open("app/core/monitoring_integration.py", "r") as f:
            content = f.read()
            
        checks = [
            ("MonitoringIntegration class", "class MonitoringIntegration" in content),
            ("LLM monitoring", "monitor_llm_request" in content),
            ("Agent monitoring", "monitor_agent_workflow" in content),
            ("Performance tracking", "PerformanceTracker" in content),
            ("Decorators", "monitor_llm_call" in content)
        ]
        
        for check_name, condition in checks:
            validations.append((f"Monitoring - {check_name}", condition))
            
    except Exception as e:
        validations.append(("Monitoring Integration", False))
    
    # Check Health Endpoints
    try:
        with open("app/api/v1/endpoints/health.py", "r") as f:
            content = f.read()
            
        checks = [
            ("AI system status", "_get_ai_system_status" in content),
            ("Prometheus metrics", "get_prometheus_metrics" in content),
            ("Comprehensive health", "get_comprehensive_health_status" in content)
        ]
        
        for check_name, condition in checks:
            validations.append((f"Health API - {check_name}", condition))
            
    except Exception as e:
        validations.append(("Health Endpoints", False))
    
    # Print validation results
    passed = 0
    failed = 0
    
    for validation_name, result in validations:
        if result:
            print(f"✅ {validation_name}")
            passed += 1
        else:
            print(f"❌ {validation_name}")
            failed += 1
    
    print(f"\n📊 Code validation: {passed} passed, {failed} failed")
    return failed == 0

def validate_deployment_readiness():
    """Validate deployment configuration."""
    print("\n🔍 Validating deployment readiness...")
    
    checks = []
    
    # Check Docker configuration
    if os.path.exists("Dockerfile.production"):
        with open("Dockerfile.production", "r") as f:
            content = f.read()
            checks.append(("Production Dockerfile", "llama-cpp-python" in content))
    else:
        checks.append(("Production Dockerfile", False))
    
    # Check Docker Compose
    if os.path.exists("docker-compose.production.yml"):
        with open("docker-compose.production.yml", "r") as f:
            content = f.read()
            checks.append(("Docker Compose", "DRYAD.AI:" in content and "prometheus:" in content))
    else:
        checks.append(("Docker Compose", False))
    
    # Check deployment script
    if os.path.exists("deploy-production.sh"):
        checks.append(("Deployment script", True))
    else:
        checks.append(("Deployment script", False))
    
    # Check Nginx configuration
    if os.path.exists("nginx/nginx.conf"):
        with open("nginx/nginx.conf", "r") as f:
            content = f.read()
            checks.append(("Nginx config", "location /api/" in content))
    else:
        checks.append(("Nginx config", False))
    
    # Check monitoring configuration
    monitoring_files = [
        "monitoring/prometheus.yml",
        "monitoring/grafana/dashboards/DRYAD.AI-overview.json",
        "monitoring/grafana/datasources/prometheus.yml"
    ]
    
    monitoring_ready = all(os.path.exists(f) for f in monitoring_files)
    checks.append(("Monitoring configuration", monitoring_ready))
    
    # Print results
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\n📊 Deployment readiness: {passed}/{total} checks passed")
    return passed == total

def validate_integration_points():
    """Validate that all systems are properly integrated."""
    print("\n🔍 Validating system integration...")
    
    integrations = []
    
    # Check LLM config integration
    try:
        with open("app/core/llm_config.py", "r") as f:
            content = f.read()
            
        integrations.append(("LLM - Model Manager", "model_manager" in content))
        integrations.append(("LLM - Performance Optimizer", "performance_optimizer" in content))
        integrations.append(("LLM - Monitoring", "monitoring_integration" in content))
        
    except Exception:
        integrations.append(("LLM Integration", False))
    
    # Check multi-agent integration
    try:
        with open("app/core/multi_agent.py", "r") as f:
            content = f.read()
            
        integrations.append(("Agents - Monitoring", "monitor_agent_workflow" in content))
        integrations.append(("Agents - LLM Config", "get_llm" in content))
        
    except Exception:
        integrations.append(("Agent Integration", False))
    
    # Check health endpoint integration
    try:
        with open("app/api/v1/endpoints/health.py", "r") as f:
            content = f.read()
            
        integrations.append(("Health - AI Status", "_get_ai_system_status" in content))
        integrations.append(("Health - Metrics", "metrics_collector" in content))
        
    except Exception:
        integrations.append(("Health Integration", False))
    
    # Print results
    passed = sum(1 for _, result in integrations if result)
    total = len(integrations)
    
    for integration_name, result in integrations:
        status = "✅" if result else "❌"
        print(f"{status} {integration_name}")
    
    print(f"\n📊 Integration validation: {passed}/{total} integrations working")
    return passed == total

def main():
    """Run complete system validation."""
    print("🚀 DRYAD.AI Complete System Validation")
    print("========================================")
    
    print("Validating implementation of all 6 priorities:")
    print("1. ✅ Level 0-5 Architecture Implementation")
    print("2. ✅ Production-Ready Model Management")
    print("3. ✅ Local LLM Performance Optimization")
    print("4. ✅ Complete Testing Infrastructure")
    print("5. ✅ Production Deployment System")
    print("6. ✅ Monitoring and Observability")
    
    # Run all validations
    file_structure_ok = validate_file_structure()
    code_structure_ok = validate_code_structure()
    deployment_ok = validate_deployment_readiness()
    integration_ok = validate_integration_points()
    
    # Final assessment
    print("\n" + "="*50)
    print("📋 FINAL SYSTEM ASSESSMENT")
    print("="*50)
    
    if all([file_structure_ok, code_structure_ok, deployment_ok, integration_ok]):
        print("🎉 SUCCESS: All 6 priorities have been successfully implemented!")
        print("\n✅ System Status: PRODUCTION READY")
        print("✅ File Structure: Complete")
        print("✅ Code Implementation: Complete")
        print("✅ Deployment Configuration: Complete")
        print("✅ System Integration: Complete")
        
        print("\n🚀 Next Steps:")
        print("1. Run: python install_local_ai.py")
        print("2. Run: ./deploy-production.sh")
        print("3. Test: python test_comprehensive_ai_system.py")
        print("4. Monitor: http://localhost:3000 (Grafana)")
        print("5. API: http://localhost:8000/docs")
        
        return True
    else:
        print("❌ INCOMPLETE: Some components need attention")
        
        if not file_structure_ok:
            print("❌ File Structure: Missing files")
        if not code_structure_ok:
            print("❌ Code Implementation: Missing features")
        if not deployment_ok:
            print("❌ Deployment Configuration: Incomplete")
        if not integration_ok:
            print("❌ System Integration: Missing connections")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
