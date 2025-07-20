# SRE (Site Reliability Engineering) Fundamentals

## Overview

This directory showcases **fundamental SRE practices** implemented in a compliance automation platform. The examples demonstrate entry-level to intermediate SRE concepts that are essential for maintaining reliable, observable, and scalable systems.

---

## 🎯 SRE Skills Demonstrated

### **Core SRE Principles**
- **Service Level Indicators (SLIs):** Metrics that matter for user experience
- **Service Level Objectives (SLOs):** Target reliability levels
- **Error Budget Management:** Balancing reliability with feature velocity
- **Golden Signals:** Latency, Traffic, Errors, Saturation
- **Incident Response:** Structured approach to outage resolution
- **Blameless Culture:** Learning from failures without blame

### **Technical Implementations**
- **Monitoring & Observability:** Prometheus, Grafana, custom metrics
- **Alerting:** Actionable alerts tied to customer impact
- **Health Checks:** Multiple types for different operational needs
- **Automation:** Reducing manual operational overhead
- **Infrastructure as Code:** Terraform for reliable deployments
- **Testing:** Automated validation of reliability practices

---

## 📁 Directory Structure

```
sre/
├── README.md                          # This file - SRE concepts overview
├── monitoring/                        # Observability and metrics
│   ├── prometheus-sre.yml            # SRE-focused Prometheus config
│   └── sre-recording-rules.yml       # Pre-computed metrics for SLIs
├── alerting/                          # Incident detection and response
│   └── sre-alert-rules.yml           # Actionable alerts with runbooks
├── runbooks/                          # Troubleshooting procedures
│   ├── service-down.md                # Critical service failure response
│   └── high-error-rate.md             # Error rate incident response
├── health-checks/                     # Service availability monitoring
│   ├── health_monitor.py              # Comprehensive health check implementation
│   ├── health_config.json             # Health check configuration
│   └── test_health_checks.sh          # Health check testing and validation
└── automation/                        # Operational automation (future)
```

---

## 🔍 SRE Concepts by File

### **Monitoring (`monitoring/`)**

#### `prometheus-sre.yml`
**SRE Concepts:**
- **Four Golden Signals:** Latency, Traffic, Errors, Saturation monitoring
- **SLI Definition:** Key metrics that reflect user experience
- **Recording Rules:** Pre-computed metrics for consistent dashboards
- **Service Discovery:** Automated target detection

**Entry-Level Skills:**
```yaml
# Basic metric collection setup
scrape_configs:
  - job_name: "compliance-service"
    static_configs:
      - targets: ["compliance-monitor:8000"]
    scrape_interval: 30s
```

#### `sre-recording-rules.yml`
**SRE Concepts:**
- **SLI Calculation:** Automated reliability metric computation
- **Error Budget Tracking:** Real-time SLO compliance monitoring
- **Performance Aggregation:** Percentile calculations for latency SLIs

**Entry-Level Skills:**
```yaml
# Simple availability SLI
- record: sre:availability_current
  expr: sre:http_success_rate_5m * 100
```

### **Alerting (`alerting/`)**

#### `sre-alert-rules.yml`
**SRE Concepts:**
- **Actionable Alerts:** Every alert requires human action
- **Customer Impact Focus:** Alerts tied to user experience
- **Severity Levels:** Critical vs Warning based on business impact
- **Runbook Integration:** Linking alerts to response procedures

**Entry-Level Skills:**
```yaml
# Basic error rate alert
- alert: HighErrorRate
  expr: sre:http_error_rate_5m > 0.05  # 5% threshold
  for: 2m
  annotations:
    summary: "Error rate: {{ $value | humanizePercentage }}"
    runbook_url: "https://runbooks.example.com/high-error-rate"
```

### **Runbooks (`runbooks/`)**

#### `service-down.md` & `high-error-rate.md`
**SRE Concepts:**
- **Incident Response:** Structured troubleshooting procedures
- **Mean Time To Recovery (MTTR):** Focus on fast restoration
- **Escalation Paths:** When and how to involve additional resources
- **Post-Incident Learning:** Documentation for improvement

**Entry-Level Skills:**
- Systematic debugging approach
- Infrastructure health validation
- Service dependency checking
- Log analysis techniques

### **Health Checks (`health-checks/`)**

#### `health_monitor.py`
**SRE Concepts:**
- **Health Check Types:** Liveness, Readiness, Startup, Deep
- **Circuit Breaker Pattern:** Preventing cascading failures
- **Dependency Monitoring:** Upstream/downstream service health
- **Graceful Degradation:** Service behavior during partial failures

**Entry-Level Skills:**
```python
# Basic liveness check
def _liveness_check(self) -> HealthCheck:
    return HealthCheck(
        name="liveness",
        status=HealthStatus.HEALTHY,
        message="Service is alive and responding"
    )
```

---

## 🎓 Learning Path for Entry-Level SRE

### **Phase 1: Monitoring Fundamentals (Week 1-2)**
1. **Start Here:** `monitoring/prometheus-sre.yml`
   - Understand metric collection basics
   - Learn about scrape intervals and targets
   - Practice reading Prometheus configuration

