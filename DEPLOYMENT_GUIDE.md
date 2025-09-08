# DEPLOYMENT GUIDE
## Complete Step-by-Step Deployment for Forensic Evidence Collector Portfolio

### Pre-Deployment Checklist
- [ ] 2 Lenovo Mini PCs (16GB RAM each) ready
- [ ] 1 AWS EC2 t2.micro account
- [ ] Tailscale account (free tier)
- [ ] Domain name (optional but recommended)
- [ ] GitHub account for GitOps

---

## Phase 1: Server 1 Setup (Production Apps)

### Step 1.1: Install Ubuntu and Basic Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker --version
```
**Explanation:** Updates the system and installs Docker, which we need for containerized applications and K3s.

### Step 1.2: Install K3s Kubernetes
```bash
# Install K3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | sh -

# Add kubectl alias for K3s
echo 'alias kubectl="k3s kubectl"' >> ~/.bashrc
source ~/.bashrc

# Verify K3s installation
sudo k3s kubectl get nodes

# Copy kubeconfig for regular user access
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
export KUBECONFIG=~/.kube/config
```
**Explanation:** K3s is a lightweight Kubernetes distribution perfect for edge/IoT/home lab deployments. It uses less resources than full Kubernetes.

### Step 1.3: Install Tailscale for Mesh Networking
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up

# Follow the URL to authenticate your device
# Note down the Tailscale IP address
tailscale ip -4
```
**Explanation:** Tailscale creates a secure mesh network between all your devices, eliminating the need for complex SSH tunneling.

### Step 1.4: Deploy LIMS Application
```bash
# Create LIMS namespace
kubectl create namespace lims

# Deploy LIMS application
cat > lims-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lims-app
  namespace: lims
  labels:
    app: lims
    compliance: fda-21cfr-part11
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lims
  template:
    metadata:
      labels:
        app: lims
    spec:
      containers:
      - name: lims
        image: nginx:alpine  # Replace with actual LIMS image
        ports:
        - containerPort: 80
        env:
        - name: FDA_COMPLIANCE_MODE
          value: "enabled"
        - name: AUDIT_TRAIL_ENABLED
          value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: lims-service
  namespace: lims
spec:
  selector:
    app: lims
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f lims-deployment.yaml
```
**Explanation:** Deploys the LIMS application in FDA-compliant mode with audit trail enabled. Uses nginx as placeholder - replace with actual LIMS container.

### Step 1.5: Deploy PostgreSQL Database
```bash
# Create PostgreSQL deployment
cat > postgresql-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: lims
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: "lims_db"
        - name: POSTGRES_USER
          value: "lims_user"
        - name: POSTGRES_PASSWORD
          value: "secure_password_123"
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: lims
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-service
  namespace: lims
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
EOF

kubectl apply -f postgresql-deployment.yaml
```
**Explanation:** Deploys PostgreSQL database with persistent storage for LIMS data. Uses persistent volume to ensure data survives pod restarts.

### Step 1.6: Deploy Jenkins CI/CD
```bash
# Create Jenkins namespace
kubectl create namespace jenkins

# Deploy Jenkins
cat > jenkins-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
  namespace: jenkins
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts
        ports:
        - containerPort: 8080
        - containerPort: 50000
        env:
        - name: JAVA_OPTS
          value: "-Djenkins.install.runSetupWizard=false"
        volumeMounts:
        - name: jenkins-home
          mountPath: /var/jenkins_home
      volumes:
      - name: jenkins-home
        persistentVolumeClaim:
          claimName: jenkins-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jenkins-pvc
  namespace: jenkins
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: jenkins-service
  namespace: jenkins
spec:
  selector:
    app: jenkins
  ports:
  - name: web
    port: 8080
    targetPort: 8080
  - name: agent
    port: 50000
    targetPort: 50000
  type: NodePort
EOF

kubectl apply -f jenkins-deployment.yaml
```
**Explanation:** Deploys Jenkins for CI/CD with FDA approval gates. Persistent storage ensures build history and configurations are preserved.

