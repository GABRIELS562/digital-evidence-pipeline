# Service Down Runbook

## SRE INCIDENT RESPONSE - SERVICE DOWN

**Alert:** ServiceDown  
**Severity:** Critical  
**SLO Impact:** Direct impact on availability SLO  
**Expected Resolution Time:** < 15 minutes  

---

## SRE FUNDAMENTAL CONCEPTS

This runbook demonstrates core SRE practices:
- **Incident Response:** Structured approach to service recovery
- **Mean Time To Recovery (MTTR):** Focus on quick restoration
- **Blameless Culture:** Focus on fixing, not blame
- **Learning from Incidents:** Post-incident review for improvement

---

## IMMEDIATE ACTIONS (First 5 Minutes)

### 1. Verify the Alert
```bash
# SRE PRACTICE: Always verify alerts before acting
curl -f http://compliance-monitor:8000/health || echo "Service confirmed down"

# Check Prometheus targets
curl -s http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="compliance-service")'
```

### 2. Check Service Status
```bash
# SRE PRACTICE: Start with service-level debugging
docker ps | grep compliance-monitor
docker logs --tail=50 compliance-monitor

# For Kubernetes environments
kubectl get pods -l app=compliance-monitor
kubectl logs -l app=compliance-monitor --tail=50
```

### 3. Quick Health Assessment
```bash
# SRE PRACTICE: Assess infrastructure dependencies
curl -f http://prometheus:9090/-/healthy
curl -f http://grafana:3000/api/health

# Check database connectivity (if applicable)
docker exec compliance-monitor nc -z database 5432
```

---

## DIAGNOSTIC STEPS (Next 10 Minutes)

### 4. Resource Utilization Check
```bash
# SRE GOLDEN SIGNAL: Saturation
docker stats compliance-monitor --no-stream

# Check system resources
df -h
free -m
top -bn1 | head -20
```

### 5. Network Connectivity
```bash
# SRE PRACTICE: Verify network layer
docker network ls
docker exec compliance-monitor ping -c 3 prometheus
docker exec compliance-monitor ping -c 3 grafana

# Check port bindings
netstat -tlnp | grep :8000
```

### 6. Application Logs Analysis
```bash
# SRE PRACTICE: Look for error patterns
docker logs compliance-monitor | grep -i error | tail -20
docker logs compliance-monitor | grep -i exception | tail -20
docker logs compliance-monitor | grep -i fatal | tail -20

# Check startup sequence
docker logs compliance-monitor | head -30
```

---

## RECOVERY ACTIONS

### 7. Service Restart (If Required)
```bash
# SRE PRACTICE: Graceful restart first
docker restart compliance-monitor

# Wait for startup
sleep 30

# Verify recovery
curl -f http://compliance-monitor:8000/health
```

### 8. Configuration Validation
```bash
# SRE PRACTICE: Verify configuration integrity
docker exec compliance-monitor cat /app/config.yml
docker exec compliance-monitor python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Check environment variables
docker exec compliance-monitor env | grep -E "(DATABASE|REDIS|API)"
```

### 9. Full Stack Restart (Last Resort)
```bash
# SRE PRACTICE: Coordinated restart to avoid cascading failures
docker-compose down
sleep 10
docker-compose up -d

# Monitor startup sequence
docker-compose logs -f
```

---

## VERIFICATION STEPS

### 10. Service Health Validation
```bash
# SRE PRACTICE: Comprehensive health verification
curl -s http://compliance-monitor:8000/health | jq .
curl -s http://compliance-monitor:8000/metrics | head -10

# Check key metrics are flowing
curl -s http://prometheus:9090/api/v1/query?query=up{job="compliance-service"}
```

### 11. SLI Monitoring
```bash
# SRE PRACTICE: Verify SLIs are recovering
curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_success_rate_5m'
curl -s 'http://prometheus:9090/api/v1/query?query=sre:http_request_latency_p99'
```

---

## ESCALATION

### When to Escalate
- Service not restored within 15 minutes
- Multiple dependencies failing
- Unknown error patterns
- Infrastructure-level issues

### Escalation Contacts
```
Primary On-call: +1-555-SRE-TEAM
Secondary: +1-555-DEV-TEAM
Infrastructure: +1-555-OPS-TEAM
```

---

## POST-INCIDENT ACTIONS

### 12. Incident Documentation
```bash
# SRE PRACTICE: Document for learning
echo "Incident: $(date)" >> /var/log/incidents.log
echo "Duration: [START] - [END]" >> /var/log/incidents.log
echo "Root Cause: [DESCRIPTION]" >> /var/log/incidents.log
echo "Resolution: [ACTIONS TAKEN]" >> /var/log/incidents.log
```

### 13. Metrics Collection
```bash
# SRE PRACTICE: Measure MTTR for improvement
INCIDENT_START="2024-01-01T10:00:00Z"
INCIDENT_END="2024-01-01T10:15:00Z"

# Calculate downtime impact
curl -s "http://prometheus:9090/api/v1/query_range?query=up{job=\"compliance-service\"}&start=${INCIDENT_START}&end=${INCIDENT_END}&step=15s"
```

---

## PREVENTION MEASURES

### 14. Health Check Enhancement
- Implement more comprehensive health checks
- Add dependency health validation
- Monitor resource utilization trends

### 15. Automation Opportunities
- Auto-restart on health check failure
- Automated log analysis and alerting
- Proactive capacity monitoring

---

## SRE LESSONS LEARNED

This incident demonstrates several SRE principles:

1. **Structured Response:** Following a systematic approach reduces MTTR
2. **Observability:** Good monitoring helps identify root causes quickly
3. **Automation:** Manual steps can be automated to prevent future incidents
4. **Documentation:** Recording actions helps improve response procedures
5. **Blameless Culture:** Focus on system improvement, not individual blame

---

## RELATED RUNBOOKS

- [High Error Rate](./high-error-rate.md)
- [High Latency](./high-latency.md)
- [Infrastructure Issues](./infrastructure-issues.md)