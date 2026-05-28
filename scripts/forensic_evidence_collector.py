#!/usr/bin/env python3
"""
Forensic Evidence Collector - Tamper-Evident Audit Trail System

Monitors LIMS and eShop metrics, creates SHA-256 hash chains for compliance,
and exposes Prometheus metrics for Grafana dashboards.

Architecture:
- Scrapes metrics from LIMS (DNA Lab) and eShop (E-commerce) every 30 seconds
- Creates blockchain-style hash chains (each block includes previous hash)
- Stores evidence in SQLite with timestamps
- Exposes /metrics (Prometheus), /evidence (JSON), /verify (integrity), /health
"""

import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('forensic-collector')

# Configuration
CONFIG = {
    'lims_endpoint': 'http://100.89.26.128:30017/metrics',
    'lims_api': 'http://100.89.26.128:30017/api/samples',
    'eshop_endpoint': 'http://100.89.26.128:30889/metrics',
    'scrape_interval': 30,  # seconds
    'http_port': 9999,
    'db_path': '/home/jaime/apps/digital-evidence-pipeline/forensic.db',
}


@dataclass
class EvidenceBlock:
    """Represents a single evidence block in the chain."""
    id: int
    timestamp: str
    source: str  # 'lims' or 'eshop'
    metrics_hash: str
    prev_hash: str
    raw_metrics: str
    block_hash: str  # Combined hash including prev_hash


@dataclass
class MetricsSnapshot:
    """Parsed metrics from a source."""
    source: str
    timestamp: str
    raw_text: str
    metrics: Dict[str, float] = field(default_factory=dict)
    labels: Dict[str, Dict[str, str]] = field(default_factory=dict)


class PrometheusParser:
    """Parse Prometheus text format metrics."""

    @staticmethod
    def parse(text: str) -> Dict[str, List[Tuple[Dict[str, str], float]]]:
        """
        Parse Prometheus metrics text format.
        Returns dict of metric_name -> [(labels_dict, value), ...]
        """
        metrics = {}

        for line in text.strip().split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse metric line: metric_name{label="value",...} value
            # or: metric_name value
            match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+(.+)$', line)
            if match:
                metric_name = match.group(1)
                labels_str = match.group(2)
                value_str = match.group(3)

                # Parse labels
                labels = {}
                for label_match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', labels_str):
                    labels[label_match.group(1)] = label_match.group(2)

                # Parse value
                try:
                    value = float(value_str.split()[0])  # Handle timestamps
                except ValueError:
                    continue

                if metric_name not in metrics:
                    metrics[metric_name] = []
                metrics[metric_name].append((labels, value))
            else:
                # Try simple format: metric_name value
                match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+(.+)$', line)
                if match:
                    metric_name = match.group(1)
                    value_str = match.group(2)

                    try:
                        value = float(value_str.split()[0])
                    except ValueError:
                        continue

                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    metrics[metric_name].append(({}, value))

        return metrics


class HashChain:
    """Manages the tamper-evident hash chain."""

    @staticmethod
    def compute_hash(data: str) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_block_hash(metrics_hash: str, prev_hash: str, timestamp: str) -> str:
        """Compute block hash including previous hash (blockchain-style)."""
        combined = f"{prev_hash}:{metrics_hash}:{timestamp}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_chain(blocks: List[EvidenceBlock]) -> Tuple[bool, Optional[str]]:
        """
        Verify the integrity of the hash chain.
        Returns (is_valid, error_message).
        """
        if not blocks:
            return True, None

        for i, block in enumerate(blocks):
            # Verify metrics hash
            expected_metrics_hash = HashChain.compute_hash(block.raw_metrics)
            if expected_metrics_hash != block.metrics_hash:
                return False, f"Metrics hash mismatch at block {block.id}"

            # Verify block hash
            expected_block_hash = HashChain.compute_block_hash(
                block.metrics_hash, block.prev_hash, block.timestamp
            )
            if expected_block_hash != block.block_hash:
                return False, f"Block hash mismatch at block {block.id}"

            # Verify chain linkage (except for genesis block)
            if i > 0:
                if block.prev_hash != blocks[i-1].block_hash:
                    return False, f"Chain broken at block {block.id}"

        return True, None


