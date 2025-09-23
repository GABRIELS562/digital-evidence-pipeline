# Digital Evidence Pipeline (DEP)

**Forensic-grade DevOps compliance monitoring applying 15 years of DNA laboratory chain-of-custody principles to infrastructure.**

## 🎯 The Forensic Difference

**Traditional Monitoring**: "The system went down at 2 AM"  
**Forensic Monitoring**: "Here's cryptographic proof of the complete system state, with tamper-evident chain of custody"

This working system demonstrates how forensic science principles create audit trails for DevOps infrastructure.

## 🚀 Current Deployment Status

- **Platform**: AWS EC2 t2.micro (Mumbai Region)
- **IP**: 100.101.99.93 (Tailscale network)
- **Process**: `forensic_complete.py` (Active)
- **Port**: 8888 (Forensic API endpoint)
- **Integration**: Connected to 3-tier monitoring architecture

## 📊 Live Compliance Metrics

Current real-time scores from production monitoring:

| Standard | Score | Purpose |
|----------|-------|---------|
| **FDA 21 CFR Part 11** | 98.5% | Electronic records compliance (LIMS) |
| **SOX Section 404** | 97.2% | Financial controls (Trading system) |
| **GMP Guidelines** | 99.1% | Good Manufacturing Practices (Pharma) |

*Scores calculated from actual application logs and system metrics*

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AWS EC2 Instance                       │
│                  100.101.99.93:8888                      │
│                                                          │
│         forensic_complete.py (Evidence Collector)       │
│                        ↓                                 │
│              Compliance Calculation                      │
│                        ↓                                 │
│              Metrics Export (Prometheus format)         │
└─────────────────────────────────────────────────────────┘
                          ↓
                 Server 2 (192.168.50.74)
                 Prometheus + Grafana Stack
                          ↓
                 Server 1 (100.89.26.128)
                 Production Applications
```

## 🔬 Forensic Principles Applied

### Evidence Integrity
- SHA256 cryptographic hashing of system states
- Tamper detection through hash chain validation
- Immutable audit trail generation

### Chain of Custody
- Complete traceability from event to audit record
- Actor identification with timestamps
- Cryptographic signatures for non-repudiation

### Compliance Validation
- Automated checking against regulatory frameworks
- Real-time compliance percentage calculations
- Alert generation for policy violations

## 🛠️ Technical Implementation

### Core Components
- **Evidence Collector**: Python service monitoring infrastructure events
- **Compliance Engine**: Algorithms for regulatory scoring (FDA/SOX/GMP)
- **Audit Trail Generator**: Blockchain-style immutable records
- **Metrics Exporter**: Prometheus-compatible endpoint

### Technologies
- **Language**: Python 3.9
- **Deployment**: AWS EC2 (Tailscale networking)
- **Monitoring**: Integrated with Prometheus/Grafana stack
- **Hashing**: SHA256 cryptographic verification

## 📁 Repository Structure

```
digital-evidence-pipeline/
├── forensic_complete.py           # Main collector (RUNNING)
├── scripts/
│   ├── forensic_collector.py      # Full implementation
│   ├── forensic_api.py            # REST API endpoints
│   ├── compliance-metrics.py      # Scoring algorithms
│   └── storage_backend.py         # Evidence storage
├── docker/
│   ├── docker-compose-ec2.yml     # Container deployment
│   └── Dockerfile.forensic        # Image definition
├── kubernetes/
│   └── forensic-collector-daemonset.yaml
├── images/
│   ├── Prometheus-1.png           # Target monitoring
│   ├── Prometheus-2.png           # Cross-cloud integration
│   ├── Regulatory\ Compliance\ Scores-1.png  # Dashboard overview
│   └── Regulatory\ Compliance\ Scores-2.png  # Extended metrics
└── README.md
```

## 📈 Integration with Monitoring Stack

### Data Sources
- **LIMS Application**: Sample processing logs and metrics
- **Financial Trading**: Transaction monitoring and anomaly detection
- **Pharmaceutical**: Temperature sensors and environmental controls
- **Infrastructure**: System health and performance metrics

### Dashboard Integration
Connected to Grafana dashboards showing:
- Real-time compliance scores across regulatory frameworks
- Environmental monitoring (temperature violations: 0)
- Financial anomaly detection (trading anomalies: 0)  
- Chain of custody integrity (LIMS chain: 1.0)

## 🎯 Business Value for Regulated Industries

### Healthcare & Life Sciences
- **HIPAA Compliance**: Patient data handling audit trails
- **FDA 21 CFR Part 11**: Electronic records validation
- **Clinical Trial**: Complete documentation chain

### Financial Services
- **SOX Compliance**: Financial controls audit preparation
- **Risk Management**: Real-time anomaly detection
- **Regulatory Reporting**: Automated evidence collection

### Manufacturing & Pharma
- **GMP Validation**: Good Manufacturing Practices monitoring  
- **Quality Control**: Environmental condition tracking
- **Batch Records**: Complete production traceability

## 🚀 Deployment

### Current Production Environment
```bash
# System is actively running on EC2
# View metrics endpoint (internal access)
curl http://100.101.99.93:8888/metrics

# View compliance scores
curl http://100.101.99.93:8888/compliance
```

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/GABRIELS562/digital-evidence-pipeline.git
cd digital-evidence-pipeline

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run forensic collector
python3 forensic_complete.py
```

## 📊 Available Metrics

Prometheus-compatible metrics exposed at `/metrics`:

```
# Compliance scoring
forensic_compliance_score{standard="FDA"} 98.5
forensic_compliance_score{standard="SOX"} 97.2
forensic_compliance_score{standard="GMP"} 99.1

# Evidence collection
forensic_evidence_collected_total 
forensic_chain_blocks_total
forensic_anomalies_detected_total
```

## 🔗 Portfolio Context

Part of comprehensive DevOps portfolio demonstrating:

1. **[LIMS System](https://lims.jagdevops.co.za)** - Production DNA tracking
2. **[Zero-Downtime Pipeline](https://dashboard.jagdevops.co.za)** - GitOps deployment
3. **Digital Evidence Pipeline** - This forensic monitoring system

## 👨‍🔬 The Forensic Advantage

*"In forensics, evidence contamination means justice fails. In DevOps, system contamination means business fails. This project demonstrates how forensic rigor prevents both."*

### Why This Approach Matters

**Unique Differentiator**: Combines 15 years forensic science experience with DevOps  
**Compliance Ready**: Demonstrates understanding of regulatory requirements  
**Audit Friendly**: Shows capability to build audit-ready systems  
**Enterprise Focus**: Cryptographic proof and tamper detection

## 📸 Visual Documentation

See `images/` directory for:
- Prometheus monitoring integration screenshots
- Grafana compliance dashboard views
- Real-time metric visualization
- Cross-cloud architecture proof

## 📝 Important Notes

- This system monitors production applications with real data
- Compliance scores calculated from actual application logs
- Screenshots show genuine system metrics and dashboards
- All sensitive data sanitized for public documentation

## 📄 License

MIT License - See LICENSE file for details

---

**Author**: Jaime Gabriels  
**Background**: 15 years DNA Forensics | DevOps Engineer | AWS SAA | CKA  
**Concept**: "Where every deployment leaves evidence, and every evidence tells the compliance story"
