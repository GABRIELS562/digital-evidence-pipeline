#!/usr/bin/env python3
"""
validate_compliance_rules.py
Validates compliance rules in Ansible playbooks for pharma and finance scenarios.
Outputs a compliance score and missing controls.
"""
import yaml
import sys

REQUIRED_CONTROLS = {
    'pharma': [
        'pharma_signers',
        '/var/log/pharma_audit',
        '/etc/security/pwquality.conf',
        '/var/backups/pharma',
    ],
    'finance': [
        '/finance/sox_data',
        '/finance/payment_card_data',
        '/var/log/finance_db_audit.log',
        '/etc/audit/rules.d/priv_esc.rules',
        '/var/backups/finance',
    ]
}

def parse_playbook(playbook_path):
    with open(playbook_path, 'r') as f:
        return yaml.safe_load(f)

def check_controls(playbook, controls):
    found = 0
    missing = []
    playbook_str = str(playbook)
    for control in controls:
        if control in playbook_str:
            found += 1
        else:
            missing.append(control)
    score = int(100 * found / len(controls))
    return score, missing

def main():
    if len(sys.argv) < 3:
        print("Usage: validate_compliance_rules.py <pharma_playbook.yml> <finance_playbook.yml>")
        sys.exit(1)
    for scenario, playbook_path in zip(['pharma', 'finance'], sys.argv[1:3]):
        playbook = parse_playbook(playbook_path)
        score, missing = check_controls(playbook, REQUIRED_CONTROLS[scenario])
        print(f"{scenario.capitalize()} Compliance Score: {score}")
        if missing:
            print(f"Missing controls: {missing}")
        else:
            print("All required controls present.")

if __name__ == "__main__":
    main() 