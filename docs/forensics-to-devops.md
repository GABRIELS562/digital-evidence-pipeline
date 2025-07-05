# From Forensics to DevOps: Skills Translation

This project demonstrates how core forensic science skills are directly applicable to DevOps and compliance engineering in regulated industries.

## Evidence Collection → Automated Audit Trails
- Forensic: Chain-of-custody, tamper-evident logs, and evidence preservation.
- DevOps: Ansible playbooks and auditd rules automate log collection, immutability, and secure storage (see `playbooks/pharma-compliance.yml`, `playbooks/finance-compliance.yml`).

## Investigation & Analysis → Compliance Scoring
- Forensic: Systematic analysis of evidence, risk assessment, and reporting.
- DevOps: Python scripts (`scripts/compliance-metrics.py`, `tests/validate_compliance_rules.py`) aggregate controls into compliance scores and risk metrics.

## Reporting → Executive Dashboards
- Forensic: Clear, actionable reporting for legal and business stakeholders.
- DevOps: Grafana dashboards (`dashboards/executive-compliance.json`) translate technical metrics into business value for executives.

## Quality Assurance → Automated Testing
- Forensic: Rigorous validation of evidence and procedures.
- DevOps: Molecule scenarios and integration scripts (`tests/`) ensure compliance controls are enforced and validated automatically.

## Example Workflow
1. **Playbook runs**: Enforces compliance controls and audit logging.
2. **Metrics collected**: Compliance monitor exposes forensic metrics to Prometheus.
3. **Dashboards update**: Executives see real-time compliance and risk posture.
4. **Automated tests**: Validate controls, scoring, and rule coverage for continuous assurance.

---
This approach bridges the gap between forensic rigor and DevOps automation, delivering measurable business value. 