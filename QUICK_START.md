# 🚀 Quick Start Guide - Compliance Automation Platform

## **5-Minute Setup for Immediate Learning**

This guide gets you up and running with the SRE/DevOps platform in 5 minutes to start hands-on learning immediately.

---

## **Prerequisites (1 minute)**

```bash
# Check required tools
docker --version          # Docker 20+ required
docker-compose --version  # Docker Compose 2+ required
python3 --version         # Python 3.9+ required
git --version             # Git required
```

**System Requirements:**
- 8GB RAM (4GB minimum)
- 10GB free disk space
- MacOS, Linux, or Windows with WSL2

---

## **Instant Deployment (2 minutes)**

```bash
# 1. Clone and enter directory
cd /path/to/compliance-automation-platform

# 2. Create Grafana admin password
echo "admin123" > docker/admin_password

# 3. Deploy entire stack
cd docker
docker-compose up -d

# 4. Verify deployment
docker-compose ps
```

**Expected Output:**
```
NAME                 COMMAND                  SERVICE              STATUS
alertmanager         "/bin/alertmanager -…"   alertmanager         Up 30 seconds
compliance-monitor   "python3 /app/script…"   compliance-monitor   Up 30 seconds
elasticsearch        "/bin/tini -- /usr/l…"   elasticsearch        Up 45 seconds
grafana              "/run.sh"                grafana              Up 30 seconds
node-exporter        "/bin/node_exporter …"   node-exporter        Up 30 seconds
prometheus           "/bin/prometheus --c…"   prometheus           Up 30 seconds
```

---

## **Access Your SRE Platform (1 minute)**

### **🔍 Monitoring Dashboard**
- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: `admin123`

### **📊 Metrics & Alerting**
- **Prometheus:** http://localhost:9090
- **Alertmanager:** http://localhost:9093

### **🏥 Health Monitoring**
- **Service Health:** http://localhost:8000/health/deep
- **Metrics Endpoint:** http://localhost:8000/metrics

### **📋 Log Analysis**
- **Elasticsearch:** http://localhost:9200/_cluster/health

---

## **Verify SRE Concepts (1 minute)**

### **Test Health Checks**
```bash
# Test different health check types
curl http://localhost:8000/health/liveness    # Basic service health
curl http://localhost:8000/health/readiness   # Ready for traffic
curl http://localhost:8000/health/deep        # Complete system health
```

### **Check Metrics Collection**
```bash
# View SRE metrics
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result'

# Check Golden Signals
curl -s "http://localhost:9090/api/v1/query?query=sre:http_success_rate_5m"
```

### **View Alert Rules**
```bash
# Check configured alerts
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[].name'
```

---

## **🎓 Start Learning Immediately**

### **1. Explore SRE Fundamentals (5 minutes)**
```bash
# Navigate to SRE examples
cd ../sre

# Read SRE concepts
cat README.md | head -50

# View monitoring configuration
cat monitoring/prometheus-sre.yml | grep -A 5 "SRE CONCEPT"
```

### **2. Practice Health Checks (5 minutes)**
```bash
# Run health check tests
cd sre/health-checks
chmod +x test_health_checks.sh
./test_health_checks.sh
```

### **3. Study Alerting (5 minutes)**
```bash
# View alert configurations
cd ../alerting
cat sre-alert-rules.yml | grep -A 10 "ServiceDown"

# Check alert routing
cd ../../docker
cat alertmanager.yml | grep -A 15 "route:"
```

### **4. Practice Incident Response (10 minutes)**
```bash
# Read runbook procedures
cd ../sre/runbooks
cat service-down.md | head -50

# Simulate service failure
docker stop compliance-monitor

# Check alerts (wait 2 minutes)
curl http://localhost:9090/alerts

# Restore service
docker start compliance-monitor
```

---

## **🎯 Learning Objectives Checklist**

After this quick start, you can demonstrate:

### **✅ Basic SRE Skills**
- [ ] **Monitoring Setup**: Deployed Prometheus/Grafana stack
- [ ] **Health Checks**: Understand liveness, readiness, deep health concepts
- [ ] **Alert Configuration**: Basic threshold-based alerting
- [ ] **Incident Response**: Structured troubleshooting approach
- [ ] **Container Orchestration**: Docker Compose service management

### **✅ DevOps Practices**
- [ ] **Infrastructure as Code**: Configuration management
- [ ] **Observability**: Metrics, logs, traces understanding
- [ ] **Automation**: Automated deployment and testing
- [ ] **Documentation**: Runbooks and procedures

---

## **🚨 Troubleshooting Common Issues**

### **Service Won't Start**
```bash
# Check logs
docker-compose logs compliance-monitor

# Check port conflicts
netstat -tlnp | grep -E "(3000|8000|9090|9093)"

# Restart specific service
docker-compose restart compliance-monitor
```

### **Health Checks Failing**
```bash
# Check container status
docker ps | grep compliance

# View health check logs
docker inspect compliance-monitor | jq '.[].State.Health'

# Test manually
docker exec compliance-monitor curl -f http://localhost:8000/health/liveness
```

### **Metrics Not Appearing**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify service connectivity
docker exec prometheus nc -zv compliance-monitor 8000

# Check configuration
docker exec prometheus cat /etc/prometheus/prometheus.yml
```

### **Memory Issues**
```bash
# Reduce Elasticsearch memory
docker-compose down
export ES_JAVA_OPTS="-Xms256m -Xmx256m"
docker-compose up -d
```

---

## **🎯 Next Steps**

### **Immediate (Today)**
1. ✅ Complete quick start setup
2. 📚 Read `sre/README.md` comprehensive guide
3. 🔧 Practice health check scenarios
4. 📊 Explore Grafana dashboards

### **This Week**
1. 📖 Study runbook procedures in `sre/runbooks/`
2. 🧪 Practice incident response scenarios
3. 🏗️ Deploy on cloud infrastructure (AWS)
4. 📝 Create your first custom alert

### **This Month**
1. 🏢 Apply concepts to personal projects
2. 📋 Build comprehensive monitoring for existing applications
3. 🎯 Practice SRE interview scenarios
4. 🌟 Contribute improvements to the platform

---

## **📚 Learning Resources**

### **Platform-Specific**
- `sre/README.md` - Complete SRE learning guide
- `docs/architecture.md` - Technical architecture deep-dive
- `CLAUDE.md` - Implementation roadmap

### **External Resources**
- [Google SRE Book](https://sre.google/sre-book/) - Free SRE fundamentals
- [Prometheus Documentation](https://prometheus.io/docs/) - Monitoring guide
- [Grafana Tutorials](https://grafana.com/tutorials/) - Dashboard creation

---

## **🎉 Success! You're Ready to Learn**

You now have a **production-quality SRE platform** running locally that demonstrates:

- **Monitoring**: Prometheus metrics collection
- **Alerting**: ActionaDeveloper alerts with runbooks
- **Health Checks**: Multiple health check types
- **Incident Response**: Structured troubleshooting procedures
- **Automation**: Infrastructure as Code and container orchestration

**Start with the SRE README:** `sre/README.md` for comprehensive learning path.

**Questions?** Check the troubleshooting section above or review configuration files in `/docker` directory.