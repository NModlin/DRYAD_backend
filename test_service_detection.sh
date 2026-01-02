#!/bin/bash
# Test script for service detection functions

# Source the utilities
source lib/utils.sh

echo "========================================="
echo "Testing Service Detection Functions"
echo "========================================="
echo ""

# Test Redis detection
echo "Testing Redis Detection:"
echo "------------------------"
if is_redis_running; then
    echo "✓ Redis is running and accessible"
    if command_exists redis-cli; then
        echo "  - redis-cli version: $(redis-cli --version)"
        echo "  - Ping test: $(redis-cli ping 2>/dev/null || echo 'FAILED')"
    fi
else
    echo "✗ Redis is not running or not accessible"
fi
echo ""

# Test Ollama detection
echo "Testing Ollama Detection:"
echo "-------------------------"
if is_ollama_running; then
    echo "✓ Ollama is running and accessible"
    if command_exists ollama; then
        echo "  - Ollama version: $(ollama --version 2>/dev/null || echo 'unknown')"
        echo "  - Available models:"
        ollama list 2>/dev/null | head -5 || echo "    (unable to list models)"
    fi
else
    echo "✗ Ollama is not running or not accessible"
fi
echo ""

# Test port checking
echo "Testing Port Checks:"
echo "--------------------"
for port in 6379 11434 8000 8080; do
    if is_port_in_use "$port"; then
        service=$(get_service_on_port "$port")
        echo "✓ Port $port is in use by: ${service:-unknown}"
    else
        echo "✗ Port $port is available"
    fi
done
echo ""

# Test command existence
echo "Testing Command Availability:"
echo "-----------------------------"
for cmd in docker redis-cli ollama curl lsof netstat; do
    if command_exists "$cmd"; then
        echo "✓ $cmd is available"
    else
        echo "✗ $cmd is not available"
    fi
done
echo ""

echo "========================================="
echo "Test Complete"
echo "========================================="

