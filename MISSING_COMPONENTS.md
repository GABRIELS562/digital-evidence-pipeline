# Missing Components for Production Monitoring

## Critical Components Needed

### 1. Remote Monitoring Configuration
```yaml
# prometheus-remote.yml - Add to docker/
scrape_configs:
  # LIMS on Home Server (via SSH tunnel)
  - job_name: "lims-homeserver"
    static_configs:
      - targets: ["localhost:9101"]  # SSH tunnel port
    metrics_path: /metrics
    scrape_interval: 30s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: "lims.homeserver"
      - source_labels: []
        target_label: environment
        replacement: "production"
      - source_labels: []
        target_label: compliance_domain
        replacement: "FDA_21CFR11"

  # Zero-Downtime Pipeline on EC2
  - job_name: "zero-downtime-pipeline"
    static_configs:
      - targets: ["ec2-instance:9102"]
    metrics_path: /metrics
    scrape_interval: 15s
    relabel_configs:
      - source_labels: []
        target_label: environment
        replacement: "production"
      - source_labels: []
        target_label: pipeline_type
        replacement: "canary_bluegreen"

  # Jenkins CI/CD Metrics
  - job_name: "jenkins"
    static_configs:
      - targets: ["ec2-instance:8080"]
    metrics_path: /prometheus/
    scrape_interval: 30s

  # ArgoCD GitOps Metrics
  - job_name: "argocd"
    static_configs:
      - targets: ["ec2-instance:8083"]
    metrics_path: /metrics
    scrape_interval: 30s

  # Trading App on Home Server
  - job_name: "trading-app"
    static_configs:
      - targets: ["localhost:9103"]  # SSH tunnel
    relabel_configs:
      - source_labels: []
        target_label: compliance_domain
        replacement: "SOX_PCIDSS"
```

### 2. SSH Tunnel Service
```python
# scripts/ssh-tunnel-manager.py
#!/usr/bin/env python3
"""
Manages SSH tunnels for secure remote monitoring
"""
import subprocess
import os
import time
import json
from typing import List, Dict

class SSHTunnelManager:
    def __init__(self, config_file: str = "tunnel_config.json"):
        with open(config_file) as f:
            self.config = json.load(f)
        self.tunnels = []
    
    def create_tunnel(self, tunnel_config: Dict):
        """Create SSH tunnel for remote monitoring"""
        cmd = [
            "ssh",
            "-N",  # No command execution
            "-f",  # Background
            "-L", f"{tunnel_config['local_port']}:{tunnel_config['remote_host']}:{tunnel_config['remote_port']}",
            "-i", tunnel_config['ssh_key'],
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=no",
            f"{tunnel_config['user']}@{tunnel_config['host']}"
        ]
        
        process = subprocess.Popen(cmd)
        return process.pid
    
    def setup_all_tunnels(self):
        """Setup all configured SSH tunnels"""
        for tunnel in self.config['tunnels']:
            pid = self.create_tunnel(tunnel)
            self.tunnels.append({
                'name': tunnel['name'],
                'pid': pid,
                'local_port': tunnel['local_port']
            })
            print(f"✓ Tunnel established: {tunnel['name']} on port {tunnel['local_port']}")
    
    def health_check(self):
        """Check if tunnels are alive"""
        for tunnel in self.tunnels:
            try:
                os.kill(tunnel['pid'], 0)
                print(f"✓ {tunnel['name']} is alive")
            except OSError:
                print(f"✗ {tunnel['name']} is dead, restarting...")
                # Restart logic here

# Tunnel configuration
TUNNEL_CONFIG = {
    "tunnels": [
        {
            "name": "LIMS-Kubernetes",
            "host": "YOUR_HOME_IP",
            "user": "ubuntu",
            "ssh_key": "/home/ubuntu/.ssh/home_server_key",
            "local_port": 9101,
            "remote_host": "localhost",
            "remote_port": 30001  # Kubernetes NodePort for LIMS
        },
        {
            "name": "Trading-App",
            "host": "YOUR_HOME_IP",
            "user": "ubuntu",
            "ssh_key": "/home/ubuntu/.ssh/home_server_key",
            "local_port": 9103,
            "remote_host": "localhost",
            "remote_port": 8080  # Trading app port
        }
    ]
}
```

