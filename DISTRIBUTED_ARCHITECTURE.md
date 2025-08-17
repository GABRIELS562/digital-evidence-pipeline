# Distributed Architecture: 2 Mini PCs + MacBook

## Perfect Setup! This changes everything

With 2 mini PCs at different sites, you can create a professional distributed system with K8s at the remote site and central monitoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MacBook Pro M3                          │
│                  (Development & Control)                     │
│  • Development environment                                   │
│  • kubectl access to both sites                             │
│  • Central dashboards                                       │
└──────────────┬────────────────────────┬────────────────────┘
               │                        │
               │ VPN/SSH                │ VPN/SSH
               │                        │
┌──────────────▼────────────┐  ┌───────▼──────────────────────┐
│   Mini PC #1 (Your Site)  │  │  Mini PC #2 (Client Site)    │
│     Lenovo i7 16GB        │  │     Lenovo i7 16GB           │
│                           │  │                              │
│  Docker Compose:          │  │  Kubernetes (K3s):           │
│  • Compliance Platform    │  │  • LIMS Backend (Full)       │
│  • Trading Apps           │  │  • LIMS Database             │
│  • Monitoring Stack       │  │  • Message Queue             │
│  • Prometheus (Central)   │  │                              │
│                           │  │  Docker (Client Access):     │
│  Remote Prometheus        │  │  • LIMS Frontend (Simple)    │
│  Scraping ───────────────►│  │  • Read-only Dashboard       │
│                           │  │  • Limited Functions         │
└───────────────────────────┘  └──────────────────────────────┘
     Primary Site                    Client Site
   (24/7 Monitoring)              (24/7 LIMS + Client)
```

## Deployment Strategy

### Mini PC #1 (Your Site) - Monitoring Hub
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Central Monitoring
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus-multi-site.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=false
      
  # Compliance Platform
  compliance-monitor:
    build: ./compliance
    ports:
      - "8000:8000"
      
  # Trading/Finance Apps
  trading-app:
    build: ./trading
    ports:
      - "8080:8080"
```

### Mini PC #2 (Client Site) - LIMS + K8s
```yaml
# K8s for internal LIMS infrastructure
apiVersion: v1
kind: Namespace
metadata:
  name: lims-internal
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lims-backend
  namespace: lims-internal
spec:
  replicas: 2  # HA for reliability
  template:
    spec:
      containers:
      - name: lims-api
        image: lims-backend:latest
        ports:
        - containerPort: 5000
        resources:
          limits:
            memory: "1Gi"
            cpu: "1"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: lims-postgres
  namespace: lims-internal
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
```

### Client Access (Docker on Same PC)
```yaml
# docker-compose-client.yml
# Simplified LIMS for client access
version: '3.8'

services:
  lims-client-ui:
    image: lims-frontend:client
    ports:
      - "80:80"  # Public facing
    environment:
      - API_URL=http://localhost:5000
      - READ_ONLY_MODE=true
      - FEATURES=basic  # Limited features
    networks:
      - client-net
      
  nginx-proxy:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx-client.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - lims-client-ui
```

## Resource Distribution

### Mini PC #1 (Primary Site)
```
Service              Memory    CPU     Purpose
--------------------------------------------------
Prometheus           512MB     0.5     Central monitoring
Grafana             256MB     0.25    Dashboards
Elasticsearch       512MB     0.5     Central logging
Compliance App      256MB     0.25    Compliance metrics
Trading App         512MB     0.5     Trading system
Trading DB          1GB       0.5     PostgreSQL
AlertManager        128MB     0.1     Alerting
--------------------------------------------------
TOTAL:              3.2GB     2.6     
FREE:               12.8GB    5.4 cores
```

### Mini PC #2 (Client Site)
```
K8s Cluster:
--------------------------------------------------
K3s Control Plane   1GB       1.0     Kubernetes
LIMS Backend (x2)   1GB       1.0     HA deployment
LIMS Database       1GB       0.5     PostgreSQL
Redis Cache         256MB     0.2     Session/cache
Message Queue       256MB     0.2     RabbitMQ
--------------------------------------------------
Subtotal:           3.5GB     2.9

Docker (Client):
--------------------------------------------------
LIMS Client UI      256MB     0.2     Simple frontend
Nginx Proxy         128MB     0.1     SSL/Security
--------------------------------------------------
Subtotal:           384MB     0.3

TOTAL:              3.9GB     3.2 cores
FREE:               12.1GB    4.8 cores
```

## Multi-Site Prometheus Configuration

