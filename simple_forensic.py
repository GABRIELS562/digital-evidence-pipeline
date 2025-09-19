from flask import Flask, Response
from prometheus_client import generate_latest, Gauge, Counter, REGISTRY

app = Flask(__name__)

# Create metrics
compliance_score = Gauge('forensic_compliance_score', 'Compliance score', ['type'])
anomalies_counter = Counter('forensic_anomalies_detected', 'Anomalies detected', ['type'])

# Set initial values
compliance_score.labels(type='sox').set(95.0)
compliance_score.labels(type='fda').set(98.5)
compliance_score.labels(type='gmp').set(97.2)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
