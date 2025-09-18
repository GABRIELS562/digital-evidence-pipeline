#!/usr/bin/env python3
"""
Lightweight Storage Backend Module
Replaces Elasticsearch with local file-based storage for resource-constrained environments.
Provides SQLite for structured audit data and JSON files for evidence blocks.

This module significantly reduces memory footprint and eliminates the need for
a separate Elasticsearch service, making it ideal for EC2 micro/small instances.
"""

import json
import sqlite3
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import glob


class StorageBackend:
    """
    Lightweight storage backend replacing Elasticsearch.
    
    Uses:
    - SQLite for audit events and structured queries
    - JSON files for evidence blocks with content-addressable storage
    - File system for efficient searching without memory overhead
    
    This approach eliminates the ~512MB memory requirement of Elasticsearch
    while maintaining all forensic capabilities.
    """
    
    def __init__(self, 
                 db_path: str = "/var/forensics/audit.db",
                 evidence_dir: str = "/evidence"):
        """
        Initialize the storage backend.
        
        Args:
            db_path: Path to SQLite database for audit events
            evidence_dir: Directory for storing evidence JSON files
        """
        self.db_path = db_path
        self.evidence_dir = Path(evidence_dir)
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with audit event schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    source TEXT,
                    user TEXT,
                    action TEXT,
                    resource TEXT,
                    outcome TEXT,
                    details TEXT,
                    evidence_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for common queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_events(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON audit_events(event_type)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_evidence_hash 
                ON audit_events(evidence_hash)
            ''')
            
            conn.commit()
    
    def save_evidence_block(self, block_data: Dict[str, Any]) -> str:
        """
        Save evidence block to JSON file using content-addressable storage.
        
        Args:
            block_data: Dictionary containing evidence data
            
        Returns:
            str: SHA-256 hash of the evidence block (used as filename)
            
        Note:
            This replaces Elasticsearch document storage with local JSON files.
            Files are named by their content hash for integrity verification.
        """
        # Add timestamp if not present
        if 'timestamp' not in block_data:
            block_data['timestamp'] = datetime.now().isoformat()
        
        # Serialize to JSON
        json_data = json.dumps(block_data, indent=2, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        evidence_hash = hashlib.sha256(json_data.encode()).hexdigest()
        
        # Save to file named by hash
        evidence_path = self.evidence_dir / f"{evidence_hash}.json"
        with open(evidence_path, 'w') as f:
            f.write(json_data)
        
        # Also save a metadata file for quick searching
        metadata = {
            'hash': evidence_hash,
            'timestamp': block_data.get('timestamp'),
            'type': block_data.get('type', 'unknown'),
            'incident_id': block_data.get('incident_id'),
            'size': len(json_data)
        }
        
        metadata_path = self.evidence_dir / f"{evidence_hash}.meta"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return evidence_hash
    
    def save_audit_event(self, event: Dict[str, Any]) -> int:
        """
        Save audit event to SQLite database.
        
        Args:
            event: Dictionary containing audit event data
            
        Returns:
            int: ID of the inserted audit event
            
        Note:
            This replaces Elasticsearch indexing with SQLite insertion.
            Provides ACID compliance and efficient querying without memory overhead.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO audit_events 
                (timestamp, event_type, severity, source, user, action, 
                 resource, outcome, details, evidence_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.get('timestamp', datetime.now().isoformat()),
                event.get('event_type', 'unknown'),
                event.get('severity', 'info'),
                event.get('source', ''),
                event.get('user', ''),
                event.get('action', ''),
                event.get('resource', ''),
                event.get('outcome', ''),
                json.dumps(event.get('details', {})),
                event.get('evidence_hash', '')
            ))
            
            return cursor.lastrowid
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit events from SQLite.
        
        Args:
            limit: Maximum number of events to retrieve
            
        Returns:
            List of audit events as dictionaries
            
        Note:
            This replaces Elasticsearch queries with SQLite SELECT statements.
            Maintains all querying capabilities with better resource efficiency.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM audit_events 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                # Parse JSON details field
                if event.get('details'):
                    try:
                        event['details'] = json.loads(event['details'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            
            return events
    
    def search_evidence(self, query: str) -> List[Dict[str, Any]]:
        """
        Search evidence blocks using metadata and content.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching evidence blocks
            
        Note:
            This replaces Elasticsearch full-text search with file-based searching.
            Efficient for moderate data volumes without memory overhead.
        """
        results = []
        query_lower = query.lower()
        
        # Search through metadata files first for efficiency
        for meta_file in self.evidence_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if query matches metadata
                if (query_lower in str(metadata).lower()):
                    # Load the actual evidence file
                    evidence_file = meta_file.with_suffix('.json')
                    if evidence_file.exists():
                        with open(evidence_file, 'r') as f:
                            evidence = json.load(f)
                            evidence['_metadata'] = metadata
                            results.append(evidence)
                else:
                    # If not in metadata, check the full evidence file
                    evidence_file = meta_file.with_suffix('.json')
                    if evidence_file.exists():
                        with open(evidence_file, 'r') as f:
                            content = f.read()
                            if query_lower in content.lower():
                                evidence = json.loads(content)
                                evidence['_metadata'] = metadata
                                results.append(evidence)
                                
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.get('_metadata', {}).get('timestamp', ''), reverse=True)
        
        return results
    
    def get_evidence_by_hash(self, evidence_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve evidence block by its hash.
        
        Args:
            evidence_hash: SHA-256 hash of the evidence block
            
        Returns:
            Evidence block data or None if not found
        """
        evidence_path = self.evidence_dir / f"{evidence_hash}.json"
        if evidence_path.exists():
            with open(evidence_path, 'r') as f:
                return json.load(f)
        return None
    
    def verify_evidence_integrity(self, evidence_hash: str) -> bool:
        """
        Verify the integrity of an evidence block.
        
        Args:
            evidence_hash: Expected SHA-256 hash of the evidence
            
        Returns:
            True if integrity verified, False otherwise
        """
        evidence_path = self.evidence_dir / f"{evidence_hash}.json"
        if not evidence_path.exists():
            return False
        
        with open(evidence_path, 'r') as f:
            content = f.read()
        
        calculated_hash = hashlib.sha256(content.encode()).hexdigest()
        return calculated_hash == evidence_hash
    
    def search_audit_events(self, 
                           event_type: Optional[str] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search audit events with filters.
        
        Args:
            event_type: Filter by event type
            start_time: Filter events after this timestamp
            end_time: Filter events before this timestamp
            limit: Maximum number of results
            
        Returns:
            List of matching audit events
        """
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event.get('details'):
                    try:
                        event['details'] = json.loads(event['details'])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            
            return events
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for monitoring.
        
        Returns:
            Dictionary with storage metrics
        """
        # Count evidence files
        evidence_files = list(self.evidence_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in evidence_files)
        
        # Count audit events
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events")
            audit_count = cursor.fetchone()[0]
        
        return {
            'evidence_blocks': len(evidence_files),
            'evidence_size_bytes': total_size,
            'evidence_size_mb': round(total_size / (1024 * 1024), 2),
            'audit_events': audit_count,
            'database_size_bytes': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            'storage_backend': 'SQLite + Filesystem',
            'elasticsearch_replaced': True
        }


# Compatibility wrapper for Elasticsearch-like interface
class ElasticsearchCompatibility:
    """
    Provides Elasticsearch-compatible method names for easier migration.
    This wrapper allows existing code to work with minimal changes.
    """
    
    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend
    
    def index(self, index: str, body: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Elasticsearch-compatible index method."""
        if 'audit' in index:
            event_id = self.storage.save_audit_event(body)
            return {'_id': event_id, 'result': 'created'}
        else:
            evidence_hash = self.storage.save_evidence_block(body)
            return {'_id': evidence_hash, 'result': 'created'}
    
    def search(self, index: str = None, body: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Elasticsearch-compatible search method."""
        if body and 'query' in body:
            query_str = str(body['query'].get('match', {}).get('_all', ''))
            results = self.storage.search_evidence(query_str)
        else:
            results = self.storage.get_recent_events(100)
        
        return {
            'hits': {
                'total': {'value': len(results)},
                'hits': [{'_source': r} for r in results]
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    storage = StorageBackend()
    
    # Save an evidence block
    evidence = {
        'incident_id': 'INC-20240118-001',
        'type': 'system_failure',
        'description': 'Test evidence block',
        'data': {'cpu': 85, 'memory': 92}
    }
    
    hash_id = storage.save_evidence_block(evidence)
    print(f"Evidence saved with hash: {hash_id}")
    
    # Save an audit event
    event = {
        'event_type': 'login_attempt',
        'user': 'admin',
        'outcome': 'success',
        'source': '192.168.1.100'
    }
    
    event_id = storage.save_audit_event(event)
    print(f"Audit event saved with ID: {event_id}")
    
    # Get storage stats
    stats = storage.get_storage_stats()
    print(f"Storage stats: {stats}")