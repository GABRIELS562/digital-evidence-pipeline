# Final Architecture: 2 Mini PCs Only

## Simple & Clean Setup

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   Mini PC #1 (Your Site)    │     │  Mini PC #2 (Client Site)   │
│      Lenovo i7 16GB         │     │      Lenovo i7 16GB         │
│                             │     │                             │
│  Docker Compose:            │     │  K3s Kubernetes:            │
│  • Compliance Platform      │────►│  • LIMS Backend (Full)      │
│  • Monitoring (Prometheus)  │ VPN │  • LIMS Database            │
│  • Grafana Dashboards       │     │                             │
│  • Trading Apps             │     │  Docker (for client):       │
│  • Finance Apps             │     │  • Simple LIMS UI           │
│  • Pharma Apps              │     │  • Read-only Dashboard      │
└─────────────────────────────┘     └─────────────────────────────┘
```

## PC #1: Monitoring & Trading Hub
```bash
# Everything in Docker Compose
docker-compose up -d

# Services running:
- Prometheus (monitors both PCs)
- Grafana (all dashboards)
- Compliance Platform
- Trading Applications
- Finance Applications
- AlertManager
```

## PC #2: LIMS & Client Access
```bash
# K3s for backend
curl -sfL https://get.k3s.io | sh -
kubectl apply -f lims/

# Docker for client UI
docker run -d -p 80:80 lims-client:simple
```

## Resource Usage

**PC #1**: ~7GB used, 9GB free
**PC #2**: ~4GB used, 12GB free

Both PCs have plenty of room. This setup gives you:
- K8s experience (PC #2)
- Central monitoring (PC #1)
- Client isolation (Docker UI only)
- Professional distributed architecture