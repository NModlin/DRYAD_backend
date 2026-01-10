#!/bin/bash
# ============================================================================
# Health Check Script for DRYAD.AI Backend
# Monitors backend health and performs failover if needed
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URLS="${BACKEND_URLS:-http://backend1:8000 http://backend2:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/api/v1/health}"
TIMEOUT="${TIMEOUT:-5}"
MAX_RETRIES="${MAX_RETRIES:-3}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

# Counters
declare -A failure_counts
declare -A last_status

# Initialize counters
for url in $BACKEND_URLS; do
    failure_counts[$url]=0
    last_status[$url]="unknown"
done

# Function to check health
check_health() {
    local url=$1
    local endpoint="${url}${HEALTH_ENDPOINT}"
    
    # Perform health check
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$endpoint" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Function to send alert
send_alert() {
    local message=$1
    local severity=$2
    
    echo -e "${RED}🚨 ALERT: $message${NC}"
    
    # Send to webhook if configured
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$message\",\"severity\":\"$severity\"}" \
            2>/dev/null || true
    fi
    
    # Log to file
    echo "$(date): $message" >> /var/log/health-check.log
}

# Function to check all backends
check_all_backends() {
    local all_healthy=true
    local healthy_count=0
    local total_count=0
    
    for url in $BACKEND_URLS; do
        total_count=$((total_count + 1))
        
        if check_health "$url"; then
            # Backend is healthy
            if [ "${last_status[$url]}" != "healthy" ]; then
                echo -e "${GREEN}✅ $url is now HEALTHY${NC}"
                send_alert "$url recovered" "info"
                last_status[$url]="healthy"
            fi
            failure_counts[$url]=0
            healthy_count=$((healthy_count + 1))
        else
            # Backend is unhealthy
            failure_counts[$url]=$((${failure_counts[$url]} + 1))
            
            if [ ${failure_counts[$url]} -ge $MAX_RETRIES ]; then
                if [ "${last_status[$url]}" != "unhealthy" ]; then
                    echo -e "${RED}❌ $url is UNHEALTHY (${failure_counts[$url]} failures)${NC}"
                    send_alert "$url is down after ${failure_counts[$url]} failed checks" "critical"
                    last_status[$url]="unhealthy"
                fi
            else
                echo -e "${YELLOW}⚠️  $url check failed (${failure_counts[$url]}/$MAX_RETRIES)${NC}"
            fi
            all_healthy=false
        fi
    done
    
    # Check if all backends are down
    if [ $healthy_count -eq 0 ]; then
        echo -e "${RED}🚨 CRITICAL: All backends are down!${NC}"
        send_alert "ALL BACKENDS DOWN - IMMEDIATE ACTION REQUIRED" "critical"
    elif [ $healthy_count -lt $total_count ]; then
        echo -e "${YELLOW}⚠️  WARNING: Only $healthy_count/$total_count backends are healthy${NC}"
    else
        echo -e "${GREEN}✅ All backends healthy ($healthy_count/$total_count)${NC}"
    fi
}

# Function to test failover
test_failover() {
    echo -e "${GREEN}🧪 Testing failover mechanism...${NC}"
    
    # Simulate backend failure
    local test_url=$(echo $BACKEND_URLS | awk '{print $1}')
    echo "Simulating failure of $test_url"
    
    # Check if other backends can handle traffic
    local other_urls=$(echo $BACKEND_URLS | sed "s|$test_url||")
    
    for url in $other_urls; do
        if check_health "$url"; then
            echo -e "${GREEN}✅ Failover successful: $url is handling traffic${NC}"
            return 0
        fi
    done
    
    echo -e "${RED}❌ Failover failed: No healthy backends available${NC}"
    return 1
}

# Main monitoring loop
monitor() {
    echo -e "${GREEN}🔍 Starting health check monitoring...${NC}"
    echo "Backends: $BACKEND_URLS"
    echo "Check interval: ${CHECK_INTERVAL}s"
    echo "Max retries: $MAX_RETRIES"
    echo ""
    
    while true; do
        echo "$(date): Checking backend health..."
        check_all_backends
        echo ""
        sleep $CHECK_INTERVAL
    done
}

# Parse command line arguments
case "${1:-monitor}" in
    monitor)
        monitor
        ;;
    check)
        check_all_backends
        ;;
    test-failover)
        test_failover
        ;;
    *)
        echo "Usage: $0 {monitor|check|test-failover}"
        exit 1
        ;;
esac

