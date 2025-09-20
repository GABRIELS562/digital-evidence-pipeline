# QUICK REFERENCE GUIDE
## Popular Commands and Shortcuts for Forensic Evidence Collector Platform

---

## Essential Commands

### Server Status Checks
```bash
# Check all pods across namespaces
kubectl get pods --all-namespaces

# Check forensic collector status
kubectl get pods -n forensics
kubectl logs -n forensics daemonset/forensic-collector --tail=20

# Check Docker containers on Server 2
docker ps
docker stats

# Check Tailscale connectivity
tailscale status
tailscale ping server2
```

### Forensic Evidence Commands
```bash
# Trigger test incidents
curl -X POST http://localhost:8888/trigger/lims      # FDA violation
curl -X POST http://localhost:8888/trigger/finance   # SOX alert  
curl -X POST http://localhost:8888/trigger/pharma    # GMP breach
curl -X POST http://localhost:8888/trigger/jenkins   # CI failure

# List recent incidents
python3 scripts/forensic_collector.py list

# Verify evidence integrity
python3 scripts/forensic_collector.py verify INC-20240108-143022

# Access evidence viewer
kubectl port-forward -n forensics svc/forensic-api 8888:8888
# Then open: http://localhost:8888
```

### Backup and Recovery Commands
```bash
# Manual backups
./scripts/backup-k3s.sh           # Backup K3s cluster state
./scripts/backup-forensics.sh     # Backup evidence chain

# Test disaster recovery (CRITICAL for interviews!)
./scripts/disaster-recovery-test.sh

# View DR test results
cat ~/DISASTER_RECOVERY_PROOF.txt

# Manual K3s restore (if needed)
k3s etcd-snapshot restore /backups/k3s/k3s-backup-LATEST
```

### Demo Commands (Interview Ready)
```bash
# Quick demo flow (5 minutes)
echo "1. Evidence Viewer"; open http://ec2-public-ip/forensics
echo "2. DR Proof"; cat ~/DISASTER_RECOVERY_PROOF.txt | head -10
echo "3. Live Incident"; curl -X POST http://localhost:8888/trigger/lims
echo "4. Dashboards"; open http://ec2-public-ip/
```

---

## Service Access URLs

### From EC2 Public IP (Interview Demo)
```
Main Dashboard:    http://ec2-public-ip/
Evidence Viewer:   http://ec2-public-ip/forensics/
Prometheus:        http://ec2-public-ip/prometheus/
DR Status:         http://ec2-public-ip/dr-status
```

### Internal Access (Development)
```bash
# Grafana (Server 2)
http://server2.tailscale.net:3000    # admin/admin

# Prometheus (Server 2)  
http://server2.tailscale.net:9090

# Forensic API (Server 1)
http://server1.tailscale.net:8888

# Jenkins (Server 1)
kubectl port-forward -n jenkins svc/jenkins-service 8080:8080
http://localhost:8080

# ArgoCD (Server 1)
kubectl port-forward -n argocd svc/argocd-server 8081:443
https://localhost:8081
```

---

## Troubleshooting Quick Fixes

### Pod Not Starting
```bash
# Check pod status and events
kubectl describe pod pod-name -n namespace
kubectl get events -n namespace --sort-by='.lastTimestamp'

# Check logs
kubectl logs pod-name -n namespace --previous

# Delete and recreate
kubectl delete pod pod-name -n namespace
```

### Forensic Collector Issues
```bash
# Check collector health
curl http://localhost:8888/health

# Check evidence directory
ls -la /var/forensics/evidence/
ls -la /var/forensics/chain_of_custody.db

# Restart collector
kubectl rollout restart daemonset/forensic-collector -n forensics
```

### Network Connectivity Issues  
```bash
# Test Tailscale connections
tailscale ping server1
tailscale ping server2
tailscale ping ec2-instance

# Check Nginx on EC2
sudo nginx -t
sudo systemctl status nginx
sudo systemctl restart nginx

# Check EC2 security groups (AWS Console)
# Ensure ports 22, 80, 8000, 8888 are open
```

### Docker Issues on Server 2
```bash
# Restart monitoring stack
cd ~/monitoring
docker-compose -f docker-compose-monitoring.yml restart

# Check logs
docker logs prometheus
docker logs grafana  
docker logs loki
docker logs alertmanager

# Clean up if needed
docker system prune -f
```

---

## Performance Monitoring

### Resource Usage
```bash
# Server resources
htop
df -h
free -h

# K3s resources
kubectl top nodes
kubectl top pods --all-namespaces

# Docker resources  
docker stats
```

### Evidence Storage
```bash
# Check evidence size
du -sh /var/forensics/
du -sh /var/forensics/evidence/

# Count incidents
find /var/forensics/evidence -name "INC-*" -type d | wc -l

# Check database size
ls -lh /var/forensics/chain_of_custody.db
```

---

## Maintenance Commands

