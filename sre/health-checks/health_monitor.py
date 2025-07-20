#!/usr/bin/env python3
"""
SRE HEALTH CHECK IMPLEMENTATION
===============================

This module demonstrates fundamental SRE health monitoring practices:

SRE CONCEPTS DEMONSTRATED:
- Deep Health Checks: Beyond simple "up/down" status
- Dependency Health: Monitor upstream/downstream services  
- Health Check Hierarchy: Different levels of health validation
- Graceful Degradation: Service behavior when dependencies fail
- Circuit Breaker Pattern: Prevent cascading failures

HEALTH CHECK TYPES:
1. Liveness: Is the service running?
2. Readiness: Can the service handle requests?
3. Startup: Is the service fully initialized?
4. Deep: Are all dependencies healthy?
"""

import json
import time
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# SRE PRACTICE: Structured logging for better observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """SRE PRACTICE: Standardized health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """SRE PRACTICE: Structured health check results"""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: str
    details: Optional[Dict] = None

class SREHealthMonitor:
    """
    SRE Health Monitor implementing industry best practices
    
    SRE PRINCIPLES:
    - Monitor what matters for user experience
    - Fail fast and provide clear status
    - Enable automated recovery decisions
    - Provide actionable diagnostic information
    """
    
    def __init__(self, config_path: str = "/app/config/health_config.json"):
        self.config = self._load_config(config_path)
        self.circuit_breakers = {}
        self.startup_time = datetime.now()
        
        # SRE PRACTICE: Initialize health check registry
        self.health_checks = {
            'liveness': self._liveness_check,
            'readiness': self._readiness_check, 
            'startup': self._startup_check,
            'deep': self._deep_health_check
        }
        
    def _load_config(self, config_path: str) -> Dict:
        """Load health check configuration"""
        default_config = {
            "startup_timeout_seconds": 60,
            "dependency_timeout_seconds": 5,
            "circuit_breaker_threshold": 5,
            "circuit_breaker_reset_timeout": 30,
            "dependencies": {
                "database": {"url": "postgresql://localhost:5432/compliance", "critical": True},
                "prometheus": {"url": "http://prometheus:9090/-/healthy", "critical": True},
                "grafana": {"url": "http://grafana:3000/api/health", "critical": False},
                "external_api": {"url": "https://api.external.com/health", "critical": False}
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return default_config

    def _liveness_check(self) -> HealthCheck:
        """
        SRE LIVENESS CHECK
        ==================
        Answers: "Is the service running?"
        
        Used by: Kubernetes liveness probes, load balancers
        Criteria: Basic service functionality (process alive, can respond)
        """
        start_time = time.time()
        
        try:
            # SRE PRACTICE: Simple check that service can respond
            current_time = datetime.now().isoformat()
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="liveness",
                status=HealthStatus.HEALTHY,
                message="Service is alive and responding",
                response_time_ms=response_time,
                timestamp=current_time,
                details={
                    "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
                    "process_id": "12345",  # In real implementation: os.getpid()
                    "version": "1.0.0"
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="liveness",
                status=HealthStatus.UNHEALTHY,
                message=f"Liveness check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _readiness_check(self) -> HealthCheck:
        """
        SRE READINESS CHECK
        ===================
        Answers: "Can the service handle requests?"
        
        Used by: Kubernetes readiness probes, traffic routing
        Criteria: Service ready to accept traffic (initialized, dependencies available)
        """
        start_time = time.time()
        
        try:
            # SRE PRACTICE: Check critical dependencies for readiness
            critical_deps_healthy = True
            dependency_details = {}
            
            for dep_name, dep_config in self.config["dependencies"].items():
                if dep_config["critical"]:
                    dep_health = self._check_dependency(dep_name, dep_config)
                    dependency_details[dep_name] = {
                        "status": dep_health.status.value,
                        "response_time_ms": dep_health.response_time_ms
                    }
                    
                    if dep_health.status != HealthStatus.HEALTHY:
                        critical_deps_healthy = False
                        
            response_time = (time.time() - start_time) * 1000
            
            if critical_deps_healthy:
                return HealthCheck(
                    name="readiness",
                    status=HealthStatus.HEALTHY,
                    message="Service is ready to handle requests",
                    response_time_ms=response_time,
                    timestamp=datetime.now().isoformat(),
                    details={
                        "critical_dependencies": dependency_details,
                        "configuration_loaded": True,
                        "database_connected": True
                    }
                )
            else:
                return HealthCheck(
                    name="readiness",
                    status=HealthStatus.UNHEALTHY,
                    message="Critical dependencies not available",
                    response_time_ms=response_time,
                    timestamp=datetime.now().isoformat(),
                    details=dependency_details
                )
                
        except Exception as e:
            return HealthCheck(
                name="readiness",
                status=HealthStatus.UNHEALTHY,
                message=f"Readiness check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _startup_check(self) -> HealthCheck:
        """
        SRE STARTUP CHECK  
        ==================
        Answers: "Has the service completed initialization?"
        
        Used by: Kubernetes startup probes, deployment validation
        Criteria: Service fully initialized (config loaded, migrations complete, etc.)
        """
        start_time = time.time()
        
        try:
            uptime = (datetime.now() - self.startup_time).total_seconds()
            startup_timeout = self.config["startup_timeout_seconds"]
            
            # SRE PRACTICE: Allow time for full initialization
            if uptime < startup_timeout:
                initialization_steps = {
                    "configuration_loaded": uptime > 5,
                    "database_migrations": uptime > 15,
                    "cache_warmed": uptime > 30,
                    "metrics_initialized": uptime > 10
                }
                
                all_initialized = all(initialization_steps.values())
                
                status = HealthStatus.HEALTHY if all_initialized else HealthStatus.DEGRADED
                message = "Startup complete" if all_initialized else "Startup in progress"
                
                return HealthCheck(
                    name="startup",
                    status=status,
                    message=message,
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now().isoformat(),
                    details={
                        "uptime_seconds": uptime,
                        "initialization_steps": initialization_steps,
                        "startup_timeout_seconds": startup_timeout
                    }
                )
            else:
                return HealthCheck(
                    name="startup",
                    status=HealthStatus.HEALTHY,
                    message="Service startup completed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now().isoformat(),
                    details={"uptime_seconds": uptime}
                )
                
        except Exception as e:
            return HealthCheck(
                name="startup",
                status=HealthStatus.UNHEALTHY,
                message=f"Startup check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _deep_health_check(self) -> HealthCheck:
        """
        SRE DEEP HEALTH CHECK
        =====================
        Answers: "Are all components and dependencies healthy?"
        
        Used by: Detailed monitoring, capacity planning, troubleshooting
        Criteria: Comprehensive system health (all deps, performance, resources)
        """
        start_time = time.time()
        
        try:
            dependency_results = {}
            overall_status = HealthStatus.HEALTHY
            critical_issues = []
            warnings = []
            
            # SRE PRACTICE: Check all dependencies with circuit breaker logic
            for dep_name, dep_config in self.config["dependencies"].items():
                dep_health = self._check_dependency_with_circuit_breaker(dep_name, dep_config)
                dependency_results[dep_name] = {
                    "status": dep_health.status.value,
                    "message": dep_health.message,
                    "response_time_ms": dep_health.response_time_ms,
                    "critical": dep_config["critical"]
                }
                
                if dep_health.status == HealthStatus.UNHEALTHY:
                    if dep_config["critical"]:
                        overall_status = HealthStatus.UNHEALTHY
                        critical_issues.append(f"{dep_name}: {dep_health.message}")
                    else:
                        warnings.append(f"{dep_name}: {dep_health.message}")
                        if overall_status == HealthStatus.HEALTHY:
                            overall_status = HealthStatus.DEGRADED
            
            # SRE PRACTICE: Resource utilization checks
            resource_health = self._check_resource_utilization()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="deep",
                status=overall_status,
                message=self._format_health_message(overall_status, critical_issues, warnings),
                response_time_ms=response_time,
                timestamp=datetime.now().isoformat(),
                details={
                    "dependencies": dependency_results,
                    "resources": resource_health,
                    "critical_issues": critical_issues,
                    "warnings": warnings,
                    "circuit_breakers": {name: cb["state"] for name, cb in self.circuit_breakers.items()}
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="deep",
                status=HealthStatus.UNHEALTHY,
                message=f"Deep health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _check_dependency(self, name: str, config: Dict) -> HealthCheck:
        """Check individual dependency health"""
        start_time = time.time()
        
        try:
            # SRE PRACTICE: Timeout protection for dependency checks
            timeout = self.config["dependency_timeout_seconds"]
            
            if "postgresql://" in config["url"]:
                # Database health check
                status = self._check_database_health(config["url"])
            else:
                # HTTP endpoint health check
                response = requests.get(config["url"], timeout=timeout)
                status = HealthStatus.HEALTHY if response.status_code == 200 else HealthStatus.UNHEALTHY
                
            return HealthCheck(
                name=name,
                status=status,
                message="Dependency healthy" if status == HealthStatus.HEALTHY else "Dependency unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )
            
        except requests.exceptions.Timeout:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Dependency timeout after {timeout}s",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Dependency check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _check_dependency_with_circuit_breaker(self, name: str, config: Dict) -> HealthCheck:
        """
        SRE CIRCUIT BREAKER PATTERN
        ============================
        Prevent cascading failures by "breaking" calls to unhealthy dependencies
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = {
                "state": "closed",  # closed, open, half-open
                "failure_count": 0,
                "last_failure_time": None,
                "threshold": self.config["circuit_breaker_threshold"]
            }
            
        cb = self.circuit_breakers[name]
        
        # SRE PRACTICE: Check circuit breaker state
        if cb["state"] == "open":
            reset_timeout = self.config["circuit_breaker_reset_timeout"]
            if cb["last_failure_time"] and \
               (datetime.now() - cb["last_failure_time"]).total_seconds() > reset_timeout:
                cb["state"] = "half-open"
                logger.info(f"Circuit breaker for {name} moved to half-open state")
            else:
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message="Circuit breaker OPEN - dependency bypassed",
                    response_time_ms=0,
                    timestamp=datetime.now().isoformat()
                )
        
        # Attempt dependency check
        health_result = self._check_dependency(name, config)
        
        # SRE PRACTICE: Update circuit breaker based on result
        if health_result.status == HealthStatus.HEALTHY:
            cb["failure_count"] = 0
            if cb["state"] == "half-open":
                cb["state"] = "closed"
                logger.info(f"Circuit breaker for {name} closed after successful check")
        else:
            cb["failure_count"] += 1
            cb["last_failure_time"] = datetime.now()
            
            if cb["failure_count"] >= cb["threshold"]:
                cb["state"] = "open"
                logger.warning(f"Circuit breaker for {name} opened after {cb['failure_count']} failures")
                
        return health_result

    def _check_database_health(self, db_url: str) -> HealthStatus:
        """Check database connectivity and basic operations"""
        try:
            # SRE PRACTICE: Minimal database health check
            # In real implementation, use proper database driver
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY

    def _check_resource_utilization(self) -> Dict:
        """
        SRE PRACTICE: Monitor resource saturation
        """
        return {
            "cpu_usage_percent": 45.2,  # In real implementation: psutil.cpu_percent()
            "memory_usage_percent": 67.8,  # In real implementation: psutil.virtual_memory().percent
            "disk_usage_percent": 23.1,  # In real implementation: psutil.disk_usage('/').percent
            "open_file_descriptors": 1234,  # In real implementation: len(psutil.Process().open_files())
            "thread_count": 45  # In real implementation: psutil.Process().num_threads()
        }

    def _format_health_message(self, status: HealthStatus, critical_issues: List[str], warnings: List[str]) -> str:
        """Format human-readable health status message"""
        if status == HealthStatus.HEALTHY:
            return "All systems healthy"
        elif status == HealthStatus.DEGRADED:
            return f"Service degraded: {len(warnings)} non-critical issues"
        else:
            return f"Service unhealthy: {len(critical_issues)} critical issues"

    def get_health_status(self, check_type: str = "readiness") -> Dict:
        """
        SRE PUBLIC API: Get health status for specified check type
        
        Args:
            check_type: One of 'liveness', 'readiness', 'startup', 'deep'
            
        Returns:
            Dict with health check results
        """
        if check_type not in self.health_checks:
            return {
                "error": f"Unknown health check type: {check_type}",
                "available_types": list(self.health_checks.keys())
            }
            
        health_check = self.health_checks[check_type]()
        
        return {
            "status": health_check.status.value,
            "message": health_check.message,
            "timestamp": health_check.timestamp,
            "response_time_ms": health_check.response_time_ms,
            "details": health_check.details or {}
        }

# SRE USAGE EXAMPLES
if __name__ == "__main__":
    """
    SRE IMPLEMENTATION EXAMPLES
    ===========================
    """
    
    # Initialize health monitor
    monitor = SREHealthMonitor()
    
    # Example: Kubernetes liveness probe endpoint
    print("=== LIVENESS CHECK (Kubernetes probe) ===")
    liveness = monitor.get_health_status("liveness")
    print(json.dumps(liveness, indent=2))
    
    # Example: Load balancer readiness check
    print("\n=== READINESS CHECK (Load balancer) ===") 
    readiness = monitor.get_health_status("readiness")
    print(json.dumps(readiness, indent=2))
    
    # Example: Deep health for monitoring dashboard
    print("\n=== DEEP HEALTH CHECK (Monitoring) ===")
    deep_health = monitor.get_health_status("deep")
    print(json.dumps(deep_health, indent=2))