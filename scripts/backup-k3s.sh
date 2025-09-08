#!/bin/bash
# K3s State Backup Script - CRITICAL FOR DISASTER RECOVERY
# This backs up your entire Kubernetes cluster state

set -e

# Configuration
BACKUP_DIR="/var/lib/rancher/k3s/server/db/snapshots"
REMOTE_BACKUP="server2:/backups/k3s"
RETENTION_DAYS=7
DATE_STAMP=$(date +%Y%m%d-%H%M%S)

echo "===========================================" 
echo "K3s Cluster State Backup"
echo "Time: $(date)"
echo "==========================================="

# Create snapshot of K3s etcd database
echo "[1/4] Creating K3s etcd snapshot..."
sudo k3s etcd-snapshot save --name "k3s-backup-${DATE_STAMP}"

# Verify snapshot was created
if [ -f "${BACKUP_DIR}/k3s-backup-${DATE_STAMP}" ]; then
    echo "✓ Snapshot created successfully"
    ls -lh "${BACKUP_DIR}/k3s-backup-${DATE_STAMP}"
else
    echo "✗ Snapshot creation failed!"
    exit 1
fi

# Sync to Server 2
echo "[2/4] Syncing to Server 2..."
rsync -av --progress "${BACKUP_DIR}/" "${REMOTE_BACKUP}/"
echo "✓ Synced to remote backup location"

# Also backup critical configs
echo "[3/4] Backing up K3s configs..."
tar -czf "/backups/k3s-configs-${DATE_STAMP}.tar.gz" \
    /etc/rancher/k3s/ \
    /var/lib/rancher/k3s/server/manifests/ \
    /var/lib/rancher/k3s/server/tls/ 2>/dev/null || true

# Clean up old snapshots
echo "[4/4] Cleaning up old snapshots (keeping ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "k3s-backup-*" -mtime +${RETENTION_DAYS} -delete
echo "✓ Cleanup complete"

# Log for forensic evidence
echo "{
  \"event\": \"k3s_backup_completed\",
  \"timestamp\": \"$(date -Iseconds)\",
  \"snapshot\": \"k3s-backup-${DATE_STAMP}\",
  \"size\": \"$(du -h ${BACKUP_DIR}/k3s-backup-${DATE_STAMP} | cut -f1)\",
  \"remote_sync\": \"success\",
  \"retention_days\": ${RETENTION_DAYS}
}" >> /var/log/backup-audit.json

echo "==========================================="
echo "K3s backup completed successfully!"
echo "Snapshot: k3s-backup-${DATE_STAMP}"
echo "==========================================="

# Recovery instructions
cat << 'EOF' > /backups/RECOVERY_INSTRUCTIONS.txt
K3S DISASTER RECOVERY PROCEDURE
================================

1. IF PRIMARY SERVER FAILS:
   ssh server2
   scp server2:/backups/k3s/k3s-backup-LATEST /tmp/
   k3s server --cluster-reset --cluster-reset-restore-path=/tmp/k3s-backup-LATEST

2. TO RESTORE ON NEW SERVER:
   # Install K3s first
   curl -sfL https://get.k3s.io | sh -
   
   # Restore from backup
   k3s etcd-snapshot restore /path/to/k3s-backup-YYYYMMDD
   
   # Restart K3s
   systemctl restart k3s

3. VERIFY RECOVERY:
   kubectl get nodes
   kubectl get pods --all-namespaces
   kubectl logs -n forensics daemonset/forensic-collector

Recovery Target: <30 minutes
Data Loss: Zero for cluster state
EOF

exit 0