### 3. LIMS-Specific Exporter
```python
# scripts/lims-exporter.py
#!/usr/bin/env python3
"""
LIMS-specific compliance metrics for FDA 21 CFR Part 11
"""
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import requests
import json

# FDA 21 CFR Part 11 Compliance Metrics
electronic_signature_valid = Gauge('lims_electronic_signature_valid', 'Electronic signature validation status')
audit_trail_integrity = Gauge('lims_audit_trail_integrity', 'Audit trail integrity check')
data_integrity_score = Gauge('lims_data_integrity_score', 'Data integrity score (0-100)')
access_control_violations = Counter('lims_access_violations', 'Unauthorized access attempts')
sample_chain_custody = Gauge('lims_sample_chain_custody', 'Sample chain of custody compliance')
backup_compliance = Gauge('lims_backup_compliance', 'Backup and recovery compliance')
validation_status = Gauge('lims_validation_status', 'System validation status')

# Performance Metrics
sample_processing_time = Histogram('lims_sample_processing_seconds', 'Time to process samples')
query_response_time = Histogram('lims_query_response_seconds', 'Database query response time')
report_generation_time = Histogram('lims_report_generation_seconds', 'Report generation time')

class LIMSMonitor:
    def __init__(self, lims_api_url: str):
        self.api_url = lims_api_url
    
    def check_fda_compliance(self):
        """Check FDA 21 CFR Part 11 compliance"""
        try:
            # Check electronic signatures
            sig_check = requests.get(f"{self.api_url}/compliance/signatures")
            electronic_signature_valid.set(1 if sig_check.json()['valid'] else 0)
            
            # Check audit trail
            audit_check = requests.get(f"{self.api_url}/compliance/audit-trail")
            audit_trail_integrity.set(1 if audit_check.json()['intact'] else 0)
            
            # Data integrity
            integrity = requests.get(f"{self.api_url}/compliance/data-integrity")
            data_integrity_score.set(integrity.json()['score'])
            
            # Sample chain of custody
            custody = requests.get(f"{self.api_url}/compliance/chain-custody")
            sample_chain_custody.set(1 if custody.json()['compliant'] else 0)
            
            # Backup compliance
            backup = requests.get(f"{self.api_url}/compliance/backup-status")
            backup_compliance.set(1 if backup.json()['compliant'] else 0)
            
            # System validation
            validation = requests.get(f"{self.api_url}/compliance/validation")
            validation_status.set(1 if validation.json()['validated'] else 0)
            
        except Exception as e:
            print(f"Error checking FDA compliance: {e}")
    
    def check_performance(self):
        """Check LIMS performance metrics"""
        try:
            perf = requests.get(f"{self.api_url}/metrics/performance")
            data = perf.json()
            
            # Record performance metrics
            sample_processing_time.observe(data['sample_processing_time'])
            query_response_time.observe(data['query_time'])
            report_generation_time.observe(data['report_time'])
            
        except Exception as e:
            print(f"Error checking performance: {e}")

def main():
    # Start metrics server
    start_http_server(30001)  # Kubernetes NodePort
    
    monitor = LIMSMonitor("http://lims-service:8080")
    
    while True:
        monitor.check_fda_compliance()
        monitor.check_performance()
        time.sleep(30)

if __name__ == "__main__":
    main()
```

