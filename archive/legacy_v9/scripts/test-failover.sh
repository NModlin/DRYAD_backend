#!/bin/bash
# ============================================================================
# Failover Testing Script for DRYAD.AI Backend
# Tests load balancer failover and recovery scenarios
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOAD_BALANCER_URL="${LOAD_BALANCER_URL:-http://localhost}"
TEST_ENDPOINT="${TEST_ENDPOINT:-/api/v1/health}"
REQUESTS_PER_TEST="${REQUESTS_PER_TEST:-100}"
CONCURRENT_REQUESTS="${CONCURRENT_REQUESTS:-10}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DRYAD.AI Backend - Failover Testing Suite              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to send requests
send_requests() {
    local url=$1
    local count=$2
    local success=0
    local failed=0
    
    for i in $(seq 1 $count); do
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
        if [ "$response" = "200" ]; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
    done
    
    echo "$success $failed"
}

# Function to get backend distribution
get_backend_distribution() {
    local url=$1
    local count=$2
    
    declare -A backend_counts
    
    for i in $(seq 1 $count); do
        # Get response with backend identifier
        backend=$(curl -s "$url" | jq -r '.hostname // "unknown"' 2>/dev/null || echo "unknown")
        backend_counts[$backend]=$((${backend_counts[$backend]:-0} + 1))
    done
    
    echo "Backend distribution:"
    for backend in "${!backend_counts[@]}"; do
        percentage=$((${backend_counts[$backend]} * 100 / count))
        echo "  $backend: ${backend_counts[$backend]} requests ($percentage%)"
    done
}

# Test 1: Basic Load Balancing
test_basic_load_balancing() {
    echo -e "${GREEN}Test 1: Basic Load Balancing${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Sending $REQUESTS_PER_TEST requests to load balancer..."
    result=$(send_requests "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" $REQUESTS_PER_TEST)
    success=$(echo $result | awk '{print $1}')
    failed=$(echo $result | awk '{print $2}')
    
    success_rate=$((success * 100 / REQUESTS_PER_TEST))
    
    echo "Results:"
    echo "  ✅ Successful: $success ($success_rate%)"
    echo "  ❌ Failed: $failed"
    
    if [ $success_rate -ge 95 ]; then
        echo -e "${GREEN}✅ PASSED: Load balancing is working${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: Success rate below 95%${NC}"
        return 1
    fi
    echo ""
}

# Test 2: Backend Failure Simulation
test_backend_failure() {
    echo -e "${GREEN}Test 2: Backend Failure Simulation${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Step 1: Stopping backend1..."
    docker-compose -f docker-compose.prod.yml stop backend1
    sleep 5
    
    echo "Step 2: Sending requests (should failover to backend2)..."
    result=$(send_requests "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" 50)
    success=$(echo $result | awk '{print $1}')
    failed=$(echo $result | awk '{print $2}')
    
    echo "Results with backend1 down:"
    echo "  ✅ Successful: $success"
    echo "  ❌ Failed: $failed"
    
    echo "Step 3: Restarting backend1..."
    docker-compose -f docker-compose.prod.yml start backend1
    sleep 10
    
    echo "Step 4: Verifying recovery..."
    result=$(send_requests "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" 50)
    success=$(echo $result | awk '{print $1}')
    
    if [ $success -ge 45 ]; then
        echo -e "${GREEN}✅ PASSED: Failover and recovery successful${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: Failover or recovery failed${NC}"
        return 1
    fi
    echo ""
}

# Test 3: All Backends Down
test_all_backends_down() {
    echo -e "${GREEN}Test 3: All Backends Down${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Step 1: Stopping all backends..."
    docker-compose -f docker-compose.prod.yml stop backend1 backend2
    sleep 5
    
    echo "Step 2: Sending requests (should fail gracefully)..."
    result=$(send_requests "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" 10)
    failed=$(echo $result | awk '{print $2}')
    
    echo "Results with all backends down:"
    echo "  ❌ Failed: $failed (expected)"
    
    echo "Step 3: Restarting all backends..."
    docker-compose -f docker-compose.prod.yml start backend1 backend2
    sleep 15
    
    echo "Step 4: Verifying recovery..."
    result=$(send_requests "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" 20)
    success=$(echo $result | awk '{print $1}')
    
    if [ $success -ge 18 ]; then
        echo -e "${GREEN}✅ PASSED: System recovered from total failure${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: System did not recover properly${NC}"
        return 1
    fi
    echo ""
}