2. **Practice:** Set up basic monitoring
   ```bash
   # Deploy monitoring stack
   docker-compose up prometheus grafana
   
   # Check metrics collection
   curl http://localhost:9090/api/v1/targets
   ```

### **Phase 2: Basic Alerting (Week 3)**
1. **Study:** `alerting/sre-alert-rules.yml`
   - Learn alert rule syntax
   - Understand threshold-based alerting
   - Practice writing simple alerts

2. **Practice:** Create your first alert
   ```yaml
   - alert: ServiceDown
     expr: up{job="my-service"} == 0
     for: 1m
   ```

### **Phase 3: Health Checks (Week 4)**
1. **Implement:** Basic health endpoints
   - Start with simple HTTP 200 responses
   - Add dependency checks gradually
   - Learn about different health check types

2. **Practice:** Use `health-checks/test_health_checks.sh`

### **Phase 4: Incident Response (Week 5-6)**
1. **Study:** Runbooks in `runbooks/`
   - Learn structured troubleshooting
   - Practice incident response procedures
   - Understand escalation criteria

2. **Practice:** Simulate outages and practice response

---

## 🛠️ Hands-On Exercises

### **Exercise 1: Basic Monitoring Setup**
```bash
# 1. Deploy monitoring stack
cd /path/to/compliance-automation-platform
docker-compose up -d prometheus grafana

# 2. Verify metrics collection
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# 3. Check basic metrics
curl -s http://localhost:9090/api/v1/query?query=up
```

### **Exercise 2: Create Your First SLI**
```yaml
# Add to prometheus-sre.yml recording rules
- record: my_service:availability_5m
  expr: |
    rate(http_requests_total{code!~"5.."}[5m]) /
    rate(http_requests_total[5m]) * 100
```

### **Exercise 3: Implement Health Check**
```python
# Simple health endpoint
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### **Exercise 4: Practice Incident Response**
1. Trigger a test alert
2. Follow runbook procedures
3. Document resolution steps
4. Identify improvement opportunities

---

## 📊 Key Metrics to Understand

### **Golden Signals**
| Signal | Metric Example | SRE Purpose |
|--------|----------------|-------------|
| **Latency** | `http_request_duration_seconds` | User experience |
| **Traffic** | `http_requests_per_second` | Load understanding |
| **Errors** | `http_error_rate` | Reliability tracking |
| **Saturation** | `cpu_utilization_percent` | Capacity planning |

### **SLI Examples**
```promql
# Availability SLI (99.9% target)
sre:availability_5m = 
  rate(http_requests_total{code!~"5.."}[5m]) /
  rate(http_requests_total[5m]) * 100

# Latency SLI (95% under 500ms)
sre:latency_p95_5m = 
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Budget (remaining allowance)
sre:error_budget_remaining = 
  (sre:availability_5m - 99.9) / (100 - 99.9) * 100
```

---

## 🚀 Resume-Ready Skills

After working through this SRE implementation, you can confidently claim:

### **Technical Skills**
- **Monitoring:** Prometheus metrics collection, Grafana dashboards
- **Alerting:** Threshold-based alerts, runbook integration
- **Health Checks:** Kubernetes probes, load balancer integration
- **Incident Response:** Structured troubleshooting, MTTR optimization
- **Automation:** Infrastructure as Code, configuration management

### **SRE Practices**
- **SLI/SLO Definition:** Understanding reliability targets
- **Error Budget Management:** Balancing reliability and velocity
- **Golden Signals Monitoring:** Focus on user-impacting metrics
- **Blameless Culture:** Learning-focused incident response
- **Observability:** Making systems understandable and debuggable

### **Tools & Technologies**
- **Monitoring:** Prometheus, Grafana, AlertManager
- **Infrastructure:** Docker, Kubernetes health probes
- **Automation:** Terraform, Ansible, Python scripting
- **Testing:** Molecule testing framework, automated validation

---

## 📚 Next Steps

### **Immediate (Next 2 weeks)**
1. Deploy the monitoring stack locally
2. Practice writing basic alerts
3. Implement simple health checks
4. Study and practice one runbook scenario

### **Short Term (Next month)**
1. Add SLO tracking to a personal project
2. Create incident response documentation
3. Practice troubleshooting workflows
4. Build monitoring dashboards

### **Medium Term (Next 3 months)**
1. Implement circuit breaker patterns
2. Add capacity planning metrics
3. Create comprehensive runbooks
4. Practice chaos engineering

---

## 🔗 Related Files

- **Main Project:** `../` - Complete compliance automation platform
- **Infrastructure:** `../terraform/` - Infrastructure as Code examples
- **Testing:** `../tests/` - Automated testing frameworks
- **CI/CD:** `../Jenkinsfile` - Deployment automation

---

## 📝 Learning Resources

### **SRE Fundamentals**
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) - Free online
- [Prometheus Documentation](https://prometheus.io/docs/) - Monitoring basics
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

### **Hands-On Practice**
- Deploy this monitoring stack
- Follow the runbook procedures
- Practice incident response scenarios
- Implement health checks in personal projects

---

**💡 Remember:** SRE is about making systems reliable, observable, and manageable. Start with the basics, practice regularly, and always focus on improving user experience and system reliability.