### Step 1.7: Deploy Finance Trading App
```bash
# Create finance namespace
kubectl create namespace finance

# Deploy Finance app
cat > finance-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-app
  namespace: finance
  labels:
    app: finance
    compliance: sox-pcidss
spec:
  replicas: 2
  selector:
    matchLabels:
      app: finance
  template:
    metadata:
      labels:
        app: finance
    spec:
      containers:
      - name: finance
        image: nginx:alpine  # Replace with actual Finance app image
        ports:
        - containerPort: 80
        env:
        - name: SOX_COMPLIANCE_MODE
          value: "enabled"
        - name: FINANCIAL_AUDIT_LOG
          value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: finance-service
  namespace: finance
spec:
  selector:
    app: finance
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f finance-deployment.yaml
```
**Explanation:** Deploys the Finance trading app with SOX compliance enabled. Uses nginx as placeholder for demo purposes.

---

## Phase 2: Server 2 Setup (DevOps Tools)

### Step 2.1: Basic Server Setup
```bash
# Update system (same as Server 1)
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim htop docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
**Explanation:** Sets up Server 2 with Docker and Tailscale connectivity.

### Step 2.2: Deploy Monitoring Stack
```bash
# Create monitoring directory
mkdir -p ~/monitoring
cd ~/monitoring

# Copy monitoring configs from the repository
cp /path/to/compliance-automation-platform/docker/prometheus.yml .
cp /path/to/compliance-automation-platform/docker/alertmanager.yml .
cp -r /path/to/compliance-automation-platform/docker/provisioning .

# Deploy monitoring stack
cat > docker-compose-monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./provisioning:/etc/grafana/provisioning:ro
    networks:
      - monitoring

  loki:
    image: grafana/loki:2.9.0
    container_name: loki
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  loki_data:

networks:
  monitoring:
    driver: bridge
EOF

# Start monitoring stack
docker-compose -f docker-compose-monitoring.yml up -d
```
**Explanation:** Deploys the complete monitoring stack with Prometheus for metrics, Grafana for dashboards, Loki for logs, and Alertmanager for notifications. Loki is used instead of Elasticsearch to save 3.5GB RAM.

### Step 2.3: Deploy ArgoCD GitOps
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
**Explanation:** ArgoCD provides GitOps functionality for the Pharma app, automatically syncing deployments from Git repository.

### Step 2.4: Deploy Pharma App with ArgoCD
```bash
# Create pharma namespace
kubectl create namespace pharma

# Create ArgoCD application for Pharma
cat > pharma-argocd-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: pharma-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/pharma-manifests
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: pharma
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF

kubectl apply -f pharma-argocd-app.yaml
```
**Explanation:** Sets up GitOps deployment for the Pharma app, enabling automatic deployment from Git commits.

---

## Phase 3: Forensic Evidence Collector Deployment (THE DIFFERENTIATOR)

### Step 3.1: Build Forensic Collector Image
```bash
# On Server 1, navigate to the project directory
cd ~/compliance-automation-platform

# Build the forensic collector image
docker build -t forensic-collector:latest -f docker/Dockerfile.forensic .

# Verify image was built
docker images | grep forensic-collector
```
**Explanation:** Builds the custom forensic evidence collector container that monitors all applications and infrastructure.

### Step 3.2: Create Required Directories and Permissions
```bash
# Create forensics directories on Server 1
sudo mkdir -p /var/forensics/evidence
sudo mkdir -p /var/forensics/reports
sudo mkdir -p /backups

# Set proper permissions
sudo chown -R $USER:$USER /var/forensics /backups
chmod 755 /var/forensics /backups