### 4. Zero-Downtime Pipeline Exporter
```python
# scripts/pipeline-exporter.py
#!/usr/bin/env python3
"""
Zero-downtime deployment pipeline metrics
"""
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import requests
import time

# Deployment Metrics
deployment_success_rate = Gauge('pipeline_deployment_success_rate', 'Deployment success rate')
canary_rollout_progress = Gauge('pipeline_canary_progress', 'Canary deployment progress (0-100)')
blue_green_active = Gauge('pipeline_blue_green_active', 'Active environment (0=blue, 1=green)')
rollback_count = Counter('pipeline_rollback_total', 'Total number of rollbacks')
deployment_duration = Histogram('pipeline_deployment_duration_seconds', 'Deployment duration')

# Health Check Metrics
health_check_latency = Histogram('pipeline_health_check_latency_ms', 'Health check response time')
health_check_success = Gauge('pipeline_health_check_success', 'Health check success rate')
sub_50ms_compliance = Gauge('pipeline_sub50ms_compliance', 'Percentage of checks under 50ms')

# CI/CD Metrics
build_success_rate = Gauge('pipeline_build_success_rate', 'Build success rate')
test_coverage = Gauge('pipeline_test_coverage', 'Test coverage percentage')
security_scan_issues = Gauge('pipeline_security_issues', 'Number of security issues found')

class PipelineMonitor:
    def __init__(self, jenkins_url: str, argocd_url: str):
        self.jenkins_url = jenkins_url
        self.argocd_url = argocd_url
    
    def check_deployment_metrics(self):
        """Monitor deployment strategies"""
        try:
            # Check canary deployment
            canary = requests.get(f"{self.argocd_url}/api/v1/applications/finance-app/resource")
            canary_data = canary.json()
            canary_rollout_progress.set(canary_data.get('rollout_percentage', 0))
            
            # Check blue-green status
            bg = requests.get(f"{self.argocd_url}/api/v1/applications/pharma-app/resource")
            bg_data = bg.json()
            blue_green_active.set(1 if bg_data.get('active_env') == 'green' else 0)
            
            # Deployment success rate
            jenkins_jobs = requests.get(f"{self.jenkins_url}/api/json?tree=jobs[lastBuild[result]]")
            jobs_data = jenkins_jobs.json()
            
            success_count = sum(1 for job in jobs_data['jobs'] 
                              if job['lastBuild'] and job['lastBuild']['result'] == 'SUCCESS')
            total_count = len(jobs_data['jobs'])
            
            if total_count > 0:
                deployment_success_rate.set((success_count / total_count) * 100)
            
        except Exception as e:
            print(f"Error checking deployment metrics: {e}")
    
    def check_health_endpoints(self):
        """Monitor sub-50ms health check compliance"""
        try:
            apps = ['finance-app', 'pharma-app']
            latencies = []
            
            for app in apps:
                start = time.time()
                resp = requests.get(f"http://{app}:8080/health", timeout=0.1)
                latency_ms = (time.time() - start) * 1000
                
                health_check_latency.observe(latency_ms)
                latencies.append(latency_ms)
            
            # Calculate sub-50ms compliance
            under_50ms = sum(1 for l in latencies if l < 50)
            sub_50ms_compliance.set((under_50ms / len(latencies)) * 100 if latencies else 0)
            
        except Exception as e:
            print(f"Error checking health endpoints: {e}")

def main():
    start_http_server(9102)
    monitor = PipelineMonitor("http://jenkins:8080", "http://argocd:8080")
    
    while True:
        monitor.check_deployment_metrics()
        monitor.check_health_endpoints()
        time.sleep(15)

if __name__ == "__main__":
    main()
```

