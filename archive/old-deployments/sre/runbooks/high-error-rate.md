# High Error Rate Runbook

## SRE INCIDENT RESPONSE - HIGH ERROR RATE

**Alert:** HighErrorRate  
**Severity:** Critical  
**SLO Impact:** Direct impact on availability SLO (99.9% target)  
**Error Budget Impact:** High burn rate  
**Expected Resolution Time:** < 20 minutes  

---

## SRE FUNDAMENTAL CONCEPTS

This runbook demonstrates:
- **Error Budget Management:** Understanding impact on SLOs
- **Golden Signals:** Focusing on errors as a key reliability metric  
- **Customer Impact Assessment:** Prioritizing user-facing issues
- **Data-Driven Debugging:** Using metrics to guide investigation

---

## IMMEDIATE TRIAGE (First 3 Minutes)

### 1. Assess Error Rate Impact
```bash
# SRE PRACTICE: Quantify the problem first
curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_error_rate_5m' | jq '.data.result[0].value[1]'

# Check current vs historical error rate
curl -s 'http://prometheus:9090/api/v1/query?query=increase(http_requests_total{code=~"5.."}[5m])'
curl -s 'http://prometheus:9090/api/v1/query?query=increase(http_requests_total[5m])'
```

### 2. Error Budget Calculation
```bash
# SRE PRACTICE: Understand SLO impact
curl -s 'http://prometheus:9090/api/v1/query?query=sre:error_budget_remaining_percent' | jq '.data.result[0].value[1]'

# Calculate burn rate
echo "If current error rate continues, error budget will be exhausted in X hours"
```

### 3. Customer Impact Assessment
```bash
# SRE PRACTICE: Determine blast radius
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total[5m])' | jq '.data.result[0].value[1]'

# Calculate affected requests per minute
echo "Approximately $(( $(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total[5m])' | jq -r '.data.result[0].value[1]' | cut -d. -f1) * $(curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_error_rate_5m' | jq -r '.data.result[0].value[1]' | cut -d. -f1) / 100 )) failed requests per minute"
```

---

## ERROR ANALYSIS (Next 5 Minutes)

### 4. Error Type Breakdown
```bash
# SRE PRACTICE: Categorize errors for targeted response
echo "=== 5XX Errors (Server Issues) ==="
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{code=~"5.."}[5m]) by (code)' | jq '.data.result'

echo "=== 4XX Errors (Client Issues) ==="
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{code=~"4.."}[5m]) by (code)' | jq '.data.result'
```

### 5. Error Pattern Analysis
```bash
# SRE PRACTICE: Look for patterns in timing and endpoints
echo "=== Errors by Endpoint ==="
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{code=~"5.."}[5m]) by (endpoint)' | jq '.data.result'

echo "=== Error Timeline ==="
curl -s 'http://prometheus:9090/api/v1/query_range?query=rate(http_requests_total{code=~"5.."}[5m])&start='$(date -d '30 minutes ago' -u +%Y-%m-%dT%H:%M:%SZ)'&end='$(date -u +%Y-%m-%dT%H:%M:%SZ)'&step=60s'
```

### 6. Application Log Investigation
```bash
# SRE PRACTICE: Correlate metrics with logs
echo "=== Recent Error Logs ==="
docker logs compliance-monitor --since=10m | grep -E "(ERROR|EXCEPTION|500|502|503|504)" | tail -20

echo "=== Error Frequency Analysis ==="
docker logs compliance-monitor --since=30m | grep -E "(ERROR|EXCEPTION)" | wc -l
```

---

## ROOT CAUSE INVESTIGATION (Next 7 Minutes)

### 7. Infrastructure Health Check
```bash
# SRE GOLDEN SIGNAL: Check Saturation
echo "=== CPU Utilization ==="
curl -s 'http://prometheus:9090/api/v1/query?query=sre:cpu_utilization_5m'

echo "=== Memory Utilization ==="
curl -s 'http://prometheus:9090/api/v1/query?query=sre:memory_utilization_5m'

echo "=== Disk I/O ==="
docker stats compliance-monitor --no-stream
```

### 8. Dependency Health Assessment
```bash
# SRE PRACTICE: Check upstream/downstream services
echo "=== Database Connectivity ==="
docker exec compliance-monitor nc -zv database 5432

echo "=== External API Health ==="
docker exec compliance-monitor curl -f http://external-api/health

echo "=== Prometheus Scraping ==="
curl -s 'http://prometheus:9090/api/v1/query?query=up{job="compliance-service"}'
```

