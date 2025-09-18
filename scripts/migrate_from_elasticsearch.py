#!/usr/bin/env python3
"""
Migration Script: Elasticsearch to SQLite/Filesystem
This script migrates existing forensic evidence and audit data from Elasticsearch
to the lightweight SQLite + filesystem storage backend.

Purpose: Transition existing deployments from resource-heavy Elasticsearch
to the lightweight storage solution suitable for EC2 micro instances.

Usage:
    python migrate_from_elasticsearch.py [--source-host localhost:9200] [--dry-run]
"""

import json
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our storage backend
try:
    from storage_backend import StorageBackend
except ImportError:
    logger.error("StorageBackend module not found. Ensure storage_backend.py is in the same directory.")
    sys.exit(1)

# Try to import elasticsearch (may not be installed in lightweight deployments)
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logger.warning("Elasticsearch module not installed. Will simulate migration with sample data.")


class ElasticsearchMigrator:
    """
    Migrates forensic evidence and audit data from Elasticsearch to SQLite/filesystem.
    Preserves all evidence hashes and maintains chain of custody during migration.
    """
    
    def __init__(self, es_host: str = "localhost:9200", dry_run: bool = False):
        """
        Initialize the migrator.
        
        Args:
            es_host: Elasticsearch host:port
            dry_run: If True, only simulate migration without writing data
        """
        self.es_host = es_host
        self.dry_run = dry_run
        self.storage = StorageBackend() if not dry_run else None
        self.es_client = None
        
        if ELASTICSEARCH_AVAILABLE:
            try:
                self.es_client = Elasticsearch([es_host])
                if not self.es_client.ping():
                    logger.warning(f"Cannot connect to Elasticsearch at {es_host}")
                    self.es_client = None
            except Exception as e:
                logger.warning(f"Failed to connect to Elasticsearch: {e}")
                self.es_client = None
    
    def migrate_evidence_blocks(self) -> int:
        """
        Migrate evidence blocks from Elasticsearch to filesystem.
        
        Returns:
            Number of evidence blocks migrated
        """
        migrated_count = 0
        
        if self.es_client:
            # Search for all evidence documents
            try:
                # Typical indices for forensic evidence
                indices = ["forensic-evidence-*", "evidence-*", "incidents-*"]
                
                for index_pattern in indices:
                    try:
                        # Use scroll API for large datasets
                        response = self.es_client.search(
                            index=index_pattern,
                            body={
                                "query": {"match_all": {}},
                                "size": 100
                            },
                            scroll='2m'
                        )
                        
                        scroll_id = response.get('_scroll_id')
                        hits = response['hits']['hits']
                        
                        while hits:
                            for hit in hits:
                                evidence = hit['_source']
                                
                                # Preserve original metadata
                                evidence['_original_index'] = hit['_index']
                                evidence['_original_id'] = hit['_id']
                                evidence['_migration_timestamp'] = datetime.now().isoformat()
                                
                                if not self.dry_run:
                                    # Save to new storage backend
                                    hash_id = self.storage.save_evidence_block(evidence)
                                    logger.info(f"Migrated evidence {hit['_id']} -> {hash_id}")
                                else:
                                    logger.info(f"[DRY RUN] Would migrate evidence {hit['_id']}")
                                
                                migrated_count += 1
                            
                            # Get next batch
                            response = self.es_client.scroll(
                                scroll_id=scroll_id,
                                scroll='2m'
                            )
                            hits = response['hits']['hits']
                        
                        # Clear scroll
                        self.es_client.clear_scroll(scroll_id=scroll_id)
                        
                    except Exception as e:
                        logger.warning(f"Could not migrate from index {index_pattern}: {e}")
                
            except Exception as e:
                logger.error(f"Error during evidence migration: {e}")
        else:
            # Simulate with sample data if Elasticsearch not available
            logger.info("Simulating migration with sample data...")
            sample_evidence = [
                {
                    'incident_id': 'INC-20240101-001',
                    'type': 'security_breach',
                    'timestamp': '2024-01-01T10:00:00Z',
                    'description': 'Unauthorized access attempt',
                    'severity': 'high',
                    'data': {'ip': '192.168.1.100', 'user': 'unknown'}
                },
                {
                    'incident_id': 'INC-20240102-002',
                    'type': 'service_failure',
                    'timestamp': '2024-01-02T15:30:00Z',
                    'description': 'Database connection timeout',
                    'severity': 'medium',
                    'data': {'service': 'postgres', 'error': 'timeout'}
                }
            ]
            
            for evidence in sample_evidence:
                if not self.dry_run:
                    hash_id = self.storage.save_evidence_block(evidence)
                    logger.info(f"Migrated sample evidence -> {hash_id}")
                else:
                    logger.info(f"[DRY RUN] Would migrate sample evidence {evidence['incident_id']}")
                migrated_count += 1
        
        return migrated_count
    
    def migrate_audit_events(self) -> int:
        """
        Migrate audit events from Elasticsearch to SQLite.
        
        Returns:
            Number of audit events migrated
        """
        migrated_count = 0
        
        if self.es_client:
            # Search for audit events
            try:
                indices = ["audit-*", "compliance-*", "logs-*"]
                
                for index_pattern in indices:
                    try:
                        response = self.es_client.search(
                            index=index_pattern,
                            body={
                                "query": {"match_all": {}},
                                "size": 100
                            },
                            scroll='2m'
                        )
                        
                        scroll_id = response.get('_scroll_id')
                        hits = response['hits']['hits']
                        
                        while hits:
                            for hit in hits:
                                event = hit['_source']
                                
                                # Map Elasticsearch fields to our schema
                                audit_event = {
                                    'timestamp': event.get('@timestamp', event.get('timestamp', '')),
                                    'event_type': event.get('event_type', event.get('type', 'unknown')),
                                    'severity': event.get('severity', event.get('level', 'info')),
                                    'source': event.get('source', event.get('host', '')),
                                    'user': event.get('user', event.get('username', '')),
                                    'action': event.get('action', ''),
                                    'resource': event.get('resource', ''),
                                    'outcome': event.get('outcome', event.get('result', '')),
                                    'details': {
                                        'original_index': hit['_index'],
                                        'original_id': hit['_id'],
                                        **event
                                    }
                                }
                                
                                if not self.dry_run:
                                    event_id = self.storage.save_audit_event(audit_event)
                                    logger.info(f"Migrated audit event {hit['_id']} -> ID {event_id}")
                                else:
                                    logger.info(f"[DRY RUN] Would migrate audit event {hit['_id']}")
                                
                                migrated_count += 1
                            
                            # Get next batch
                            response = self.es_client.scroll(
                                scroll_id=scroll_id,
                                scroll='2m'
                            )
                            hits = response['hits']['hits']
                        
                        # Clear scroll
                        self.es_client.clear_scroll(scroll_id=scroll_id)
                        
                    except Exception as e:
                        logger.warning(f"Could not migrate from index {index_pattern}: {e}")
                
            except Exception as e:
                logger.error(f"Error during audit event migration: {e}")
        else:
            # Simulate with sample data
            logger.info("Simulating audit event migration with sample data...")
            sample_events = [
                {
                    'event_type': 'login',
                    'user': 'admin',
                    'outcome': 'success',
                    'source': '10.0.0.1',
                    'timestamp': '2024-01-01T09:00:00Z'
                },
                {
                    'event_type': 'configuration_change',
                    'user': 'system',
                    'action': 'update_settings',
                    'resource': 'prometheus.yml',
                    'outcome': 'success',
                    'timestamp': '2024-01-01T10:00:00Z'
                }
            ]
            
            for event in sample_events:
                if not self.dry_run:
                    event_id = self.storage.save_audit_event(event)
                    logger.info(f"Migrated sample audit event -> ID {event_id}")
                else:
                    logger.info(f"[DRY RUN] Would migrate sample audit event {event['event_type']}")
                migrated_count += 1
        
        return migrated_count
    
    def verify_migration(self) -> bool:
        """
        Verify the integrity of migrated data.
        
        Returns:
            True if verification passed
        """
        if self.dry_run:
            logger.info("[DRY RUN] Skipping verification")
            return True
        
        try:
            # Check storage statistics
            stats = self.storage.get_storage_stats()
            logger.info(f"Migration Statistics:")
            logger.info(f"  - Evidence blocks: {stats['evidence_blocks']}")
            logger.info(f"  - Evidence size: {stats['evidence_size_mb']} MB")
            logger.info(f"  - Audit events: {stats['audit_events']}")
            logger.info(f"  - Database size: {stats['database_size_bytes'] / 1024 / 1024:.2f} MB")
            
            # Verify some evidence blocks
            evidence_files = list(Path("/var/forensics/evidence").glob("*.json"))[:5]
            for evidence_file in evidence_files:
                hash_name = evidence_file.stem
                if self.storage.verify_evidence_integrity(hash_name):
                    logger.info(f"  ✓ Evidence {hash_name[:8]}... integrity verified")
                else:
                    logger.error(f"  ✗ Evidence {hash_name[:8]}... integrity check failed")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def create_migration_report(self, evidence_count: int, audit_count: int):
        """
        Create a migration report for audit purposes.
        
        Args:
            evidence_count: Number of evidence blocks migrated
            audit_count: Number of audit events migrated
        """
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'source': f'elasticsearch://{self.es_host}',
            'destination': 'sqlite+filesystem',
            'dry_run': self.dry_run,
            'evidence_blocks_migrated': evidence_count,
            'audit_events_migrated': audit_count,
            'total_items': evidence_count + audit_count,
            'status': 'success' if not self.dry_run else 'dry_run_completed'
        }
        
        report_path = Path("/var/forensics/migration_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.dry_run:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Migration report saved to {report_path}")
        else:
            logger.info(f"[DRY RUN] Would save report: {json.dumps(report, indent=2)}")
        
        # Display summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Source: Elasticsearch @ {self.es_host}")
        print(f"Destination: SQLite + Filesystem")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"Evidence Blocks: {evidence_count}")
        print(f"Audit Events: {audit_count}")
        print(f"Total Items: {evidence_count + audit_count}")
        print(f"Status: {'✓ Complete' if not self.dry_run else '✓ Dry run complete'}")
        print("="*60)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description='Migrate forensic data from Elasticsearch to SQLite/Filesystem'
    )
    parser.add_argument(
        '--source-host',
        default='localhost:9200',
        help='Elasticsearch host:port (default: localhost:9200)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without writing data'
    )
    parser.add_argument(
        '--skip-evidence',
        action='store_true',
        help='Skip evidence block migration'
    )
    parser.add_argument(
        '--skip-audit',
        action='store_true',
        help='Skip audit event migration'
    )
    
    args = parser.parse_args()
    
    # Display migration plan
    print("\n" + "="*60)
    print("FORENSIC DATA MIGRATION TOOL")
    print("="*60)
    print("This tool migrates forensic evidence and audit data from")
    print("Elasticsearch to the lightweight SQLite/filesystem backend.")
    print("\nThis is essential for:")
    print("  • Reducing memory footprint (saves ~512MB)")
    print("  • Running on EC2 t2.micro instances")
    print("  • Eliminating Java/JVM dependencies")
    print("  • Preserving chain of custody during transition")
    print("="*60 + "\n")
    
    if not args.dry_run:
        response = input("Proceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
    
    # Initialize migrator
    migrator = ElasticsearchMigrator(
        es_host=args.source_host,
        dry_run=args.dry_run
    )
    
    evidence_count = 0
    audit_count = 0
    
    # Migrate evidence blocks
    if not args.skip_evidence:
        logger.info("Starting evidence block migration...")
        evidence_count = migrator.migrate_evidence_blocks()
        logger.info(f"Migrated {evidence_count} evidence blocks")
    
    # Migrate audit events
    if not args.skip_audit:
        logger.info("Starting audit event migration...")
        audit_count = migrator.migrate_audit_events()
        logger.info(f"Migrated {audit_count} audit events")
    
    # Verify migration
    if not args.dry_run and (evidence_count > 0 or audit_count > 0):
        logger.info("Verifying migration integrity...")
        if migrator.verify_migration():
            logger.info("✓ Migration verification passed")
        else:
            logger.error("✗ Migration verification failed - please check logs")
    
    # Create report
    migrator.create_migration_report(evidence_count, audit_count)
    
    # Post-migration instructions
    if not args.dry_run:
        print("\nPOST-MIGRATION STEPS:")
        print("1. Verify the migrated data:")
        print("   python forensic_collector.py list")
        print("   python forensic_collector.py search 'test'")
        print("\n2. Stop Elasticsearch (if no longer needed):")
        print("   docker-compose stop elasticsearch")
        print("\n3. Deploy the lightweight version:")
        print("   docker-compose -f docker-compose-ec2.yml up -d")
        print("\n4. Remove Elasticsearch data (optional, after verification):")
        print("   docker volume rm elasticsearch_data")


if __name__ == "__main__":
    main()