### 5. Industry-Specific Alert Rules
```yaml
# alert_rules_industry.yml
groups:
  - name: fda_compliance_alerts
    rules:
      - alert: FDAElectronicSignatureInvalid
        expr: lims_electronic_signature_valid == 0
        for: 1m
        labels:
          severity: critical
          regulation: "FDA 21 CFR Part 11"
          system: lims
        annotations:
          summary: "FDA: Electronic signature validation failed"
          description: "Electronic signatures are not compliant with FDA 21 CFR Part 11"
          
      - alert: LIMSAuditTrailCompromised
        expr: lims_audit_trail_integrity == 0
        for: 1m
        labels:
          severity: critical
          regulation: "FDA 21 CFR Part 11"
        annotations:
          summary: "FDA: Audit trail integrity compromised"
          description: "Audit trail is incomplete or tampered - FDA violation"
          
      - alert: LIMSDataIntegrityLow
        expr: lims_data_integrity_score < 95
        for: 5m
        labels:
          severity: warning
          regulation: "FDA 21 CFR Part 11"
        annotations:
          summary: "FDA: Data integrity score below threshold"
          description: "Data integrity score is {{ $value }}% - FDA requires 95%+"

  - name: sox_compliance_alerts
    rules:
      - alert: SOXFinancialDataUnencrypted
        expr: trading_encryption_status == 0
        for: 1m
        labels:
          severity: critical
          regulation: "SOX Section 404"
          system: trading
        annotations:
          summary: "SOX: Financial data transmission unencrypted"
          description: "Trading app transmitting financial data without encryption"
          
      - alert: SOXAccessControlViolation
        expr: increase(trading_unauthorized_access[5m]) > 0
        labels:
          severity: critical
          regulation: "SOX Section 302"
        annotations:
          summary: "SOX: Unauthorized access attempt detected"
          description: "{{ $value }} unauthorized access attempts in trading system"

  - name: zero_downtime_alerts
    rules:
      - alert: HealthCheckAbove50ms
        expr: pipeline_sub50ms_compliance < 95
        for: 2m
        labels:
          severity: warning
          slo: "sub-50ms"
        annotations:
          summary: "Health checks exceeding 50ms SLO"
          description: "Only {{ $value }}% of health checks under 50ms (target: 95%)"
          
      - alert: DeploymentRollbackDetected
        expr: increase(pipeline_rollback_total[1h]) > 0
        labels:
          severity: warning
          deployment: "zero-downtime"
        annotations:
          summary: "Deployment rollback occurred"
          description: "{{ $value }} rollbacks in the last hour"
          
      - alert: CanaryDeploymentStalled
        expr: pipeline_canary_progress > 0 and pipeline_canary_progress < 100
        for: 30m
        labels:
          severity: warning
          strategy: "canary"
        annotations:
          summary: "Canary deployment stalled"
          description: "Canary at {{ $value }}% for over 30 minutes"
```

### 6. Enhanced Grafana Dashboards
```json
{
  "title": "Multi-Site Compliance Overview",
  "panels": [
    {
      "title": "LIMS FDA Compliance Score",
      "targets": [
        {
          "expr": "(lims_electronic_signature_valid + lims_audit_trail_integrity + (lims_data_integrity_score/100) + lims_sample_chain_custody + lims_backup_compliance + lims_validation_status) / 6 * 100"
        }
      ]
    },
    {
      "title": "Zero-Downtime Health Check Latency",
      "targets": [
        {
          "expr": "histogram_quantile(0.99, pipeline_health_check_latency_ms)"
        }
      ]
    },
    {
      "title": "Trading App SOX Compliance",
      "targets": [
        {
          "expr": "(trading_encryption_status + trading_access_control_valid + trading_audit_complete) / 3 * 100"
        }
      ]
    },
    {
      "title": "Deployment Success Rate",
      "targets": [
        {
          "expr": "pipeline_deployment_success_rate"
        }
      ]
    }
  ]
}
```

