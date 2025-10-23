#!/usr/bin/env python3
"""
REAL verification that AI is actually working.
This will write results to a file so we can see them.
"""

import sys
import os
import traceback
sys.path.insert(0, '.')

def write_result(message):
    """Write result to file and print."""
    print(message)
    with open('ai_verification_results.txt', 'a') as f:
        f.write(message + '\n')

def main():
    # Clear previous results
    with open('ai_verification_results.txt', 'w') as f:
        f.write('=== AI VERIFICATION TEST ===\n')
    
    write_result('=== AI VERIFICATION TEST ===')
    
    # Test 1: Check model file
    write_result('\n1. Checking model file...')
    model_path = 'models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024*1024)
        write_result(f'   ✓ Model file exists: {size_mb:.1f} MB')
    else:
        write_result('   ✗ Model file NOT FOUND')
        return False
    
    # Test 2: Check llama-cpp-python
    write_result('\n2. Testing llama-cpp-python import...')
    try:
        from llama_cpp import Llama
        write_result('   ✓ llama-cpp-python imported successfully')
    except ImportError as e:
        write_result(f'   ✗ llama-cpp-python import failed: {e}')
        return False
    
    # Test 3: Create LLM instance
    write_result('\n3. Creating LLM instance...')
    try:
        from langchain_community.llms import LlamaCpp
        
        llm = LlamaCpp(
            model_path=model_path,
            temperature=0.1,
            max_tokens=100,
            n_ctx=1024,
            n_threads=2,
            verbose=False,
            n_gpu_layers=0,
            use_mlock=False,
            use_mmap=True,
        )
        write_result('   ✓ LlamaCpp instance created successfully')
    except Exception as e:
        write_result(f'   ✗ LlamaCpp creation failed: {e}')
        traceback.print_exc()
        return False
    
    # Test 4: ACTUAL AI INFERENCE
    write_result('\n4. Testing ACTUAL AI inference...')
    try:
        test_prompt = "What is 2+2? Answer briefly."
        write_result(f'   Prompt: "{test_prompt}"')
        write_result('   Generating response...')
        
        response = llm.invoke(test_prompt)
        
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
        
        write_result(f'   AI Response: "{result.strip()}"')
        
        if result and len(result.strip()) > 0:
            write_result('   ✓ AI INFERENCE WORKING!')
            return True
        else:
            write_result('   ✗ AI returned empty response')
            return False
            
    except Exception as e:
        write_result(f'   ✗ AI inference failed: {e}')
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            write_result('\n=== FINAL RESULT: AI IS WORKING! ===')
        else:
            write_result('\n=== FINAL RESULT: AI IS NOT WORKING ===')
        sys.exit(0 if success else 1)
    except Exception as e:
        write_result(f'\nCRITICAL ERROR: {e}')
        traceback.print_exc()
        sys.exit(1)
