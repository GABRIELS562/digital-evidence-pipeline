#!/bin/bash

# ================================================================================
# SRE HEALTH CHECK TESTING SCRIPT
# ================================================================================
# This script demonstrates how SRE health checks would be used in practice
# 
# SRE PRACTICES DEMONSTRATED:
# - Automated health validation
# - Different health check types for different use cases
# - Integration with monitoring and alerting systems
# - Debugging and troubleshooting workflows
# ================================================================================

set -e

echo "========================================"
echo "SRE HEALTH CHECK VALIDATION"
echo "========================================"
echo ""

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SRE PRACTICE: Function to check health endpoint and parse results
check_health_endpoint() {
    local check_type=$1
    local description=$2
    
    echo -e "${BLUE}Testing $description...${NC}"
    
    # In a real environment, this would be:
    # curl -s http://compliance-monitor:8000/health/$check_type
    
    # For demonstration, we'll use the Python script directly
    if [ -f "health_monitor.py" ]; then
        result=$(python3 health_monitor.py | grep -A 20 "=== $(echo $check_type | tr '[:lower:]' '[:upper:]') CHECK")
        
        if echo "$result" | grep -q '"status": "healthy"'; then
            echo -e "${GREEN}✓ $description: HEALTHY${NC}"
            return 0
        elif echo "$result" | grep -q '"status": "degraded"'; then
            echo -e "${YELLOW}⚠ $description: DEGRADED${NC}"
            return 1
        else
            echo -e "${RED}✗ $description: UNHEALTHY${NC}"
            return 2
        fi
    else
        echo -e "${YELLOW}⚠ Health monitor script not found${NC}"
        return 1
    fi
}

# SRE PRACTICE: Function to simulate real health check HTTP endpoints
simulate_health_endpoints() {
    echo "=== SIMULATING HEALTH CHECK ENDPOINTS ==="
    echo ""
    
    echo "# Kubernetes Liveness Probe"
    echo "curl -f http://compliance-monitor:8000/health/liveness"
    echo "Expected: HTTP 200 with basic service status"
    echo ""
    
    echo "# Kubernetes Readiness Probe" 
    echo "curl -f http://compliance-monitor:8000/health/readiness"
    echo "Expected: HTTP 200 when service can handle traffic"
    echo ""
    
    echo "# Load Balancer Health Check"
    echo "curl -f http://compliance-monitor:8000/health/ready"
    echo "Expected: HTTP 200 when service should receive traffic"
    echo ""
    
    echo "# Deep Health Check for Monitoring"
    echo "curl -s http://compliance-monitor:8000/health/deep | jq ."
    echo "Expected: Detailed JSON with all dependency statuses"
    echo ""
}

# SRE PRACTICE: Function to test different health check scenarios
test_health_scenarios() {
    echo "=== TESTING DIFFERENT HEALTH SCENARIOS ==="
    echo ""
    
    echo -e "${BLUE}1. Normal Operation (All systems healthy)${NC}"
    check_health_endpoint "liveness" "Service Liveness"
    check_health_endpoint "readiness" "Service Readiness" 
    check_health_endpoint "deep" "Deep Health Check"
    echo ""
    
    echo -e "${BLUE}2. Startup Scenario (Service initializing)${NC}"
    check_health_endpoint "startup" "Startup Health Check"
    echo ""
    
    echo -e "${BLUE}3. Degraded Operation (Non-critical dependency down)${NC}"
    echo "   Scenario: Grafana dashboard unavailable"
    echo "   Expected: Service still ready, but degraded status"
    echo ""
    
    echo -e "${BLUE}4. Critical Failure (Database unavailable)${NC}"
    echo "   Scenario: Database connection lost"
    echo "   Expected: Readiness check fails, liveness still passes"
    echo ""
}

# SRE PRACTICE: Function to demonstrate monitoring integration
demonstrate_monitoring_integration() {
    echo "=== SRE MONITORING INTEGRATION ==="
    echo ""
    
    echo "# Prometheus Health Check Metrics"
    echo "curl -s http://compliance-monitor:8000/metrics | grep health_check"
    echo ""
    
    echo "# Example Prometheus queries for health monitoring:"
    echo "up{job=\"compliance-service\"}                    # Service up/down"
    echo "health_check_duration_seconds                     # Health check latency"
    echo "health_check_status{type=\"readiness\"}          # Readiness status"
    echo "health_check_dependency_status                    # Dependency health"
    echo ""
    
    echo "# Grafana Dashboard Panels:"
    echo "- Service Availability (up metric)"
    echo "- Health Check Response Times"
    echo "- Dependency Status Matrix"
    echo "- Circuit Breaker States"
    echo ""
}

