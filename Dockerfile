FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir requests

# Create app directory
WORKDIR /app

# Copy the new forensic evidence collector
COPY scripts/forensic_evidence_collector.py /app/

# Make scripts executable
RUN chmod +x /app/*.py

# Create data directory
RUN mkdir -p /data

# Expose HTTP port
EXPOSE 9999

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9999/health || exit 1

# Default command - run the evidence collector
CMD ["python3", "/app/forensic_evidence_collector.py", \
     "--port", "9999", \
     "--db", "/data/forensic.db", \
     "--interval", "30"]
