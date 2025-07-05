#!/usr/bin/env python3
"""
Audit Tools for Compliance Automation
Provides utilities for audit trail analysis and compliance verification
"""

import json
import csv
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class AuditTools:
    def __init__(self):
        self.audit_data = []
    
    def load_audit_logs(self, log_file: str) -> None:
        """Load audit logs from file"""
        try:
            with open(log_file, 'r') as f:
                if log_file.endswith('.json'):
                    self.audit_data = json.load(f)
                elif log_file.endswith('.csv'):
                    reader = csv.DictReader(f)
                    self.audit_data = list(reader)
        except FileNotFoundError:
            print(f"Error: Audit log file {log_file} not found")
            sys.exit(1)
    
    def analyze_access_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze user access patterns"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        analysis = {
            'total_accesses': len(self.audit_data),
            'unique_users': len(set(entry.get('user_id', '') for entry in self.audit_data)),
            'access_by_hour': self._group_by_hour(),
            'failed_attempts': self._count_failed_attempts(),
            'suspicious_activities': self._detect_suspicious_activities()
        }
        
        return analysis
    
    def _group_by_hour(self) -> Dict[str, int]:
        """Group access attempts by hour"""
        hourly_access = {}
        for entry in self.audit_data:
            timestamp = entry.get('timestamp', '')
            if timestamp:
                hour = timestamp.split('T')[1].split(':')[0] if 'T' in timestamp else '00'
                hourly_access[hour] = hourly_access.get(hour, 0) + 1
        return hourly_access
    
    def _count_failed_attempts(self) -> int:
        """Count failed login attempts"""
        return sum(1 for entry in self.audit_data if entry.get('status') == 'failed')
    
    def _detect_suspicious_activities(self) -> List[Dict[str, Any]]:
        """Detect suspicious activities"""
        suspicious = []
        
        # Example: Multiple failed attempts from same user
        user_failures = {}
        for entry in self.audit_data:
            if entry.get('status') == 'failed':
                user_id = entry.get('user_id', '')
                user_failures[user_id] = user_failures.get(user_id, 0) + 1
        
        for user_id, count in user_failures.items():
            if count > 5:  # Threshold for suspicious activity
                suspicious.append({
                    'type': 'multiple_failed_attempts',
                    'user_id': user_id,
                    'count': count,
                    'severity': 'high'
                })
        
        return suspicious
    
    def generate_compliance_report(self, output_file: str = None) -> str:
        """Generate compliance audit report"""
        if not output_file:
            output_file = f"compliance_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        analysis = self.analyze_access_patterns()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'audit_summary': analysis,
            'compliance_status': self._assess_compliance_status(analysis),
            'recommendations': self._generate_recommendations(analysis)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file
    
    def _assess_compliance_status(self, analysis: Dict[str, Any]) -> str:
        """Assess overall compliance status"""
        failed_attempts = analysis.get('failed_attempts', 0)
        suspicious_count = len(analysis.get('suspicious_activities', []))
        
        if failed_attempts > 100 or suspicious_count > 10:
            return 'non_compliant'
        elif failed_attempts > 50 or suspicious_count > 5:
            return 'at_risk'
        else:
            return 'compliant'
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if analysis.get('failed_attempts', 0) > 50:
            recommendations.append("Review and strengthen authentication policies")
        
        if len(analysis.get('suspicious_activities', [])) > 5:
            recommendations.append("Investigate suspicious user activities")
        
        return recommendations

if __name__ == "__main__":
    tools = AuditTools()
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        tools.load_audit_logs(log_file)
        
        if len(sys.argv) > 2 and sys.argv[2] == '--report':
            report_file = tools.generate_compliance_report()
            print(f"Compliance report generated: {report_file}")
        else:
            analysis = tools.analyze_access_patterns()
            print(json.dumps(analysis, indent=2))
    else:
        print("Usage: python audit-tools.py <log_file> [--report]")