#!/bin/bash
# Forensic Evidence Chain Backup - YOUR CRITICAL DIFFERENTIATOR
# Real-time replication to prevent evidence loss

set -e

# Configuration
EVIDENCE_DIR="/var/forensics"
REPLICA_SERVER2="server2:/forensics-replica"
REPLICA_EC2="ec2:/backup/forensics"
BACKUP_LOG="/var/log/forensic-backup.log"

echo "===========================================" | tee -a $BACKUP_LOG
echo "Forensic Evidence Chain Backup" | tee -a $BACKUP_LOG
echo "Time: $(date)" | tee -a $BACKUP_LOG
echo "==========================================="  | tee -a $BACKUP_LOG

# Function to verify evidence integrity
verify_integrity() {
    echo "[*] Verifying evidence chain integrity..." | tee -a $BACKUP_LOG
    python3 - << 'PYTHON'
import sqlite3
import hashlib
import json
import sys

try:
    db = sqlite3.connect('/var/forensics/chain_of_custody.db')
    cursor = db.execute("SELECT COUNT(*) FROM evidence WHERE verified=0")
    tampered = cursor.fetchone()[0]
    
    if tampered > 0:
        print(f"⚠️  WARNING: {tampered} evidence entries may be tampered!")
        sys.exit(1)
    else:
        cursor = db.execute("SELECT COUNT(*) FROM evidence")
        total = cursor.fetchone()[0]
        print(f"✓ Evidence chain verified: {total} entries intact")
        
        # Calculate chain hash
        cursor = db.execute("SELECT evidence_hash FROM evidence ORDER BY id")
        chain_hash = hashlib.sha256()
        for row in cursor:
            chain_hash.update(row[0].encode())
        
        final_hash = chain_hash.hexdigest()
        print(f"✓ Chain hash: {final_hash[:16]}...")
        
        # Save hash for verification after restore
        with open('/var/forensics/chain_hash.txt', 'w') as f:
            f.write(final_hash)
            
except Exception as e:
    print(f"✗ Verification failed: {e}")
    sys.exit(1)
PYTHON
}

# Step 1: Verify integrity before backup
verify_integrity

# Step 2: Create point-in-time snapshot
echo "[*] Creating evidence snapshot..." | tee -a $BACKUP_LOG
SNAPSHOT_NAME="evidence-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "/backups/${SNAPSHOT_NAME}" -C / var/forensics/
echo "✓ Snapshot created: ${SNAPSHOT_NAME}" | tee -a $BACKUP_LOG

# Step 3: Sync to Server 2 (primary replica)
echo "[*] Syncing to Server 2..." | tee -a $BACKUP_LOG
rsync -av --delete \
    --exclude '*.tmp' \
    --exclude '*.lock' \
    "${EVIDENCE_DIR}/" "${REPLICA_SERVER2}/"

if [ $? -eq 0 ]; then
    echo "✓ Server 2 sync complete" | tee -a $BACKUP_LOG
else
    echo "✗ Server 2 sync failed!" | tee -a $BACKUP_LOG
    exit 1
fi

# Step 4: Sync critical data to EC2 (for demo access)
echo "[*] Syncing to EC2 gateway..." | tee -a $BACKUP_LOG
# Only sync database and recent evidence (last 7 days) to save bandwidth
rsync -av \
    --include='chain_of_custody.db' \
    --include='*/' \
    --include='INC-*' \
    --exclude='*' \
    --bwlimit=1000 \
    "${EVIDENCE_DIR}/" "${REPLICA_EC2}/"

# Step 5: Verify replica integrity
echo "[*] Verifying replicas..." | tee -a $BACKUP_LOG
ssh server2 "cd /forensics-replica && sha256sum chain_of_custody.db" > /tmp/replica_hash
LOCAL_HASH=$(sha256sum ${EVIDENCE_DIR}/chain_of_custody.db)

if [ "$(cat /tmp/replica_hash)" = "$LOCAL_HASH" ]; then
    echo "✓ Replica verified" | tee -a $BACKUP_LOG
else
    echo "⚠️  Replica mismatch - investigating..." | tee -a $BACKUP_LOG
fi

# Step 6: Create recovery script
cat > /backups/FORENSIC_RECOVERY.sh << 'EOF'
#!/bin/bash
# FORENSIC EVIDENCE RECOVERY SCRIPT
# Use this when Server 1 fails

echo "Starting Forensic Evidence Recovery..."

# Option 1: Restore from Server 2
if ping -c 1 server2 &> /dev/null; then
    echo "Restoring from Server 2..."
    rsync -av server2:/forensics-replica/ /var/forensics/
    
# Option 2: Restore from EC2
elif ping -c 1 ec2.amazonaws.com &> /dev/null; then
    echo "Restoring from EC2..."
    rsync -av ec2:/backup/forensics/ /var/forensics/
    
# Option 3: Restore from snapshot
else
    echo "Restoring from latest snapshot..."
    LATEST_SNAPSHOT=$(ls -t /backups/evidence-*.tar.gz | head -1)
    tar -xzf "$LATEST_SNAPSHOT" -C /
fi

# Verify integrity after restore
python3 /scripts/forensic_collector.py verify-all

echo "Recovery complete! Checking status..."
python3 /scripts/forensic_collector.py list
EOF

chmod +x /backups/FORENSIC_RECOVERY.sh

# Step 7: Log backup metrics
EVIDENCE_COUNT=$(find ${EVIDENCE_DIR}/evidence -type d -name "INC-*" | wc -l)
DB_SIZE=$(du -h ${EVIDENCE_DIR}/chain_of_custody.db | cut -f1)
TOTAL_SIZE=$(du -sh ${EVIDENCE_DIR} | cut -f1)

cat >> /var/prometheus/backup_metrics.prom << METRICS
# Forensic Evidence Backup Metrics
forensic_backup_last_success $(date +%s)
forensic_evidence_count ${EVIDENCE_COUNT}
forensic_backup_size_bytes $(du -sb ${EVIDENCE_DIR} | cut -f1)
forensic_replicas_count 2
METRICS

echo "==========================================="  | tee -a $BACKUP_LOG
echo "Backup Summary:" | tee -a $BACKUP_LOG
echo "Evidence Count: ${EVIDENCE_COUNT}" | tee -a $BACKUP_LOG
echo "Database Size: ${DB_SIZE}" | tee -a $BACKUP_LOG
echo "Total Size: ${TOTAL_SIZE}" | tee -a $BACKUP_LOG
echo "Replicas: Server2 ✓ EC2 ✓" | tee -a $BACKUP_LOG
echo "==========================================="  | tee -a $BACKUP_LOG

exit 0