# SRE PRACTICE: Function to show troubleshooting workflow
demonstrate_troubleshooting_workflow() {
    echo "=== SRE TROUBLESHOOTING WORKFLOW ==="
    echo ""
    
    echo -e "${BLUE}When Health Check Fails:${NC}"
    echo ""
    
    echo "1. Check overall service status:"
    echo "   curl -s http://compliance-monitor:8000/health/deep | jq '.status'"
    echo ""
    
    echo "2. Identify specific failing dependencies:"
    echo "   curl -s http://compliance-monitor:8000/health/deep | jq '.details.dependencies'"
    echo ""
    
    echo "3. Check circuit breaker states:"
    echo "   curl -s http://compliance-monitor:8000/health/deep | jq '.details.circuit_breakers'"
    echo ""
    
    echo "4. Review resource utilization:"
    echo "   curl -s http://compliance-monitor:8000/health/deep | jq '.details.resources'"
    echo ""
    
    echo "5. Check application logs:"
    echo "   docker logs compliance-monitor --since=10m | grep -i error"
    echo ""
    
    echo "6. Verify infrastructure:"
    echo "   docker ps | grep compliance"
    echo "   docker stats compliance-monitor --no-stream"
    echo ""
}

# SRE PRACTICE: Function to show different operational use cases
demonstrate_operational_use_cases() {
    echo "=== SRE OPERATIONAL USE CASES ==="
    echo ""
    
    echo -e "${BLUE}Use Case 1: Kubernetes Deployment${NC}"
    echo "livenessProbe:"
    echo "  httpGet:"
    echo "    path: /health/liveness"
    echo "    port: 8000"
    echo "  initialDelaySeconds: 30"
    echo "  periodSeconds: 10"
    echo ""
    echo "readinessProbe:"
    echo "  httpGet:"
    echo "    path: /health/readiness" 
    echo "    port: 8000"
    echo "  initialDelaySeconds: 10"
    echo "  periodSeconds: 5"
    echo ""
    
    echo -e "${BLUE}Use Case 2: Load Balancer Configuration${NC}"
    echo "health_check {"
    echo "  enabled             = true"
    echo "  healthy_threshold   = 2"
    echo "  unhealthy_threshold = 2"
    echo "  timeout             = 5"
    echo "  interval            = 30"
    echo "  path                = \"/health/readiness\""
    echo "  matcher             = \"200\""
    echo "}"
    echo ""
    
    echo -e "${BLUE}Use Case 3: Monitoring Alerts${NC}"
    echo "- alert: ServiceUnhealthy"
    echo "  expr: health_check_status{type=\"readiness\"} != 1"
    echo "  for: 2m"
    echo "  labels:"
    echo "    severity: critical"
    echo "  annotations:"
    echo "    summary: \"Service health check failing\""
    echo ""
}

# Main execution
main() {
    echo -e "${GREEN}Starting SRE Health Check Demonstration...${NC}"
    echo ""
    
    simulate_health_endpoints
    echo ""
    
    test_health_scenarios
    echo ""
    
    demonstrate_monitoring_integration
    echo ""
    
    demonstrate_troubleshooting_workflow
    echo ""
    
    demonstrate_operational_use_cases
    echo ""
    
    echo -e "${GREEN}========================================"
    echo "SRE HEALTH CHECK DEMONSTRATION COMPLETE"
    echo "========================================${NC}"
    echo ""
    echo "Key SRE Concepts Demonstrated:"
    echo "✓ Multiple health check types (liveness, readiness, startup, deep)"
    echo "✓ Dependency health monitoring with circuit breakers"
    echo "✓ Integration with Kubernetes, load balancers, and monitoring"
    echo "✓ Structured troubleshooting workflows"
    echo "✓ Automated operational procedures"
    echo ""
    echo "Next Steps:"
    echo "1. Implement health endpoints in your service"
    echo "2. Configure Kubernetes probes"
    echo "3. Set up monitoring alerts"
    echo "4. Create runbooks for health check failures"
    echo "5. Test failure scenarios in staging environment"
}

# Run the demonstration
main "$@"