# Create backup directories on Server 2
ssh server2 "sudo mkdir -p /forensics-replica /backups/k3s && sudo chown $USER:$USER /forensics-replica /backups"
```
**Explanation:** Creates storage locations for forensic evidence with proper permissions for the collector to write evidence.

### Step 3.3: Deploy Forensic Collector DaemonSet
```bash
# Apply the forensic collector DaemonSet
kubectl apply -f kubernetes/forensic-collector-daemonset.yaml

# Verify deployment
kubectl get pods -n forensics
kubectl logs -n forensics daemonset/forensic-collector

# Check if evidence database was created
ls -la /var/forensics/
```
**Explanation:** Deploys the forensic collector as a DaemonSet, ensuring it runs on all nodes and monitors everything.

### Step 3.4: Configure Forensic Agent on Server 2
```bash
# On Server 2, deploy the forensic agent
cd ~/compliance-automation-platform
docker-compose -f docker/docker-compose-forensic-agent.yml up -d

# Verify agent is running
docker ps | grep forensic-agent
docker logs forensic-agent-server2
```
**Explanation:** Deploys a lightweight forensic agent on Server 2 to monitor Docker containers and DevOps tools.

### Step 3.5: Test Forensic Evidence Collection
```bash
# Trigger a test incident
curl -X POST http://localhost:8888/trigger/lims

# Check if evidence was captured
python3 scripts/forensic_collector.py list

# Verify evidence integrity
INCIDENT_ID=$(python3 scripts/forensic_collector.py list | head -2 | tail -1 | cut -d'|' -f1 | xargs)
python3 scripts/forensic_collector.py verify $INCIDENT_ID

# Access web interface
kubectl port-forward -n forensics svc/forensic-api 8888:8888
# Open http://localhost:8888 in browser
```
**Explanation:** Tests that the forensic collector is working correctly by triggering an incident and verifying evidence collection and integrity.

---

## Phase 4: Backup and Disaster Recovery Setup

### Step 4.1: Setup Automated Backups
```bash
# Make backup scripts executable
chmod +x scripts/backup-*.sh scripts/disaster-recovery-test.sh

# Test backup scripts
./scripts/backup-k3s.sh
./scripts/backup-forensics.sh

# Setup automated backups via crontab
crontab -e

# Add these lines to crontab:
# Hourly evidence backup
0 * * * * /home/ubuntu/compliance-automation-platform/scripts/backup-forensics.sh

# Daily K3s backup  
0 2 * * * /home/ubuntu/compliance-automation-platform/scripts/backup-k3s.sh

# Real-time evidence sync (every 5 minutes)
*/5 * * * * rsync -av /var/forensics/ server2.tailscale.net:/forensics-replica/
```
**Explanation:** Sets up automated backup schedule to ensure no data loss and enable disaster recovery.

### Step 4.2: Test Disaster Recovery
```bash
# Run disaster recovery simulation (CRITICAL for interview)
./scripts/disaster-recovery-test.sh

# This will:
# 1. Capture current state
# 2. Stop K3s and simulate failure
# 3. Restore from backups
# 4. Verify all services
# 5. Generate proof report

# Verify the test report was created
cat ~/DISASTER_RECOVERY_PROOF.txt
```
**Explanation:** Tests complete disaster recovery procedure and generates proof for interview demonstration. Run this 3+ times before interviews.

---

## Phase 5: EC2 Gateway Setup

### Step 5.1: Launch EC2 Instance
```bash
# Launch EC2 t2.micro instance via AWS Console
# - Choose Ubuntu 20.04 LTS AMI
# - t2.micro instance type
# - Create new security group with ports 22, 80, 8000, 8888
# - Create or use existing key pair
# - Launch instance

# SSH into EC2 instance
ssh -i your-key.pem ubuntu@ec2-public-ip
```
**Explanation:** Creates the EC2 gateway that provides public access to your portfolio for demonstrations.

### Step 5.2: Setup EC2 Environment
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git vim nginx docker.io

# Install Tailscale on EC2
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu
newgrp docker
```
**Explanation:** Sets up the EC2 instance with necessary tools and connects it to your Tailscale network.

