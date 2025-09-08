# ARCHIVED FILES

This directory contains old deployment files that are no longer needed for the current deployment.

## Contents:
- `old-deployments/` - Previous deployment configurations, scripts, and manifests
- `playbooks/` - Ansible playbooks (superseded by K3s and Docker deployments)
- `tests/` - Old test files (superseded by disaster recovery testing)
- `sre/` - Old SRE configs (integrated into main deployment)
- `terraform/` - Old terraform (too expensive, using home servers + EC2)

## Current Active Files:
- `DEPLOYMENT_GUIDE.md` - Complete step-by-step deployment
- `QUICK_REFERENCE.md` - Popular commands and shortcuts
- `UNIFIED_PORTFOLIO_PLAN.md` - Master reference
- `kubernetes/forensic-collector-daemonset.yaml` - K3s deployment
- `docker/Dockerfile.forensic` - Forensic collector image
- `scripts/forensic_*.py` - Core forensic system
- `scripts/backup-*.sh` - Backup and DR scripts

These archived files are kept for reference but are not needed for deployment.