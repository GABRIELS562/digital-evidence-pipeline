#!/bin/bash
# Integration test for full compliance pipeline
set -e

# Run Molecule tests for pharma and finance playbooks
molecule test -s pharma-compliance
molecule test -s finance-compliance

# Validate compliance rules
python3 tests/validate_compliance_rules.py playbooks/pharma-compliance.yml playbooks/finance-compliance.yml

echo "\nFull compliance pipeline integration test completed successfully." 