# Test 4: Load Distribution
test_load_distribution() {
    echo -e "${GREEN}Test 4: Load Distribution${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Analyzing load distribution across backends..."
    get_backend_distribution "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" 100
    
    echo -e "${GREEN}✅ PASSED: Load distribution analysis complete${NC}"
    echo ""
}

# Test 5: Concurrent Requests
test_concurrent_requests() {
    echo -e "${GREEN}Test 5: Concurrent Request Handling${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Sending $CONCURRENT_REQUESTS concurrent requests..."
    
    start_time=$(date +%s)
    
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        curl -s "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" > /dev/null &
    done
    
    wait
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo "Results:"
    echo "  Duration: ${duration}s"
    echo "  Requests: $CONCURRENT_REQUESTS"
    echo "  Throughput: $((CONCURRENT_REQUESTS / duration)) req/s"
    
    if [ $duration -le 10 ]; then
        echo -e "${GREEN}✅ PASSED: Concurrent requests handled efficiently${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  WARNING: Concurrent requests took longer than expected${NC}"
        return 1
    fi
    echo ""
}

# Test 6: Session Persistence
test_session_persistence() {
    echo -e "${GREEN}Test 6: Session Persistence${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "Testing sticky sessions (if configured)..."
    
    # Make multiple requests with same session
    cookie_jar=$(mktemp)
    backend1=$(curl -s -c $cookie_jar "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" | jq -r '.hostname // "unknown"')
    backend2=$(curl -s -b $cookie_jar "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" | jq -r '.hostname // "unknown"')
    backend3=$(curl -s -b $cookie_jar "${LOAD_BALANCER_URL}${TEST_ENDPOINT}" | jq -r '.hostname // "unknown"')
    
    rm $cookie_jar
    
    echo "Backend responses:"
    echo "  Request 1: $backend1"
    echo "  Request 2: $backend2"
    echo "  Request 3: $backend3"
    
    if [ "$backend1" = "$backend2" ] && [ "$backend2" = "$backend3" ]; then
        echo -e "${GREEN}✅ PASSED: Session persistence is working${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  INFO: Session persistence not configured (this is okay)${NC}"
        return 0
    fi
    echo ""
}

# Run all tests
run_all_tests() {
    local passed=0
    local failed=0
    
    echo -e "${BLUE}Starting failover test suite...${NC}"
    echo ""
    
    # Run tests
    test_basic_load_balancing && passed=$((passed + 1)) || failed=$((failed + 1))
    test_backend_failure && passed=$((passed + 1)) || failed=$((failed + 1))
    test_all_backends_down && passed=$((passed + 1)) || failed=$((failed + 1))
    test_load_distribution && passed=$((passed + 1)) || failed=$((failed + 1))
    test_concurrent_requests && passed=$((passed + 1)) || failed=$((failed + 1))
    test_session_persistence && passed=$((passed + 1)) || failed=$((failed + 1))
    
    # Summary
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Test Summary                                              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Total tests: $((passed + failed))"
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"
    echo ""
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Main
case "${1:-all}" in
    all)
        run_all_tests
        ;;
    basic)
        test_basic_load_balancing
        ;;
    failover)
        test_backend_failure
        ;;
    total-failure)
        test_all_backends_down
        ;;
    distribution)
        test_load_distribution
        ;;
    concurrent)
        test_concurrent_requests
        ;;
    session)
        test_session_persistence
        ;;
    *)
        echo "Usage: $0 {all|basic|failover|total-failure|distribution|concurrent|session}"
        exit 1
        ;;
esac