### 9. Recent Changes Analysis
```bash
# SRE PRACTICE: Correlate with deployments
echo "=== Recent Container Restarts ==="
docker ps --format "table {{.Names}}\t{{.Status}}" | grep compliance

echo "=== Git History (Recent Deployments) ==="
git log --oneline --since="2 hours ago"

echo "=== Configuration Changes ==="
find /app/config -name "*.yml" -mtime -1
```

---

## MITIGATION STRATEGIES

### 10. Quick Fixes (If Identified)

#### For Resource Exhaustion:
```bash
# SRE PRACTICE: Scale up resources temporarily
docker update --memory=2g --cpus=2 compliance-monitor
docker restart compliance-monitor
```

#### For Database Connection Issues:
```bash
# SRE PRACTICE: Restart database connections
docker exec compliance-monitor kill -USR1 1  # Graceful restart signal
```

#### For External Dependency Issues:
```bash
# SRE PRACTICE: Enable circuit breaker or fallback
docker exec compliance-monitor curl -X POST http://localhost:8000/admin/circuit-breaker/enable
```

### 11. Rollback Strategy (If Recent Deployment)
```bash
# SRE PRACTICE: Quick rollback to last known good state
git log --oneline -5
git checkout [PREVIOUS_COMMIT_HASH]
docker-compose down && docker-compose up -d

# Monitor error rate post-rollback
sleep 60
curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_error_rate_5m'
```

### 12. Traffic Reduction (Emergency)
```bash
# SRE PRACTICE: Reduce load to stabilize service
# Enable rate limiting
docker exec compliance-monitor curl -X POST http://localhost:8000/admin/rate-limit -d '{"rpm": 100}'

# Or redirect traffic via load balancer
# curl -X POST http://load-balancer/admin/weight -d '{"compliance-service": 50}'
```

---

## VERIFICATION AND MONITORING

### 13. Error Rate Recovery Tracking
```bash
# SRE PRACTICE: Monitor recovery metrics
echo "=== Monitoring Recovery ==="
for i in {1..10}; do
  ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_error_rate_5m' | jq -r '.data.result[0].value[1]')
  echo "$(date): Error rate = ${ERROR_RATE}%"
  sleep 30
done
```

### 14. SLO Impact Assessment
```bash
# SRE PRACTICE: Calculate impact on error budget
echo "=== Error Budget Status ==="
curl -s 'http://prometheus:9090/api/v1/query?query=sre:error_budget_remaining_percent' | jq '.data.result[0].value[1]'

echo "=== Estimated Recovery Time ==="
# Calculate time needed to restore error budget at current success rate
```

---

## ESCALATION CRITERIA

### Escalate Immediately If:
- Error rate > 20% for > 5 minutes
- Error budget < 5% remaining  
- Multiple services affected
- Customer-facing data corruption
- Security-related errors (401, 403 patterns)

### Escalation Contacts:
```
Engineering Manager: +1-555-ENG-MGR
Product Owner: +1-555-PRODUCT  
Security Team: +1-555-SECURITY (if security-related)
Customer Support: +1-555-SUPPORT (for customer communication)
```

---

## POST-INCIDENT ACTIVITIES

### 15. Error Budget Reporting
```bash
# SRE PRACTICE: Document SLO impact
cat > incident-report.md << EOF
# Error Rate Incident Report

## Summary
- **Start Time:** $(date -d '30 minutes ago')
- **End Time:** $(date)  
- **Peak Error Rate:** X%
- **Error Budget Consumed:** Y%
- **Customer Impact:** Z failed requests

## Timeline
- [TIME] Alert triggered
- [TIME] Investigation started  
- [TIME] Root cause identified
- [TIME] Mitigation applied
- [TIME] Service recovered

## Root Cause
[DESCRIPTION]

## Resolution
[ACTIONS TAKEN]

## Follow-up Actions
- [ ] Implement additional monitoring
- [ ] Improve error handling  
- [ ] Update runbook based on learnings
EOF
```

### 16. Preventive Measures
```bash
# SRE PRACTICE: Improve system reliability
echo "=== Suggested Improvements ==="
echo "1. Add circuit breakers for external dependencies"
echo "2. Implement graceful degradation"
echo "3. Add more granular error monitoring"
echo "4. Improve load testing coverage"
echo "5. Enhance alerting thresholds"
```

---

## SRE LESSONS LEARNED

This incident response demonstrates:

1. **Quantitative Analysis:** Using metrics to understand impact
2. **Systematic Investigation:** Following structured debugging approach
3. **Customer Focus:** Prioritizing user impact over technical details
4. **Error Budget Management:** Understanding SLO implications
5. **Proactive Monitoring:** Using leading indicators to prevent incidents

---

## RELATED RUNBOOKS

- [Service Down](./service-down.md)
- [High Latency](./high-latency.md)
- [Database Issues](./database-issues.md)
- [Security Incidents](./security-incidents.md)