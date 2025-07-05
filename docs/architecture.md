# Technical Architecture

## Overview
The compliance automation platform integrates forensic investigation principles with DevOps automation to deliver end-to-end compliance, audit, and risk management for regulated industries.

## Components
- **Compliance Monitor (Python):** Collects compliance metrics, exposes Prometheus endpoint, applies forensic logic to metric collection.
- **Prometheus:** Scrapes and stores compliance metrics for alerting and dashboarding.
- **Grafana:** Visualizes compliance scores, risk, and audit readiness for executives.
- **Elasticsearch:** Stores forensic-grade audit logs for investigation and compliance evidence.
- **Ansible Playbooks:** Enforce and validate compliance controls for pharma and finance scenarios.
- **Terraform:** Deploys the platform on AWS ECS, configures cloud-native compliance (AWS Config, CloudTrail).
- **Automated Testing:** Molecule, Python, and shell scripts validate compliance controls and scoring.

## Data Flow Diagram
```
+-------------------+      +-----------------+      +-------------------+
| Compliance Monitor| ---> | Prometheus      | ---> | Grafana Dashboard |
+-------------------+      +-----------------+      +-------------------+
        |                        |                        |
        v                        v                        v
  +----------------+      +----------------+      +-------------------+
  | Audit Logs     |      | Compliance     |      | Executive Reports |
  | (Elasticsearch)|      | Scoring/Alerts |      | & Risk Metrics    |
  +----------------+      +----------------+      +-------------------+
```

## Forensic + DevOps Integration
- **Forensic:** Audit trail completeness, chain-of-custody, tamper-evidence, and evidence validation are built into playbooks and monitoring.
- **DevOps:** Infrastructure-as-code, automated testing, CI/CD, and cloud-native deployment ensure repeatability and scalability.

## Cloud Architecture (AWS)
- **ECS Fargate:** Runs compliance monitor and supporting services.
- **Application Load Balancer:** Secure access to metrics and dashboards.
- **AWS Config & CloudTrail:** Native cloud compliance and audit logging.
- **Security Groups:** Least privilege, segmented access.

---
See `../terraform/main.tf` and `../docker/docker-compose.yml` for implementation details. 