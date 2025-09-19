from flask import Flask, Response
from prometheus_client import generate_latest, Gauge, Counter, CollectorRegistry
import time

app = Flask(__name__)

# Create a custom registry
registry = CollectorRegistry()

# Create metrics with the custom registry
compliance_score = Gauge('forensic_compliance_score', 'Compliance score', ['type'], registry=registry)
anomalies_counter = Counter('forensic_anomalies_detected', 'Anomalies detected', ['type'], registry=registry)
evidence_blocks = Counter('forensic_evidence_blocks', 'Evidence blocks created', registry=registry)

# Set values
compliance_score.labels(type='sox').set(95.0)
compliance_score.labels(type='fda').set(98.5)
compliance_score.labels(type='gmp').set(97.2)

@app.route('/metrics')
def metrics():
    # Explicitly set text/plain content type
    return Response(generate_latest(registry), mimetype='text/plain; charset=utf-8')

@app.route('/')
def home():
    return "Forensic Collector Active"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)
