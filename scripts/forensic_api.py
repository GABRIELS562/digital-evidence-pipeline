#!/usr/bin/env python3
"""
Forensic Evidence API Server
Provides webhook endpoint for Alertmanager and web interface for evidence viewing
"""

from flask import Flask, request, jsonify, render_template_string
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import threading
import time
from forensic_collector import ForensicEvidenceCollector

app = Flask(__name__)

# Prometheus metrics
incident_counter = Counter('forensic_incidents_total', 'Total forensic incidents captured', ['type', 'app'])
evidence_size = Gauge('forensic_evidence_size_bytes', 'Size of forensic evidence stored')
capture_duration = Histogram('forensic_capture_duration_seconds', 'Time to capture evidence')
chain_integrity = Gauge('forensic_chain_integrity', 'Chain of custody integrity status')

# Initialize collector
collector = ForensicEvidenceCollector()

# HTML template for web interface
EVIDENCE_VIEWER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Forensic Evidence Chain Viewer</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
        h1 { color: #0ff; text-shadow: 0 0 10px #0ff; }
        .incident { border: 1px solid #0f0; padding: 10px; margin: 10px 0; background: #0a0a0a; }
        .verified { color: #0f0; }
        .tampered { color: #f00; font-weight: bold; }
        .hash { font-size: 0.8em; color: #888; word-break: break-all; }
        .timestamp { color: #ff0; }
        .type { color: #f0f; }
        button { background: #0f0; color: #000; border: none; padding: 5px 10px; cursor: pointer; }
        button:hover { background: #0ff; }
        .stats { background: #111; padding: 10px; margin: 20px 0; border-left: 3px solid #0ff; }
    </style>
</head>
<body>
    <h1>🔬 Forensic Evidence Chain Viewer</h1>
    <div class="stats">
        <h2>System Statistics</h2>
        <p>Total Incidents: {{ stats.total }}</p>
        <p>Verified: {{ stats.verified }}</p>
        <p>Chain Integrity: {{ stats.integrity }}%</p>
        <p>Evidence Size: {{ stats.size_mb }} MB</p>
    </div>
    
    <h2>Recent Incidents</h2>
    {% for incident in incidents %}
    <div class="incident">
        <div><span class="timestamp">{{ incident.timestamp }}</span></div>
        <div>ID: {{ incident.id }}</div>
        <div>Type: <span class="type">{{ incident.type }}</span></div>
        <div>App: {{ incident.app }}</div>
        <div class="hash">Hash: {{ incident.hash }}</div>
        <div class="hash">Previous: {{ incident.previous_hash[:16] }}...</div>
        <div>
            Status: 
            {% if incident.verified %}
                <span class="verified">✓ VERIFIED - Admissible for audit</span>
            {% else %}
                <span class="tampered">✗ TAMPERED - NOT admissible!</span>
            {% endif %}
        </div>
        <button onclick="window.location.href='/evidence/{{ incident.id }}'">View Evidence</button>
        <button onclick="verifyIncident('{{ incident.id }}')">Verify Integrity</button>
    </div>
    {% endfor %}
    
    <script>
        function verifyIncident(id) {
            fetch('/verify/' + id)
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                });
        }
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/incident', methods=['POST'])
def webhook_incident():
    """Webhook endpoint for Alertmanager"""
    start_time = time.time()
    
    try:
        data = request.json
        alerts = data.get('alerts', [])
        
        for alert in alerts:
            # Extract alert details
            alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
            severity = alert.get('labels', {}).get('severity', 'warning')
            app_name = alert.get('labels', {}).get('app', 'system')
            description = alert.get('annotations', {}).get('description', 'No description')
            
            # Determine incident type based on alert
            incident_type = 'ALERT_' + severity.upper()
            
            # Capture forensic evidence
            print(f"[API] Received alert: {alert_name} for {app_name}")
            incident_id = collector.capture_incident(
                incident_type=incident_type,
                description=f"{alert_name}: {description}"
            )
            
            # Update metrics
            incident_counter.labels(type=incident_type, app=app_name).inc()
            
        capture_duration.observe(time.time() - start_time)
        return jsonify({'status': 'captured', 'count': len(alerts)}), 200
        
    except Exception as e:
        print(f"[API] Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def evidence_viewer():
    """Web interface for viewing evidence chain"""
    try:
        # Get recent incidents from database
        db = sqlite3.connect('/var/forensics/chain_of_custody.db')
        cursor = db.execute("""
            SELECT incident_id, timestamp, incident_type, evidence_hash, 
                   previous_hash, verified 
            FROM evidence 
            ORDER BY id DESC 
            LIMIT 20
        """)
        
        incidents = []
        for row in cursor.fetchall():
            # Extract app name from incident_id if possible
            app_name = 'system'
            if 'LIMS' in row[2]:
                app_name = 'LIMS'
            elif 'FINANCE' in row[2]:
                app_name = 'Finance'
            elif 'PHARMA' in row[2]:
                app_name = 'Pharma'
            elif 'JENKINS' in row[2]:
                app_name = 'Jenkins'
            elif 'ARGOCD' in row[2]:
                app_name = 'ArgoCD'
            
            incidents.append({
                'id': row[0],
                'timestamp': row[1],
                'type': row[2],
                'hash': row[3],
                'previous_hash': row[4],
                'verified': row[5],
                'app': app_name
            })
        
        # Calculate statistics
        total_count = db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        verified_count = db.execute("SELECT COUNT(*) FROM evidence WHERE verified=1").fetchone()[0]
        
        # Calculate evidence size
        evidence_path = Path('/var/forensics/evidence')
        total_size = sum(f.stat().st_size for f in evidence_path.rglob('*') if f.is_file())
        
        stats = {
            'total': total_count,
            'verified': verified_count,
            'integrity': round((verified_count / total_count * 100) if total_count > 0 else 100, 2),
            'size_mb': round(total_size / 1024 / 1024, 2)
        }
        
        # Update metrics
        evidence_size.set(total_size)
        chain_integrity.set(stats['integrity'])
        
        return render_template_string(EVIDENCE_VIEWER_HTML, incidents=incidents, stats=stats)
        
    except Exception as e:
        return f"Error loading evidence: {e}", 500

@app.route('/evidence/<incident_id>')
def view_evidence(incident_id):
    """View detailed evidence for a specific incident"""
    try:
        evidence_file = Path(f'/var/forensics/evidence/{incident_id}/evidence.json')
        report_file = Path(f'/var/forensics/evidence/{incident_id}/incident_report.txt')
        
        if evidence_file.exists():
            with open(evidence_file) as f:
                evidence = json.load(f)
            
            report = ""
            if report_file.exists():
                with open(report_file) as f:
                    report = f.read()
            
            # Create detailed view
            html = f"""
            <html>
            <head>
                <title>Evidence: {incident_id}</title>
                <style>
                    body {{ font-family: monospace; background: #000; color: #0f0; padding: 20px; }}
                    pre {{ background: #111; padding: 10px; overflow: auto; }}
                    .section {{ margin: 20px 0; }}
                    h2 {{ color: #0ff; }}
                    a {{ color: #ff0; }}
                </style>
            </head>
            <body>
                <h1>Forensic Evidence: {incident_id}</h1>
                <a href="/">← Back to Chain</a>
                
                <div class="section">
                    <h2>Incident Report</h2>
                    <pre>{report}</pre>
                </div>
                
                <div class="section">
                    <h2>Raw Evidence (JSON)</h2>
                    <pre>{json.dumps(evidence, indent=2)}</pre>
                </div>
                
                <div class="section">
                    <a href="/download/{incident_id}">Download Evidence Package</a>
                </div>
            </body>
            </html>
            """
            return html
        else:
            return "Evidence not found", 404
            
    except Exception as e:
        return f"Error viewing evidence: {e}", 500

@app.route('/verify/<incident_id>')
def verify_incident(incident_id):
    """Verify evidence integrity"""
    valid, message = collector.verify_evidence(incident_id)
    return jsonify({'valid': valid, 'message': message})

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.route('/trigger/<app_name>')
def trigger_demo(app_name):
    """Manual trigger for demo purposes"""
    incident_types = {
        'lims': ('FDA_COMPLIANCE_VIOLATION', 'LIMS audit trail gap detected'),
        'finance': ('SOX_VIOLATION', 'Finance app unauthorized access attempt'),
        'pharma': ('GMP_VIOLATION', 'Pharma batch record modification'),
        'jenkins': ('CI_FAILURE', 'Jenkins build failed with security scan errors'),
        'argocd': ('CD_FAILURE', 'ArgoCD sync failed - configuration drift detected')
    }
    
    if app_name in incident_types:
        incident_type, description = incident_types[app_name]
        incident_id = collector.capture_incident(incident_type, description)
        incident_counter.labels(type=incident_type, app=app_name).inc()
        return jsonify({
            'triggered': True, 
            'incident_id': incident_id,
            'app': app_name,
            'type': incident_type
        })
    else:
        return jsonify({'error': 'Unknown app'}), 400

def background_monitor():
    """Background thread to monitor system health"""
    while True:
        try:
            # Check chain integrity periodically
            db = sqlite3.connect('/var/forensics/chain_of_custody.db')
            cursor = db.execute("SELECT COUNT(*) FROM evidence WHERE verified=0")
            tampered_count = cursor.fetchone()[0]
            
            if tampered_count > 0:
                print(f"[ALERT] {tampered_count} tampered evidence entries detected!")
                collector.capture_incident(
                    'CHAIN_INTEGRITY_VIOLATION',
                    f'{tampered_count} evidence entries failed integrity check'
                )
            
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            print(f"[MONITOR] Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Start background monitor
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    # Start Flask app
    print("[API] Starting Forensic Evidence API on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=False)