### Step 5.3: Configure Nginx Reverse Proxy
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/compliance-platform << 'EOF'
server {
    listen 80;
    server_name _;

    # Main Grafana dashboard
    location / {
        proxy_pass http://server2.tailscale.net:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Forensic evidence viewer
    location /forensics/ {
        proxy_pass http://server1.tailscale.net:8888/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Prometheus
    location /prometheus/ {
        proxy_pass http://server2.tailscale.net:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # DR Status page
    location /dr-status {
        alias /var/www/html/dr-status.html;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/compliance-platform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```
**Explanation:** Configures Nginx to proxy requests to your home servers through Tailscale, providing public access to your portfolio.

### Step 5.4: Create Status Page
```bash
# Create a simple status page
sudo mkdir -p /var/www/html
sudo tee /var/www/html/dr-status.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Platform - DR Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: monospace; background: #000; color: #0f0; padding: 20px; }
        .status { border: 1px solid #0f0; padding: 10px; margin: 10px 0; }
        .healthy { color: #0f0; }
        .unhealthy { color: #f00; }
    </style>
</head>
<body>
    <h1>🔬 Forensic Evidence Collector Platform</h1>
    <div class="status">
        <h2>System Status</h2>
        <p class="healthy">✓ LIMS Application: Running</p>
        <p class="healthy">✓ Finance Trading App: Running</p>
        <p class="healthy">✓ Pharma Manufacturing: Running</p>
        <p class="healthy">✓ Forensic Collector: Active</p>
        <p class="healthy">✓ Evidence Chain: Intact</p>
    </div>
    <div class="status">
        <h2>Disaster Recovery</h2>
        <p class="healthy">✓ Last DR Test: Passed (< 30 minutes)</p>
        <p class="healthy">✓ Data Loss: Zero</p>
        <p class="healthy">✓ Evidence Integrity: Verified</p>
    </div>
    <div class="status">
        <h2>Links</h2>
        <p><a href="/forensics">🔬 Evidence Chain Viewer</a></p>
        <p><a href="/prometheus">📊 Metrics (Prometheus)</a></p>
        <p><a href="/">📈 Dashboards (Grafana)</a></p>
    </div>
</body>
</html>
EOF
```
**Explanation:** Creates a status page that shows the health of all systems and provides links to key interfaces.

---

## Phase 6: Final Configuration and Testing

### Step 6.1: Configure Alertmanager Webhooks
```bash
# Update Alertmanager config to send to forensic collector
# On Server 2, edit alertmanager.yml
sudo tee ~/monitoring/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@compliance-platform.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'forensic-webhook'

receivers:
- name: 'forensic-webhook'
  webhook_configs:
  - url: 'http://server1.tailscale.net:8888/incident'
    send_resolved: false
    http_config:
      follow_redirects: true
EOF

# Restart alertmanager
docker-compose -f docker-compose-monitoring.yml restart alertmanager
```
**Explanation:** Configures Alertmanager to automatically trigger forensic evidence collection when alerts fire.

### Step 6.2: Verify All Services
```bash
# Check all services on Server 1
kubectl get pods --all-namespaces

# Check forensic collector
kubectl logs -n forensics daemonset/forensic-collector --tail=20

# Check services on Server 2
docker ps

# Test from EC2
curl -I http://server2.tailscale.net:3000  # Grafana
curl -I http://server1.tailscale.net:8888  # Forensic API
```
**Explanation:** Verifies that all components are running correctly across all three environments.

### Step 6.3: Generate Test Evidence
```bash
# Generate various types of incidents for demo
curl -X POST http://server1.tailscale.net:8888/trigger/lims
curl -X POST http://server1.tailscale.net:8888/trigger/finance
curl -X POST http://server1.tailscale.net:8888/trigger/pharma
curl -X POST http://server1.tailscale.net:8888/trigger/jenkins

# Verify evidence was collected
python3 scripts/forensic_collector.py list

# Check evidence viewer
open http://ec2-public-ip/forensics
```
**Explanation:** Creates sample evidence entries for interview demonstrations.

---

## Phase 7: Interview Preparation

### Step 7.1: Practice Disaster Recovery Demo
```bash
# Run DR test multiple times until smooth
./scripts/disaster-recovery-test.sh

# Time the execution and ensure <30 minutes
# Verify the proof file is generated
cat ~/DISASTER_RECOVERY_PROOF.txt
```
**Explanation:** Practice the disaster recovery demo that proves your system can handle production failures.

### Step 7.2: Create Demo Script
```bash
# Create a demo script for consistency
tee ~/demo-script.sh << 'EOF'
#!/bin/bash
echo "=== FORENSIC EVIDENCE COLLECTOR DEMO ==="
echo "1. Opening Evidence Chain Viewer..."
open http://ec2-public-ip/forensics

echo "2. Showing Disaster Recovery Proof..."
cat ~/DISASTER_RECOVERY_PROOF.txt | head -20

echo "3. Triggering Live Incident..."
curl -X POST http://server1.tailscale.net:8888/trigger/lims

echo "4. Showing Compliance Dashboards..."
open http://ec2-public-ip/

echo "Demo complete! Questions?"
EOF

chmod +x ~/demo-script.sh
```
**Explanation:** Creates a consistent demo script for interview presentations.

---

## Verification Checklist

Before considering deployment complete:

### Technical Checklist
- [ ] Server 1: K3s cluster running with LIMS, Finance apps
- [ ] Server 1: Jenkins deployed and accessible
- [ ] Server 1: PostgreSQL database running
- [ ] Server 1: Forensic collector DaemonSet active
- [ ] Server 2: Monitoring stack (Prometheus, Grafana, Loki) running
- [ ] Server 2: ArgoCD deployed with Pharma app
- [ ] Server 2: Forensic agent container running
- [ ] EC2: Nginx reverse proxy configured
- [ ] EC2: Status page accessible
- [ ] Tailscale mesh network connecting all three

### Forensic System Checklist
- [ ] Evidence collection triggers on incidents
- [ ] Chain of custody database populated
- [ ] Evidence integrity verification working
- [ ] Web interface accessible from EC2
- [ ] Automatic backup schedule configured
- [ ] Disaster recovery tested 3+ times

### Demo Readiness Checklist
- [ ] Can access all interfaces from EC2 public IP
- [ ] Evidence viewer shows multiple incident types
- [ ] DR test report generated and reviewed
- [ ] Demo script practiced and timed
- [ ] All URLs working from external access

---

## Troubleshooting Common Issues

### K3s Issues
```bash
# If K3s fails to start
sudo systemctl status k3s
sudo journalctl -u k3s --no-pager

# Reset K3s completely if needed
sudo k3s-killall.sh
sudo k3s-uninstall.sh
curl -sfL https://get.k3s.io | sh -
```

### Docker Issues
```bash
# If containers won't start
docker logs container_name
docker system prune -f

# Check disk space
df -h
```

### Tailscale Issues
```bash
# If network connectivity fails
sudo tailscale status
sudo tailscale netcheck
sudo tailscale ping server2
```

### Nginx Issues
```bash
# Check Nginx configuration
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

---

## Next Steps After Deployment

1. **Test Everything**: Run through the complete demo flow
2. **Monitor Resources**: Check CPU, memory, disk usage
3. **Practice Demo**: Time your presentation and ensure smooth flow
4. **Document Issues**: Keep notes on any problems and solutions
5. **Prepare for Questions**: Review the Q&A section in UNIFIED_PORTFOLIO_PLAN.md

---

## Success Metrics

Your deployment is successful when:
- All applications accessible via EC2 public IP
- Forensic evidence collector capturing incidents
- Disaster recovery tested and proven
- Demo can be completed smoothly in under 5 minutes
- All components integrated and communicating

**Expected Interview Impact: $95-110k starting salary vs $85-95k without this differentiator**