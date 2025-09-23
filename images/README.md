# Digital Evidence Pipeline - Screenshots

## Current Screenshots

**`Prometheus-1.png`**
- Prometheus targets page showing infrastructure monitoring
- Shows forensic-ec2 target (100.101.99.93:9999) in UP status
- Demonstrates multi-tier monitoring architecture

**`Prometheus-2.png`** 
- Alternative view of Prometheus targets with forensic collector highlighted
- Proves cross-cloud monitoring integration (on-premise to AWS EC2)

**`Regulatory Compliance Scores-1.png`**
- Grafana dashboard showing compliance metrics overview
- Four panels: LIMS integrity, GMP compliance (94), Forensic monitor (92), SOX trending
- Executive-level compliance view

**`Regulatory Compliance Scores-2.png`**
- Extended compliance dashboard with additional metrics
- Shows: LIMS chain (1), Temperature violations (0), Trading anomalies (0), GMP (94)
- Demonstrates real-time regulatory monitoring

## Screenshot Details

**Compliance Scores Explained:**
- Green numbers (0,1): Perfect compliance/no violations
- Amber numbers (92,94): Good compliance with minor variations
- Time series: Shows compliance trends over time

**Architecture Shown:**
- Server 1: Production applications (ports 30007, 30002, 30003)
- Server 2: Monitoring stack (Prometheus/Grafana)  
- EC2: Forensic evidence collector (port 9999)

**Status:** All screenshots from live production system
