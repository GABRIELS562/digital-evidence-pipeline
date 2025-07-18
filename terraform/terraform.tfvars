# AWS Configuration
aws_region = "us-east-1"

# Docker Image Configuration
# Replace with your actual ECR repository URL or Docker Hub image
compliance_monitor_image = "compliance-monitor:latest"

# Optional: Override default values
# Uncomment and modify as needed:

# Alternative regions for compliance requirements
# aws_region = "us-west-2"  # For California compliance
# aws_region = "eu-west-1"  # For GDPR compliance

# Production image examples:
# compliance_monitor_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/compliance-monitor:v1.0.0"
# compliance_monitor_image = "yourdockerhub/compliance-monitor:latest"