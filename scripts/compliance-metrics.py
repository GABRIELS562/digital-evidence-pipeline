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
    # Check for audit log files in expected locations
    audit_paths = [
        '/var/log/audit/audit.log',
        '/var/log/auth.log', 
        '/var/log/syslog'
    ]
    
    missing_logs = 0
    for path in audit_paths:
        if not os.path.exists(path):
            missing_logs += 1
    
    # Return 1 if most logs are present, 0 if significant gaps
    completeness = 1 - (missing_logs / len(audit_paths))
    return 1 if completeness > 0.7 else 0

def check_security_policy_violations():
    """Return 1 if violations detected, else 0."""
    # Check common security violation indicators
    violation_indicators = [
        'failed password',
        'authentication failure', 
        'invalid user',
        'root login',
        'sudo command'
    ]
    
    # Check recent auth logs for violations
    auth_log_path = '/var/log/auth.log'
    if os.path.exists(auth_log_path):
        try:
            with open(auth_log_path, 'r') as f:
                recent_logs = f.readlines()[-100:]  # Last 100 lines
                for line in recent_logs:
                    for indicator in violation_indicators:
                        if indicator in line.lower():
                            return 1
        except (IOError, OSError):
            pass
    
    # If no logs accessible, use fallback simulation
    return 1 if random.random() > 0.8 else 0

def check_risk_level():
    """Return a risk score (0-10)."""
    # Calculate risk based on system indicators
    risk_factors = []
    
    # Check system load (higher load = higher risk)
    try:
        load_avg = os.getloadavg()[0]  # 1-minute load average
        cpu_count = os.cpu_count() or 1
        cpu_usage = min(load_avg / cpu_count, 1.0)
        risk_factors.append(cpu_usage * 3)  # 0-3 risk points
    except (OSError, AttributeError):
        risk_factors.append(1)  # Default moderate risk
    
    # Check disk usage (higher usage = higher risk)  
    try:
        disk_usage = os.statvfs('/').f_bavail / os.statvfs('/').f_blocks
        disk_risk = (1 - disk_usage) * 4  # 0-4 risk points
        risk_factors.append(disk_risk)
    except (OSError, AttributeError):
        risk_factors.append(2)  # Default moderate risk
    
    # Check recent failed logins (security risk)
    auth_failures = check_security_policy_violations()
    risk_factors.append(auth_failures * 3)  # 0-3 risk points
    
    # Calculate total risk (0-10)
    total_risk = sum(risk_factors)
    return min(int(total_risk), 10)

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