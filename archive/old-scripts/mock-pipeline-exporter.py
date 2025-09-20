#!/usr/bin/env python3
"""
Simplified Pipeline Exporter with realistic mock data
Simulates zero-downtime deployment metrics for Jenkins/ArgoCD
"""
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import random
import math

# Deployment Metrics
pipeline_deployment_success = Gauge('pipeline_deployment_success_rate', 'Deployment success rate %')
pipeline_canary_progress = Gauge('pipeline_canary_progress', 'Canary rollout progress %')
pipeline_blue_green_active = Gauge('pipeline_blue_green_active', 'Active env (0=blue, 1=green)')
pipeline_rollback_total = Counter('pipeline_rollback_total', 'Total rollbacks')
pipeline_deployment_duration = Histogram('pipeline_deployment_duration_seconds', 'Deploy duration')

# Health Check Metrics (Critical for sub-50ms requirement)
pipeline_health_latency = Histogram('pipeline_health_latency_ms', 'Health check latency')
pipeline_health_success = Gauge('pipeline_health_success_rate', 'Health check success %')
pipeline_sub50ms_rate = Gauge('pipeline_sub50ms_rate', 'Checks under 50ms %')

# CI/CD Pipeline Metrics
pipeline_builds_total = Counter('pipeline_builds_total', 'Total builds')
pipeline_builds_failed = Counter('pipeline_builds_failed', 'Failed builds')
pipeline_test_coverage = Gauge('pipeline_test_coverage', 'Test coverage %')
pipeline_security_score = Gauge('pipeline_security_score', 'Security scan score')

# Application-specific metrics
pipeline_finance_app_health = Gauge('pipeline_finance_app_health', 'Finance app health')
pipeline_pharma_app_health = Gauge('pipeline_pharma_app_health', 'Pharma app health')

class MockPipelineData:
    def __init__(self):
        self.time_offset = 0
        self.current_canary = 0
        self.canary_direction = 1  # 1 = rolling out, -1 = rolling back
        self.blue_green_state = 0  # 0 = blue, 1 = green
        self.last_deployment = 0
        self.deployment_interval = 240  # Deploy every 2 hours (240 * 30s)
        
    def simulate_deployment(self):
        """Simulate a deployment event"""
        deployment_type = random.choice(['canary', 'blue-green', 'rolling'])
        
        if deployment_type == 'canary':
            # Start canary rollout
            self.current_canary = 10
            self.canary_direction = 1
            print(f"Starting canary deployment...")
            
        elif deployment_type == 'blue-green':
            # Switch blue-green
            self.blue_green_state = 1 - self.blue_green_state
            print(f"Switching to {'green' if self.blue_green_state else 'blue'} environment")
            
        # Deployment duration (30-300 seconds)
        duration = random.uniform(30, 300)
        pipeline_deployment_duration.observe(duration)
        
        # Success/failure (90% success rate)
        if random.random() < 0.9:
            pipeline_builds_total.inc()
            return True
        else:
            pipeline_builds_total.inc()
            pipeline_builds_failed.inc()
            pipeline_rollback_total.inc()
            return False
    
    def generate_health_metrics(self):
        """Generate health check metrics focusing on sub-50ms requirement"""
        
        # Simulate 10 health checks
        latencies = []
        for _ in range(10):
            # Most checks are fast (20-40ms), some are slower
            if random.random() < 0.85:  # 85% are fast
                latency = random.uniform(20, 45)
            else:  # 15% are slower
                latency = random.uniform(50, 150)
            
            latencies.append(latency)
            pipeline_health_latency.observe(latency)
        
        # Calculate sub-50ms percentage
        under_50 = sum(1 for l in latencies if l < 50) / len(latencies) * 100
        pipeline_sub50ms_rate.set(under_50)
        
        # Health success rate (usually high)
        health_success = min(100, max(95, 98 + random.uniform(-2, 2)))
        pipeline_health_success.set(health_success)
        
        return under_50
    
    def generate_metrics(self):
        """Generate all pipeline metrics"""
        self.time_offset += 1
        
        # Check if it's time for a deployment
        if self.time_offset - self.last_deployment >= self.deployment_interval:
            success = self.simulate_deployment()
            self.last_deployment = self.time_offset
            
            # Update success rate
            success_rate = 90 + random.uniform(-5, 5) if success else 70 + random.uniform(-5, 5)
            pipeline_deployment_success.set(success_rate)
        
        # Update canary progress
        if self.current_canary > 0:
            if self.canary_direction == 1:
                # Rolling out
                self.current_canary = min(100, self.current_canary + random.uniform(5, 15))
                if self.current_canary >= 100:
                    self.current_canary = 0  # Complete
                    print("Canary deployment completed")
            else:
                # Rolling back
                self.current_canary = max(0, self.current_canary - random.uniform(10, 20))
                if self.current_canary <= 0:
                    print("Canary rollback completed")
                    
            pipeline_canary_progress.set(self.current_canary)
        
        # Blue-green state
        pipeline_blue_green_active.set(self.blue_green_state)
        
        # Generate health metrics
        sub50_rate = self.generate_health_metrics()
        
        # Test coverage (relatively stable)
        coverage = min(95, max(75, 85 + random.uniform(-2, 2)))
        pipeline_test_coverage.set(coverage)
        
        # Security score (changes slowly)
        security = min(100, max(70, 88 + random.uniform(-1, 1)))
        pipeline_security_score.set(security)
        
        # App health scores
        finance_health = min(100, max(90, 95 + random.uniform(-3, 3)))
        pharma_health = min(100, max(88, 94 + random.uniform(-3, 3)))
        pipeline_finance_app_health.set(finance_health)
        pipeline_pharma_app_health.set(pharma_health)
        
        # Print status
        print(f"Pipeline - Sub50ms: {sub50_rate:.1f}%, Canary: {self.current_canary}%, "
              f"Env: {'green' if self.blue_green_state else 'blue'}")

def main():
    # Start Prometheus metrics server
    port = 9102
    start_http_server(port)
    print(f"Pipeline Mock Exporter serving metrics on :{port}/metrics")
    
    # Initialize mock data generator
    mock_data = MockPipelineData()
    
    # Generate metrics every 30 seconds
    while True:
        mock_data.generate_metrics()
        time.sleep(30)

if __name__ == "__main__":
    main()