class Database:
    """SQLite database for evidence storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        # Enable WAL mode for concurrent reads/writes
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=5000')

        # Main evidence chain table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chain_of_custody (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                metrics_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                block_hash TEXT NOT NULL,
                raw_metrics TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Compliance snapshots for quick queries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                lims_samples_total INTEGER DEFAULT 0,
                lims_transitions_total INTEGER DEFAULT 0,
                eshop_orders_total INTEGER DEFAULT 0,
                eshop_payments_total INTEGER DEFAULT 0,
                chain_valid INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chain_source
            ON chain_of_custody(source)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chain_timestamp
            ON chain_of_custody(timestamp)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def get_last_block(self, source: str = None) -> Optional[EvidenceBlock]:
        """Get the most recent block, optionally filtered by source."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        if source:
            cursor.execute('''
                SELECT id, timestamp, source, metrics_hash, prev_hash, raw_metrics, block_hash
                FROM chain_of_custody
                WHERE source = ?
                ORDER BY id DESC LIMIT 1
            ''', (source,))
        else:
            cursor.execute('''
                SELECT id, timestamp, source, metrics_hash, prev_hash, raw_metrics, block_hash
                FROM chain_of_custody
                ORDER BY id DESC LIMIT 1
            ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return EvidenceBlock(
                id=row[0], timestamp=row[1], source=row[2],
                metrics_hash=row[3], prev_hash=row[4],
                raw_metrics=row[5], block_hash=row[6]
            )
        return None

    def add_block(self, timestamp: str, source: str, metrics_hash: str,
                  prev_hash: str, block_hash: str, raw_metrics: str) -> int:
        """Add a new block to the chain."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO chain_of_custody
            (timestamp, source, metrics_hash, prev_hash, block_hash, raw_metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, source, metrics_hash, prev_hash, block_hash, raw_metrics))

        block_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return block_id

    def get_blocks(self, source: str = None, limit: int = 100) -> List[EvidenceBlock]:
        """Get blocks, optionally filtered by source."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        if source:
            cursor.execute('''
                SELECT id, timestamp, source, metrics_hash, prev_hash, raw_metrics, block_hash
                FROM chain_of_custody
                WHERE source = ?
                ORDER BY id ASC
                LIMIT ?
            ''', (source, limit))
        else:
            cursor.execute('''
                SELECT id, timestamp, source, metrics_hash, prev_hash, raw_metrics, block_hash
                FROM chain_of_custody
                ORDER BY id ASC
                LIMIT ?
            ''', (limit,))

        blocks = []
        for row in cursor.fetchall():
            blocks.append(EvidenceBlock(
                id=row[0], timestamp=row[1], source=row[2],
                metrics_hash=row[3], prev_hash=row[4],
                raw_metrics=row[5], block_hash=row[6]
            ))

        conn.close()
        return blocks

    def get_block_count(self, source: str = None) -> int:
        """Get total block count."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        if source:
            cursor.execute(
                'SELECT COUNT(*) FROM chain_of_custody WHERE source = ?',
                (source,)
            )
        else:
            cursor.execute('SELECT COUNT(*) FROM chain_of_custody')

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def save_compliance_snapshot(self, lims_samples: int, lims_transitions: int,
                                  eshop_orders: int, eshop_payments: int,
                                  chain_valid: bool):
        """Save a compliance snapshot."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO compliance_snapshots
            (timestamp, lims_samples_total, lims_transitions_total,
             eshop_orders_total, eshop_payments_total, chain_valid)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(timezone.utc).isoformat(),
            lims_samples, lims_transitions,
            eshop_orders, eshop_payments,
            1 if chain_valid else 0
        ))

        conn.commit()
        conn.close()


class MetricsScraper:
    """Scrapes metrics from LIMS and eShop endpoints."""

    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = 10

    def scrape_lims(self) -> Optional[MetricsSnapshot]:
        """Scrape LIMS metrics."""
        try:
            response = self.session.get(self.config['lims_endpoint'])
            response.raise_for_status()

            raw_text = response.text
            parsed = PrometheusParser.parse(raw_text)

            snapshot = MetricsSnapshot(
                source='lims',
                timestamp=datetime.now(timezone.utc).isoformat(),
                raw_text=raw_text,
                metrics={},
                labels={}
            )

            # Extract key LIMS metrics
            for metric_name, values in parsed.items():
                if metric_name.startswith('lims_'):
                    for labels, value in values:
                        key = metric_name
                        if labels:
                            key = f"{metric_name}_{json.dumps(labels, sort_keys=True)}"
                        snapshot.metrics[key] = value
                        snapshot.labels[key] = labels

            logger.debug(f"Scraped {len(snapshot.metrics)} LIMS metrics")
            return snapshot

        except requests.RequestException as e:
            logger.error(f"Failed to scrape LIMS: {e}")
            return None

    def scrape_eshop(self) -> Optional[MetricsSnapshot]:
        """Scrape eShop metrics."""
        try:
            response = self.session.get(self.config['eshop_endpoint'])
            response.raise_for_status()

            raw_text = response.text
            parsed = PrometheusParser.parse(raw_text)

            snapshot = MetricsSnapshot(
                source='eshop',
                timestamp=datetime.now(timezone.utc).isoformat(),
                raw_text=raw_text,
                metrics={},
                labels={}
            )

            # Extract key eShop metrics
            for metric_name, values in parsed.items():
                if metric_name.startswith('eshop_'):
                    for labels, value in values:
                        key = metric_name
                        if labels:
                            key = f"{metric_name}_{json.dumps(labels, sort_keys=True)}"
                        snapshot.metrics[key] = value
                        snapshot.labels[key] = labels

            logger.debug(f"Scraped {len(snapshot.metrics)} eShop metrics")
            return snapshot

        except requests.RequestException as e:
            logger.error(f"Failed to scrape eShop: {e}")
            return None


class ForensicCollector:
    """Main collector orchestrating scraping, hashing, and storage."""

    def __init__(self, config: dict):
        self.config = config
        self.db = Database(config['db_path'])
        self.scraper = MetricsScraper(config)
        self.running = False
        self._scrape_thread = None

        # Current state for metrics exposure
        self.last_scrape_lims = None
        self.last_scrape_eshop = None
        self.chain_valid_lims = True
        self.chain_valid_eshop = True

        # Aggregated metrics
        self.lims_transitions_total = 0
        self.lims_samples_total = 0
        self.eshop_orders_total = 0
        self.eshop_payments_total = 0

    def _process_snapshot(self, snapshot: MetricsSnapshot) -> int:
        """Process a metrics snapshot and add to chain."""
        # Get previous block
        last_block = self.db.get_last_block(snapshot.source)
        prev_hash = last_block.block_hash if last_block else "genesis"

        # Compute hashes
        metrics_hash = HashChain.compute_hash(snapshot.raw_text)
        block_hash = HashChain.compute_block_hash(
            metrics_hash, prev_hash, snapshot.timestamp
        )

        # Store block
        block_id = self.db.add_block(
            timestamp=snapshot.timestamp,
            source=snapshot.source,
            metrics_hash=metrics_hash,
            prev_hash=prev_hash,
            block_hash=block_hash,
            raw_metrics=snapshot.raw_text
        )

        logger.info(f"Added {snapshot.source} block #{block_id}, hash: {block_hash[:16]}...")
        return block_id

    def _extract_aggregates(self, snapshot: MetricsSnapshot):
        """Extract aggregate metrics from snapshot."""
        if snapshot.source == 'lims':
            # Sum up lims_samples_processed_total
            samples = 0
            transitions = 0
            for key, value in snapshot.metrics.items():
                if 'lims_samples_processed_total' in key:
                    samples += value
                elif 'lims_workflow_transitions_total' in key:
                    transitions += value
            self.lims_samples_total = int(samples)
            self.lims_transitions_total = int(transitions)

        elif snapshot.source == 'eshop':
            # Sum up eshop_calls_total for specific services
            orders = 0
            payments = 0
            for key, value in snapshot.metrics.items():
                if 'eshop_calls_total' in key:
                    if 'checkoutservice' in key.lower():
                        orders += value
                    elif 'paymentservice' in key.lower():
                        payments += value
            self.eshop_orders_total = int(orders)
            self.eshop_payments_total = int(payments)

    def _scrape_loop(self):
        """Main scraping loop."""
        while self.running:
            try:
                # Scrape LIMS
                lims_snapshot = self.scraper.scrape_lims()
                if lims_snapshot:
                    self._process_snapshot(lims_snapshot)
                    self._extract_aggregates(lims_snapshot)
                    self.last_scrape_lims = time.time()

                # Scrape eShop
                eshop_snapshot = self.scraper.scrape_eshop()
                if eshop_snapshot:
                    self._process_snapshot(eshop_snapshot)
                    self._extract_aggregates(eshop_snapshot)
                    self.last_scrape_eshop = time.time()

                # Verify chain integrity periodically
                lims_blocks = self.db.get_blocks(source='lims', limit=1000)
                self.chain_valid_lims, _ = HashChain.verify_chain(lims_blocks)

                eshop_blocks = self.db.get_blocks(source='eshop', limit=1000)
                self.chain_valid_eshop, _ = HashChain.verify_chain(eshop_blocks)

                # Save compliance snapshot
                self.db.save_compliance_snapshot(
                    lims_samples=self.lims_samples_total,
                    lims_transitions=self.lims_transitions_total,
                    eshop_orders=self.eshop_orders_total,
                    eshop_payments=self.eshop_payments_total,
                    chain_valid=self.chain_valid_lims and self.chain_valid_eshop
                )

            except Exception as e:
                logger.error(f"Scrape loop error: {e}")

            # Sleep until next interval
            time.sleep(self.config['scrape_interval'])

    def start(self):
        """Start the collector."""
        self.running = True
        self._scrape_thread = threading.Thread(target=self._scrape_loop, daemon=True)
        self._scrape_thread.start()
        logger.info("Forensic collector started")

    def stop(self):
        """Stop the collector."""
        self.running = False
        if self._scrape_thread:
            self._scrape_thread.join(timeout=5)
        logger.info("Forensic collector stopped")

    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus format metrics."""
        lines = []

        # Chain integrity
        lines.append("# HELP forensic_chain_integrity Hash chain integrity (1=valid, 0=broken)")
        lines.append("# TYPE forensic_chain_integrity gauge")
        lines.append(f'forensic_chain_integrity{{source="lims"}} {1 if self.chain_valid_lims else 0}')
        lines.append(f'forensic_chain_integrity{{source="eshop"}} {1 if self.chain_valid_eshop else 0}')

        # Evidence blocks total
        lims_count = self.db.get_block_count('lims')
        eshop_count = self.db.get_block_count('eshop')
        lines.append("# HELP forensic_evidence_blocks_total Total evidence blocks collected")
        lines.append("# TYPE forensic_evidence_blocks_total counter")
        lines.append(f'forensic_evidence_blocks_total{{source="lims"}} {lims_count}')
        lines.append(f'forensic_evidence_blocks_total{{source="eshop"}} {eshop_count}')

        # Last scrape timestamp
        lines.append("# HELP forensic_last_scrape_timestamp Unix timestamp of last successful scrape")
        lines.append("# TYPE forensic_last_scrape_timestamp gauge")
        lims_ts = self.last_scrape_lims or 0
        eshop_ts = self.last_scrape_eshop or 0
        lines.append(f'forensic_last_scrape_timestamp{{source="lims"}} {lims_ts:.0f}')
        lines.append(f'forensic_last_scrape_timestamp{{source="eshop"}} {eshop_ts:.0f}')

        # Compliance scores (derived)
        # FDA compliance for LIMS - based on chain validity and recent activity
        fda_score = 100.0 if self.chain_valid_lims else 0.0
        if self.last_scrape_lims and (time.time() - self.last_scrape_lims) > 120:
            fda_score = max(0, fda_score - 20)  # Stale data penalty

        # SOC2 compliance for eShop
        soc2_score = 100.0 if self.chain_valid_eshop else 0.0
        if self.last_scrape_eshop and (time.time() - self.last_scrape_eshop) > 120:
            soc2_score = max(0, soc2_score - 20)

        lines.append("# HELP forensic_compliance_score Compliance score percentage")
        lines.append("# TYPE forensic_compliance_score gauge")
        lines.append(f'forensic_compliance_score{{type="fda",source="lims"}} {fda_score:.1f}')
        lines.append(f'forensic_compliance_score{{type="soc2",source="eshop"}} {soc2_score:.1f}')

        # LIMS workflow summary
        lines.append("# HELP forensic_lims_transitions_total Total LIMS workflow transitions")
        lines.append("# TYPE forensic_lims_transitions_total gauge")
        lines.append(f'forensic_lims_transitions_total {self.lims_transitions_total}')

        lines.append("# HELP forensic_lims_samples_total Total LIMS samples processed")
        lines.append("# TYPE forensic_lims_samples_total gauge")
        lines.append(f'forensic_lims_samples_total {self.lims_samples_total}')

        # eShop transaction summary
        lines.append("# HELP forensic_eshop_orders_total Total eShop checkout operations")
        lines.append("# TYPE forensic_eshop_orders_total gauge")
        lines.append(f'forensic_eshop_orders_total {self.eshop_orders_total}')

        lines.append("# HELP forensic_eshop_payments_total Total eShop payment operations")
        lines.append("# TYPE forensic_eshop_payments_total gauge")
        lines.append(f'forensic_eshop_payments_total {self.eshop_payments_total}')

        return '\n'.join(lines) + '\n'

    def get_evidence_json(self, source: str = None, limit: int = 50) -> dict:
        """Get evidence chain as JSON."""
        blocks = self.db.get_blocks(source=source, limit=limit)

        return {
            'total_blocks': len(blocks),
            'chain_valid': {
                'lims': self.chain_valid_lims,
                'eshop': self.chain_valid_eshop
            },
            'blocks': [
                {
                    'id': b.id,
                    'timestamp': b.timestamp,
                    'source': b.source,
                    'metrics_hash': b.metrics_hash,
                    'prev_hash': b.prev_hash,
                    'block_hash': b.block_hash
                }
                for b in blocks[-limit:]  # Most recent
            ]
        }

    def verify_chain(self, source: str = None) -> dict:
        """Verify chain integrity."""
        results = {}

        if source is None or source == 'lims':
            lims_blocks = self.db.get_blocks(source='lims', limit=10000)
            valid, error = HashChain.verify_chain(lims_blocks)
            results['lims'] = {
                'valid': valid,
                'blocks': len(lims_blocks),
                'error': error
            }

        if source is None or source == 'eshop':
            eshop_blocks = self.db.get_blocks(source='eshop', limit=10000)
            valid, error = HashChain.verify_chain(eshop_blocks)
            results['eshop'] = {
                'valid': valid,
                'blocks': len(eshop_blocks),
                'error': error
            }

        return results


class HTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the collector API."""

    collector: ForensicCollector = None

    def log_message(self, format, *args):
        """Suppress default logging, use our logger instead."""
        logger.debug(f"HTTP: {args[0]}")

    def _send_response(self, status: int, content_type: str, body: str):
        """Send HTTP response with CORS headers."""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        # CORS headers for browser access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == '/metrics':
            # Prometheus metrics endpoint
            metrics = self.collector.get_prometheus_metrics()
            self._send_response(200, 'text/plain; charset=utf-8', metrics)

        elif path == '/evidence':
            # JSON evidence chain
            source = query.get('source', [None])[0]
            limit = int(query.get('limit', [50])[0])
            evidence = self.collector.get_evidence_json(source=source, limit=limit)
            self._send_response(200, 'application/json', json.dumps(evidence, indent=2))

        elif path == '/verify':
            # Chain integrity verification
            source = query.get('source', [None])[0]
            results = self.collector.verify_chain(source=source)
            self._send_response(200, 'application/json', json.dumps(results, indent=2))

        elif path == '/health':
            # Health check
            health = {
                'status': 'healthy',
                'service': 'forensic-collector',
                'uptime': time.time() - self.collector.last_scrape_lims if self.collector.last_scrape_lims else 0,
                'last_scrape': {
                    'lims': self.collector.last_scrape_lims,
                    'eshop': self.collector.last_scrape_eshop
                }
            }
            self._send_response(200, 'application/json', json.dumps(health, indent=2))

        elif path == '/':
            # Simple index page
            html = """<!DOCTYPE html>
<html>
<head><title>Forensic Evidence Collector</title></head>
<body>
<h1>Forensic Evidence Collector</h1>
<ul>
<li><a href="/metrics">Prometheus Metrics</a></li>
<li><a href="/evidence">Evidence Chain (JSON)</a></li>
<li><a href="/verify">Verify Chain Integrity</a></li>
<li><a href="/health">Health Check</a></li>
</ul>
</body>
</html>"""
            self._send_response(200, 'text/html', html)

        else:
            self._send_response(404, 'text/plain', 'Not Found')


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Forensic Evidence Collector')
    parser.add_argument('--port', type=int, default=CONFIG['http_port'],
                        help='HTTP server port')
    parser.add_argument('--db', type=str, default=CONFIG['db_path'],
                        help='SQLite database path')
    parser.add_argument('--interval', type=int, default=CONFIG['scrape_interval'],
                        help='Scrape interval in seconds')
    parser.add_argument('--lims-endpoint', type=str, default=CONFIG['lims_endpoint'],
                        help='LIMS metrics endpoint')
    parser.add_argument('--eshop-endpoint', type=str, default=CONFIG['eshop_endpoint'],
                        help='eShop metrics endpoint')

    args = parser.parse_args()

    # Update config from args
    config = CONFIG.copy()
    config['http_port'] = args.port
    config['db_path'] = args.db
    config['scrape_interval'] = args.interval
    config['lims_endpoint'] = args.lims_endpoint
    config['eshop_endpoint'] = args.eshop_endpoint

    # Create collector
    collector = ForensicCollector(config)
    HTTPHandler.collector = collector

    # Start collector
    collector.start()

    # Start HTTP server
    server_address = ('0.0.0.0', config['http_port'])
    httpd = ThreadingHTTPServer(server_address, HTTPHandler)

    logger.info(f"HTTP server listening on port {config['http_port']}")
    logger.info(f"Scraping LIMS: {config['lims_endpoint']}")
    logger.info(f"Scraping eShop: {config['eshop_endpoint']}")
    logger.info(f"Database: {config['db_path']}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        collector.stop()
        httpd.shutdown()


if __name__ == '__main__':
    main()