### 7. Docker Compose Updates
```yaml
# docker-compose-remote.yml
services:
  ssh-tunnel-manager:
    build:
      context: .
      dockerfile: Dockerfile.tunnel-manager
    container_name: ssh-tunnel-manager
    volumes:
      - ~/.ssh:/root/.ssh:ro
      - ./tunnel_config.json:/app/tunnel_config.json:ro
    network_mode: host
    restart: unless-stopped
    
  lims-exporter:
    build:
      context: .
      dockerfile: Dockerfile.lims-exporter
    container_name: lims-exporter
    ports:
      - "9101:9101"
    environment:
      - LIMS_API_URL=http://localhost:9101  # Via SSH tunnel
    depends_on:
      - ssh-tunnel-manager
    networks:
      - compliance-net
      
  pipeline-exporter:
    build:
      context: .
      dockerfile: Dockerfile.pipeline-exporter
    container_name: pipeline-exporter
    ports:
      - "9102:9102"
    environment:
      - JENKINS_URL=http://ec2-instance:8080
      - ARGOCD_URL=http://ec2-instance:8083
    networks:
      - compliance-net
```

## Implementation Steps

1. **Setup SSH Keys** (30 min)
   - Generate SSH keypair on EC2
   - Add public key to home server
   - Test connectivity

2. **Deploy SSH Tunnel Manager** (1 hour)
   - Configure tunnel_config.json
   - Build and deploy container
   - Verify tunnels are established

3. **Deploy Custom Exporters** (2 hours)
   - Deploy LIMS exporter on home K8s
   - Deploy pipeline exporter on EC2
   - Verify metrics endpoints

4. **Update Prometheus Configuration** (30 min)
   - Add remote scrape targets
   - Configure service discovery
   - Reload Prometheus

5. **Import Industry Dashboards** (1 hour)
   - Create FDA compliance dashboard
   - Create SOX compliance dashboard
   - Create deployment metrics dashboard

6. **Configure Alerts** (30 min)
   - Add industry-specific rules
   - Configure AlertManager routing
   - Test alert firing

## Missing Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS EC2 Instance                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Compliance Automation Platform               │   │
│  │  ┌────────────┐  ┌─────────┐  ┌──────────────┐     │   │
│  │  │ Prometheus │──│ Grafana │──│ AlertManager │     │   │
│  │  └─────┬──────┘  └─────────┘  └──────────────┘     │   │
│  │        │                                            │   │
│  │  ┌─────▼──────────────────────────────┐            │   │
│  │  │     SSH Tunnel Manager              │            │   │
│  │  │  ┌─────────┐  ┌──────────┐        │            │   │
│  │  │  │ Port    │  │ Port     │        │            │   │
│  │  │  │ 9101    │  │ 9103     │        │            │   │
│  │  └──┴─────────┴──┴──────────┴────────┘            │   │
│  └──────────────────────────────────────────────────┘   │
│         │                │                               │
│         │ SSH Tunnel     │ SSH Tunnel                   │
│  ┌──────▼────────┐  ┌───▼──────┐                       │
│  │ Pipeline      │  │ Jenkins  │                       │
│  │ Exporter      │  │ ArgoCD   │                       │
│  │ :9102         │  │          │                       │
│  └───────────────┘  └──────────┘                       │
└─────────────┬────────────────────────────────────────────┘
              │ SSH Tunnels (Encrypted)
              │
┌─────────────▼────────────────────────────────────────────┐
│                    Home Server                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Kubernetes Cluster                      │   │
│  │  ┌─────────────┐  ┌──────────────┐              │   │
│  │  │ LIMS System │──│ LIMS Exporter│              │   │
│  │  │             │  │ :30001       │              │   │
│  │  └─────────────┘  └──────────────┘              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Docker Compose Stack                    │   │
│  │  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ Trading App  │──│ Trading      │            │   │
│  │  │              │  │ Exporter     │            │   │
│  │  └──────────────┘  └──────────────┘            │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

## Cost Impact
- No additional AWS services needed
- Uses existing EC2 instance
- SSH tunnels are free
- All monitoring stays on EC2

## Security Considerations
- SSH keys must be protected
- Use fail2ban on home server
- Implement IP whitelisting
- Regular key rotation
- Monitor tunnel connections

## Next Steps
1. Generate SSH keys
2. Configure home server access
3. Deploy tunnel manager
4. Test remote metrics collection
5. Build custom exporters
6. Update dashboards
7. Configure industry alerts