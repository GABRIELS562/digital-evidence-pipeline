#!/usr/bin/env python3
"""
Simplified LIMS Exporter with realistic mock data
Connects to existing LIMS data loops for FDA compliance metrics
"""
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import random
import math

# FDA 21 CFR Part 11 Compliance Metrics
lims_compliance_score = Gauge('lims_compliance_score', 'Overall FDA compliance score')
lims_electronic_signatures = Gauge('lims_electronic_signatures', 'Electronic signature validity')
lims_audit_trail = Gauge('lims_audit_trail', 'Audit trail completeness')
lims_data_integrity = Gauge('lims_data_integrity', 'Data integrity score')
lims_sample_processing = Histogram('lims_sample_processing_seconds', 'Sample processing time')
lims_validation_status = Gauge('lims_validation_status', 'System validation status')
lims_backup_status = Gauge('lims_backup_status', 'Backup compliance status')
lims_access_violations = Counter('lims_access_violations', 'Unauthorized access attempts')

# Performance Metrics
lims_active_samples = Gauge('lims_active_samples', 'Number of active samples')
lims_queue_length = Gauge('lims_queue_length', 'Sample queue length')
lims_api_latency = Histogram('lims_api_latency_ms', 'API response time in ms')

class MockLIMSData:
    def __init__(self):
        self.time_offset = 0
        self.violation_probability = 0.02  # 2% chance per check
        self.base_compliance = 92  # Base compliance score
        
    def generate_metrics(self):
        """Generate realistic LIMS metrics with natural variations"""
        self.time_offset += 1
        
        # Simulate daily compliance variations (peaks during business hours)
        hour_of_day = (self.time_offset // 120) % 24  # 30s intervals = 120 per hour
        business_hours = 9 <= hour_of_day <= 17
        
        # FDA Compliance Metrics (higher during business hours)
        compliance_modifier = 5 if business_hours else -3
        compliance = min(100, max(75, self.base_compliance + compliance_modifier + random.uniform(-3, 3)))
        lims_compliance_score.set(compliance)
        
        # Electronic signatures (mostly valid, occasional issues)
        sig_valid = 0 if random.random() < 0.01 else 1  # 1% failure rate
        lims_electronic_signatures.set(sig_valid)
        
        # Audit trail (very reliable)
        audit_complete = 0 if random.random() < 0.001 else 1  # 0.1% failure rate
        lims_audit_trail.set(audit_complete)
        
        # Data integrity (fluctuates based on system load)
        load_factor = 1.2 if business_hours else 0.8
        integrity = min(100, max(85, 95 + random.uniform(-5, 5) * load_factor))
        lims_data_integrity.set(integrity)
        
        # Sample processing time (slower during peak hours)
        base_time = 45 if business_hours else 30
        processing_time = max(10, base_time + random.uniform(-10, 20))
        lims_sample_processing.observe(processing_time)
        
        # System validation (changes rarely)
        if random.random() < 0.0001:  # Very rare status change
            lims_validation_status.set(0)
        else:
            lims_validation_status.set(1)
        
        # Backup status (runs at night)
        backup_good = 1 if hour_of_day < 6 or hour_of_day > 22 else random.choice([0, 1])
        lims_backup_status.set(backup_good)
        
        # Access violations (more during off-hours)
        if not business_hours and random.random() < 0.05:
            lims_access_violations.inc()
        
        # Performance metrics
        active_samples = 150 + int(50 * math.sin(self.time_offset / 100)) + random.randint(-10, 10)
        lims_active_samples.set(max(0, active_samples))
        
        queue_length = 20 + int(15 * math.cos(self.time_offset / 80)) + random.randint(-5, 5)
        lims_queue_length.set(max(0, queue_length))
        
        # API latency (increases with load)
        base_latency = 15 if business_hours else 8
        latency = max(5, base_latency + random.uniform(-3, 10))
        lims_api_latency.observe(latency)
        
        # Print status for debugging
        print(f"LIMS Metrics - Compliance: {compliance:.1f}%, Samples: {active_samples}, Queue: {queue_length}")

def main():
    # Start Prometheus metrics server
    port = 9101
    start_http_server(port)
    print(f"LIMS Mock Exporter serving metrics on :{port}/metrics")
    
    # Initialize mock data generator
    mock_data = MockLIMSData()
    
    # Generate metrics every 30 seconds
    while True:
        mock_data.generate_metrics()
        time.sleep(30)

if __name__ == "__main__":
    main()