```yaml
# prometheus-multi-site.yml (on Mini PC #1)
global:
  scrape_interval: 15s
  external_labels:
    site: 'primary'

scrape_configs:
  # Local monitoring
  - job_name: 'local-services'
    static_configs:
      - targets: 
        - 'localhost:9090'
        - 'compliance-monitor:8000'
        - 'trading-app:8080'
        labels:
          site: 'primary'
          
  # Remote LIMS monitoring (via VPN/SSH tunnel)
  - job_name: 'remote-lims'
    static_configs:
      - targets:
        - 'mini-pc-2.vpn:30000'  # K8s metrics endpoint
        - 'mini-pc-2.vpn:5000'   # LIMS metrics
        labels:
          site: 'client'
          service: 'lims'
    
  # Remote K8s cluster monitoring
  - job_name: 'kubernetes-cluster'
    kubernetes_sd_configs:
      - role: endpoints
        api_server: 'https://mini-pc-2.vpn:6443'
        tls_config:
          ca_file: /etc/prometheus/k8s-ca.crt
          cert_file: /etc/prometheus/k8s-cert.crt
          key_file: /etc/prometheus/k8s-key.key
```

## Security & Networking

### VPN Setup (WireGuard)
```bash
# On Mini PC #2 (Client Site)
sudo apt install wireguard
wg genkey | tee privatekey | wg pubkey > publickey

# /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.2/24
PrivateKey = <private-key>
ListenPort = 51820

[Peer]
PublicKey = <mini-pc-1-public-key>
Endpoint = <your-site-ip>:51820
AllowedIPs = 10.0.0.1/32
```

### SSH Tunnel Alternative
```bash
# From Mini PC #1 to Mini PC #2
ssh -L 30000:localhost:30000 \
    -L 6443:localhost:6443 \
    -L 5000:localhost:5000 \
    user@mini-pc-2

# Make permanent with autossh
autossh -M 0 -f -N \
  -o "ServerAliveInterval 30" \
  -o "ServerAliveCountMax 3" \
  -L 30000:localhost:30000 \
  user@mini-pc-2
```

## Client Access Security

### 1. Read-Only LIMS for Client
```javascript
// lims-client-config.js
export default {
  features: {
    viewSamples: true,
    editSamples: false,
    runAnalysis: false,
    viewReports: true,
    exportReports: true,
    adminPanel: false
  },
  api: {
    endpoint: '/api/readonly',
    timeout: 5000,
    retries: 3
  }
}
```

### 2. Network Isolation
```yaml
# docker-compose-client.yml
networks:
  client-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
  internal-net:
    driver: bridge
    internal: true  # No external access
```

## Deployment Commands

### Initial Setup
```bash
# Mini PC #1 (Your Site)
cd /opt/compliance-platform
docker-compose up -d

# Mini PC #2 (Client Site)
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Deploy LIMS to K8s
kubectl apply -f lims-k8s/

# Start client Docker
docker-compose -f docker-compose-client.yml up -d
```

### Remote Management from MacBook
```bash
# Add both clusters to kubectl
kubectl config set-cluster mini-pc-1 \
  --server=https://mini-pc-1.vpn:6443

kubectl config set-cluster mini-pc-2 \
  --server=https://mini-pc-2.vpn:6443

# Switch contexts
kubectl config use-context mini-pc-2
kubectl get pods -n lims-internal

# Deploy updates
kubectl apply -f updates/
```

## Monitoring Dashboard Configuration

### Grafana Multi-Site Dashboard
```json
{
  "dashboard": {
    "title": "Multi-Site Compliance Overview",
    "panels": [
      {
        "title": "Site Health",
        "targets": [
          {
            "expr": "up{site='primary'}",
            "legendFormat": "Primary Site"
          },
          {
            "expr": "up{site='client'}",
            "legendFormat": "Client Site (LIMS)"
          }
        ]
      },
      {
        "title": "LIMS Performance",
        "targets": [
          {
            "expr": "rate(lims_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Compliance Score by Site",
        "targets": [
          {
            "expr": "compliance_score{site='primary'}",
            "legendFormat": "Trading/Finance"
          },
          {
            "expr": "compliance_score{site='client'}",
            "legendFormat": "LIMS/Laboratory"
          }
        ]
      }
    ]
  }
}
```

## Backup Strategy

```bash
# Automated backup script
#!/bin/bash
# backup-lims.sh (runs on Mini PC #2)

# Backup K8s LIMS data
kubectl exec -n lims-internal lims-postgres-0 -- \
  pg_dump -U postgres lims_db > /backup/lims-$(date +%Y%m%d).sql

# Sync to primary site
rsync -avz /backup/ mini-pc-1:/backup/client-site/

# Keep 30 days of backups
find /backup -name "*.sql" -mtime +30 -delete
```

## Advantages of This Setup

1. **True K8s Experience**: Client site runs real K8s
2. **Client Isolation**: Simplified Docker UI for clients
3. **Central Monitoring**: All metrics flow to primary site
4. **Resource Efficiency**: Each PC handles ~4GB, plenty of headroom
5. **High Availability**: K8s provides HA for LIMS
6. **Security**: Client can't access internal K8s
7. **Professional**: Enterprise-grade distributed architecture

This is actually a better architecture than running everything on one machine!