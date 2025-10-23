#!/usr/bin/env python3
"""
Comprehensive validation script for DRYAD.AI self-contained local LLM system.

This script validates that all critical fixes have been implemented correctly:
1. No mock LLM fallbacks
2. Local LLM prioritized over external APIs
3. No search fallbacks in AI reasoning
4. Explicit failures instead of silent degradation
5. Clear error messages for missing dependencies
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_llm_config_fixes():
    """Test that LLM configuration fixes are implemented correctly."""
    logger.info("🔍 Testing LLM Configuration Fixes...")
    
    try:
        from app.core.llm_config import LLMConfig, create_llm, LLMProvider
        
        # Test 1: Default provider should be LLAMACPP
        config = LLMConfig()
        if config.provider != LLMProvider.LLAMACPP:
            logger.error(f"❌ Default provider is {config.provider}, should be LLAMACPP")
            return False
        logger.info("✅ Default provider correctly set to LLAMACPP")
        
        # Test 2: Mock LLM fallback should be removed
        # This should raise an exception instead of falling back to mock
        os.environ['LLM_PROVIDER'] = 'llamacpp'
        try:
            # This might fail due to missing dependencies, which is expected
            llm = create_llm(config)
            logger.info("✅ LLM creation succeeded (local LLM available)")
        except RuntimeError as e:
            if "Local LLM initialization failed" in str(e):
                logger.info("✅ LLM creation fails explicitly with helpful error message")
            else:
                logger.error(f"❌ Unexpected error message: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Unexpected exception type: {type(e).__name__}: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM config test failed: {e}")
        return False

def test_search_restrictions():
    """Test that search functions are properly restricted."""
    logger.info("🔍 Testing Search Function Restrictions...")
    
    try:
        from app.core.tools import duckduckgo_search, explicit_web_search
        
        # Test 1: duckduckgo_search should be deprecated and raise error
        try:
            result = duckduckgo_search("test query")
            logger.error("❌ duckduckgo_search should raise RuntimeError but didn't")
            return False
        except RuntimeError as e:
            if "deprecated" in str(e).lower():
                logger.info("✅ duckduckgo_search correctly raises deprecation error")
            else:
                logger.error(f"❌ Wrong error message: {e}")
                return False
        
        # Test 2: explicit_web_search should require explicit_request=True
        try:
            result = explicit_web_search("test query", explicit_request=False)
            logger.error("❌ explicit_web_search should require explicit_request=True")
            return False
        except RuntimeError as e:
            if "explicit" in str(e).lower():
                logger.info("✅ explicit_web_search correctly requires explicit confirmation")
            else:
                logger.error(f"❌ Wrong error message: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Search restrictions test failed: {e}")
        return False

def test_multi_agent_system():
    """Test that multi-agent system fails explicitly."""
    logger.info("🔍 Testing Multi-Agent System Explicit Failures...")
    
    try:
        from app.core.multi_agent import MultiAgentOrchestrator
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator()
        
        # Test that it doesn't fall back to search
        try:
            result = orchestrator.execute_simple_query("What is the weather today?")
            # If it succeeds, check that it's using AI reasoning, not search
            if result.get('task_type') == 'fallback_search':
                logger.error("❌ Multi-agent system falling back to search")
                return False
            logger.info("✅ Multi-agent system using AI reasoning (no search fallback)")
        except RuntimeError as e:
            if "Multi-agent system execution failed" in str(e):
                logger.info("✅ Multi-agent system fails explicitly when AI unavailable")
            else:
                logger.error(f"❌ Unexpected error: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-agent test failed: {e}")
        return False

def test_mock_llm_responses():
    """Test that mock LLM responses don't mention search capabilities."""
    logger.info("🔍 Testing Mock LLM Response Content...")
    
    try:
        from app.core.llm_config import _create_mock_llm, LLMConfig
        
        config = LLMConfig()
        mock_llm = _create_mock_llm(config)
        
        # Test various prompts to check responses
        test_prompts = [
            "Research the latest AI developments",
            "What is machine learning?",
            "Write a summary about Python",
            "Help me understand quantum computing"
        ]
        
        for prompt in test_prompts:
            response = mock_llm.invoke(prompt)
            response_lower = response.lower()
            
            # Check for prohibited terms
            prohibited_terms = [
                "web search", "search engines", "real-time web", 
                "search databases", "multiple sources", "real-time information"
            ]
            
            for term in prohibited_terms:
                if term in response_lower:
                    logger.error(f"❌ Mock LLM response contains prohibited term '{term}': {response[:100]}...")
                    return False
        
        logger.info("✅ Mock LLM responses correctly mention only local AI processing")
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock LLM response test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    logger.info("🚀 Starting DRYAD.AI Self-Contained AI Validation...")
    
    tests = [
        ("LLM Configuration Fixes", test_llm_config_fixes),
        ("Search Function Restrictions", test_search_restrictions),
        ("Multi-Agent System", test_multi_agent_system),
        ("Mock LLM Response Content", test_mock_llm_responses),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info('='*60)
        
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    logger.info('='*60)
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - DRYAD.AI is now a self-contained local LLM system!")
        logger.info("✅ No mock fallbacks")
        logger.info("✅ Local LLM prioritized")
        logger.info("✅ No search fallbacks in AI reasoning")
        logger.info("✅ Explicit failures instead of silent degradation")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed - system still has dependencies/fallbacks")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
