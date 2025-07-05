#!/usr/bin/env python3
"""
compliance-metrics.py
Collects and exposes custom compliance metrics for Prometheus, demonstrating how forensic investigation principles apply to automated compliance monitoring.
"""

from prometheus_client import start_http_server, Gauge, Counter
import time
import random
import os

# --- Metric Definitions ---
# Compliance score (0-100%)
compliance_score = Gauge('compliance_score', 'Overall compliance score as a percentage (0-100)')

# Audit trail completeness (1 = complete, 0 = incomplete)
audit_trail_complete = Gauge('audit_trail_complete', 'Audit trail completeness (1=complete, 0=incomplete)')

# Security policy violations (counter)
security_policy_violations = Counter('security_policy_violations', 'Number of detected security policy violations')

# Risk assessment score (0-10, higher = more risk)
risk_assessment_score = Gauge('risk_assessment_score', 'Risk assessment score (0=low risk, 10=high risk)')

# --- Forensic Investigation Principles ---
# - Audit trail completeness: Ensures all critical events are logged and available for investigation.
# - Security policy violations: Tracks events that may indicate non-compliance or malicious activity.
# - Compliance score: Aggregates multiple controls into a single, business-relevant metric.
# - Risk assessment: Quantifies risk based on findings, supporting proactive mitigation.

# --- Example Data Collection Functions ---
def calculate_compliance_score():
    """Aggregate compliance controls into a single score (0-100)."""
    # In a real system, this would check multiple controls, e.g. password policy, encryption, access logs, etc.
    controls = [
        check_audit_trail(),
        1 - check_security_policy_violations(),
        1 - check_risk_level()/10
    ]
    score = sum(controls) / len(controls) * 100
    return max(0, min(100, score))

def check_audit_trail():
    """Check if audit trail is complete (1) or incomplete (0)."""
    # For demonstration, randomly simulate completeness
    # In production, check for missing log files, gaps, or tampering
    return 1 if random.random() > 0.1 else 0

def check_security_policy_violations():
    """Return 1 if violations detected, else 0."""
    # In production, scan logs/configs for violations
    return 1 if random.random() > 0.8 else 0

def check_risk_level():
    """Return a risk score (0-10)."""
    # In production, aggregate findings, vulnerabilities, incidents
    return random.randint(0, 10)

# --- Main Metrics Collection Loop ---
def main():
    # Start Prometheus metrics server
    start_http_server(8000)
    print("Serving compliance metrics on :8000/metrics")
    while True:
        # Compliance score
        score = calculate_compliance_score()
        compliance_score.set(score)

        # Audit trail completeness
        audit_complete = check_audit_trail()
        audit_trail_complete.set(audit_complete)

        # Security policy violations
        violations = check_security_policy_violations()
        if violations:
            security_policy_violations.inc()

        # Risk assessment
        risk = check_risk_level()
        risk_assessment_score.set(risk)

        # Forensic principle: log each metric update (in real system, write to secure log)
        print(f"Compliance Score: {score:.1f}% | Audit Trail: {'Complete' if audit_complete else 'Incomplete'} | Violations: {violations} | Risk: {risk}")

        time.sleep(30)

if __name__ == "__main__":
    main()