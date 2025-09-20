# 🚀 Quick Deploy Guide - 4 Hour Setup

## Overview
This guide gets your multi-site compliance monitoring operational in 4 hours using mock exporters that simulate realistic data from your LIMS and zero-downtime pipeline.

## Architecture
```
EC2 Instance (Compliance Platform)
├── Prometheus (collects metrics)
├── Grafana (visualizes data)
├── Mock LIMS Exporter (simulates FDA metrics)
├── Mock Pipeline Exporter (simulates deployment metrics)
└── SSH Tunnels → Home Server (when ready)
```

## Hour 1: Setup Mock Exporters (45 min)

### 1.1 Start Mock Exporters Locally (15 min)
```bash
# Terminal 1 - LIMS Exporter
cd compliance-automation-platform
python3 scripts/mock-lims-exporter.py
# Serves on :9101/metrics

# Terminal 2 - Pipeline Exporter  
python3 scripts/mock-pipeline-exporter.py
# Serves on :9102/metrics

# Verify metrics are exposed
curl localhost:9101/metrics | grep lims_
curl localhost:9102/metrics | grep pipeline_
```

### 1.2 Deploy with Docker Compose (30 min)
```bash
cd docker

# Use the remote monitoring stack
docker-compose -f docker-compose-remote.yml up -d

# Check all services are running
docker-compose -f docker-compose-remote.yml ps

# View logs
docker-compose -f docker-compose-remote.yml logs -f
```

## Hour 2: Configure Prometheus (30 min)

### 2.1 Verify Prometheus Targets
```bash
# Open Prometheus UI
open http://localhost:9090/targets

# Should see:
# ✓ lims-homeserver (via :9101)
# ✓ pipeline-ec2 (via :9102)
# ✓ compliance-monitor (:8000)
```

### 2.2 Test Queries
```promql
# In Prometheus UI, test these queries:

# LIMS FDA Compliance
lims_compliance_score

# Pipeline Health Checks
pipeline_sub50ms_rate

# Deployment Success
pipeline_deployment_success_rate
```

## Hour 3: Setup Grafana Dashboards (45 min)

### 3.1 Access Grafana
```bash
# Default credentials
URL: http://localhost:3000
Username: admin
Password: admin  # Change on first login
```

### 3.2 Import Dashboard
1. Click "+" → "Import"
2. Upload `/dashboards/multi-site-overview.json`
3. Select Prometheus data source
4. Save dashboard

### 3.3 Verify Metrics Flow
- LIMS compliance should fluctuate 85-95%
- Health checks should show ~85% under 50ms
- Deployment metrics update every 2 hours
- Watch for canary deployments (0-100% progress)

## Hour 4: SSH Tunnels & Testing (45 min)

### 4.1 Setup SSH Access (When Home Server Ready)
```bash
# Generate SSH key on EC2
ssh-keygen -t rsa -b 4096 -f ~/.ssh/home_server_key

# Copy public key to home server
ssh-copy-id -i ~/.ssh/home_server_key.pub user@YOUR_HOME_IP

# Test connection
ssh -i ~/.ssh/home_server_key user@YOUR_HOME_IP
```

### 4.2 Start SSH Tunnels
```bash
# Edit script with your home IP
vim scripts/simple-ssh-tunnel.sh
# Change: HOME_SERVER_IP="YOUR_HOME_IP"

# Start tunnels
./scripts/simple-ssh-tunnel.sh start

# Check status
./scripts/simple-ssh-tunnel.sh status

# Monitor tunnels (keeps them alive)
./scripts/simple-ssh-tunnel.sh monitor
```

### 4.3 Test Alerts
```bash
# Trigger test alert (stop an exporter)
docker stop lims-mock-exporter

# Check AlertManager
open http://localhost:9093

# Should see "LIMSExporterDown" alert

# Restart exporter
docker start lims-mock-exporter
```

## Deployment Commands Summary

### Start Everything
```bash
# Quick start with mock data
cd compliance-automation-platform/docker
docker-compose -f docker-compose-remote.yml up -d

# Verify
docker ps
curl localhost:9090/targets
curl localhost:3000/api/health
```

### Stop Everything
```bash
docker-compose -f docker-compose-remote.yml down
./scripts/simple-ssh-tunnel.sh stop
```

### View Logs
```bash
# All services
docker-compose -f docker-compose-remote.yml logs

# Specific service
docker logs prometheus
docker logs lims-mock-exporter
docker logs pipeline-mock-exporter
```

### Update Configuration
```bash
# After editing prometheus-remote.yml
docker-compose -f docker-compose-remote.yml restart prometheus

# After editing alert rules
docker exec prometheus kill -HUP 1
```

## What You Get

### Metrics Available
- **LIMS**: FDA compliance, signatures, audit trail, data integrity
- **Pipeline**: Sub-50ms health checks, deployment success, rollbacks
- **Apps**: Finance/Pharma health scores
- **System**: CPU, memory, disk usage

### Dashboards
- Multi-site overview with all locations
- FDA compliance trending
- Deployment success rates
- Health check latency distribution

### Alerts Configured
- FDA compliance violations
- Health checks over 50ms
- Deployment failures
- System connectivity issues

## Next Steps (After 4 Hours)

### Replace Mock Data with Real Metrics
1. Deploy exporters to actual LIMS/Pipeline
2. Update endpoints in prometheus-remote.yml
3. Remove mock exporters from docker-compose

### Add More Dashboards
- Create industry-specific views
- Add SLO/SLI tracking
- Build executive reports

### Enhance Monitoring
- Add log aggregation with ELK
- Implement distributed tracing
- Add custom business metrics

## Troubleshooting

### Prometheus Can't Reach Exporters
```bash
# Check network
docker network inspect docker_compliance-net

# Test from Prometheus container
docker exec prometheus wget -O- http://lims-mock-exporter:9101/metrics
```

### Grafana Shows No Data
```bash
# Check datasource
curl -X GET http://admin:admin@localhost:3000/api/datasources

# Test query
curl -X POST http://localhost:9090/api/v1/query \
  -d 'query=lims_compliance_score'
```

### SSH Tunnels Keep Dropping
```bash
# Use monitoring mode
./scripts/simple-ssh-tunnel.sh monitor

# Or use autossh (more robust)
apt-get install autossh
autossh -M 0 -f -N -L 9101:localhost:9101 user@home_ip
```

## Success Checklist

- [ ] Mock exporters generating data
- [ ] Prometheus scraping all targets
- [ ] Grafana dashboard showing metrics
- [ ] Alerts configured and tested
- [ ] SSH tunnel script ready (for later)
- [ ] Documentation complete

## Time Saved

**Traditional Approach**: 10-12 hours
- Writing real exporters: 4 hours
- Setting up SSH/VPN: 2 hours  
- Debugging connectivity: 2 hours
- Creating dashboards: 2 hours
- Testing everything: 2 hours

**This Approach**: 4 hours
- Mock exporters work immediately
- No network debugging needed
- Pre-built dashboards
- Alerts ready to go
- SSH tunnels prepared for later

You now have a **fully functional compliance monitoring platform** that looks exactly like production but uses simulated data. When your LIMS and pipeline are ready, just swap the mock exporters for real ones!