### Daily Maintenance
```bash
# Check system health
kubectl get pods --all-namespaces | grep -v Running
docker ps -a | grep -v Up

# Review recent evidence
python3 scripts/forensic_collector.py list | head -10

# Check backup status
ls -la /backups/k3s/ | tail -5
ssh server2 "ls -la /forensics-replica/"
```

### Weekly Maintenance
```bash
# Clean old evidence (keep 30 days)
find /var/forensics/evidence -name "INC-*" -type d -mtime +30 -exec rm -rf {} \;

# Update Docker images
docker-compose -f ~/monitoring/docker-compose-monitoring.yml pull
docker-compose -f ~/monitoring/docker-compose-monitoring.yml up -d

# Clean Docker system
docker system prune -f --volumes
```

---

## Security Commands

### Check Access Logs
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Failed login attempts
sudo tail -f /var/log/auth.log | grep Failed

# Check for suspicious activity
sudo tail -f /var/forensics/evidence/*/evidence.json | grep -i "security"
```

### Firewall Status
```bash
# Check UFW status (if used)
sudo ufw status verbose

# Check open ports
sudo netstat -tlnp
sudo ss -tlnp
```

---

## Emergency Procedures

### Complete System Failure
```bash
# 1. Check Tailscale connectivity first
tailscale status

# 2. If Server 1 down, restore from Server 2
ssh server2
cd /backups
./FORENSIC_RECOVERY.sh

# 3. If evidence corrupted, verify from backup
python3 scripts/forensic_collector.py verify-all

# 4. If demo broken, use EC2 as fallback
ssh ec2-instance
# Access everything via http://ec2-public-ip/
```

### Demo Day Emergency
```bash
# If home servers unreachable, EC2 fallback
ssh ec2-instance
docker run -d -p 8888:8888 forensic-collector:latest

# Quick evidence generation for demo
curl -X POST http://localhost:8888/trigger/demo_incident

# Backup demo URLs (if main fails)
# Use screenshots in ~/demo-screenshots/
# Use recorded video in ~/demo-video.mp4
```

---

## Git Workflow

### Development Changes
```bash
# Stage changes
git add .

# Commit with good messages
git commit -m "feat: Add new forensic feature

- Enhanced evidence collection
- Added new compliance rules
- Improved DR recovery time

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to repository
git push origin master
```

### Rollback if Needed
```bash
# Check recent commits
git log --oneline -10

# Rollback to previous version
git reset --hard HEAD~1

# Or rollback specific files
git checkout HEAD~1 -- filename
```

---

## Interview Commands Cheat Sheet

### 30-Second Demo Setup
```bash
# Open all demo windows
open http://ec2-public-ip/forensics     # Evidence viewer
open http://ec2-public-ip/              # Grafana dashboards
cat ~/DISASTER_RECOVERY_PROOF.txt | head -5  # DR proof ready
```

### Live Demo Commands
```bash
# Trigger incident during interview
curl -X POST http://localhost:8888/trigger/lims

# Show real-time evidence capture
python3 scripts/forensic_collector.py list

# Verify evidence integrity  
python3 scripts/forensic_collector.py verify $(python3 scripts/forensic_collector.py list | head -2 | tail -1 | cut -d'|' -f1 | xargs)

# Show cost savings
echo "Cloud cost: ~\$500/month | Home lab: ~\$25/month | Savings: 95%"
```

---

## Cost Monitoring

### Monthly Costs Tracking
```bash
# AWS costs (check AWS billing dashboard)
# Expected: ~$8.50/month for t2.micro

# Home electricity estimate
# 2 servers * ~15W avg * 24h * 30d * $0.12/kWh = ~$15/month

# Total: ~$25/month vs ~$500/month cloud equivalent
```

---

## Backup Quick Reference

### Automated Schedule (crontab -e)
```
# Hourly evidence backup
0 * * * * /home/ubuntu/compliance-automation-platform/scripts/backup-forensics.sh

# Daily K3s backup
0 2 * * * /home/ubuntu/compliance-automation-platform/scripts/backup-k3s.sh

# Real-time evidence sync
*/5 * * * * rsync -av /var/forensics/ server2:/forensics-replica/
```

---

## Success Metrics Dashboard

### Pre-Interview Checklist
```bash
# Verify all green
kubectl get pods --all-namespaces | grep -v Running | wc -l    # Should be 0
curl -s http://localhost:8888/health | grep healthy           # Should return healthy
./scripts/disaster-recovery-test.sh | grep "TEST RESULT"      # Should be PASSED
python3 scripts/forensic_collector.py list | wc -l           # Should be >5 incidents
```

**If all commands return expected results, your system is interview-ready!**

---

## Emergency Contacts & Resources

- **Tailscale Support**: https://tailscale.com/contact/support
- **K3s Documentation**: https://docs.k3s.io/
- **AWS Support**: AWS Console → Support
- **GitHub Repository**: https://github.com/GABRIELS562/compliance-automation-platform

---

*Keep this file handy during deployment and interviews. Practice the demo commands until they're muscle memory!*