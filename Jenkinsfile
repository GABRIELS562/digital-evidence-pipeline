pipeline {
    agent any

    environment {
        // Define environment variables for playbooks, scripts, and Docker images
        PHARMA_PLAYBOOK = 'playbooks/pharma-compliance.yml'
        FINANCE_PLAYBOOK = 'playbooks/finance-compliance.yml'
        COMPLIANCE_IMAGE = 'compliance-monitor:latest'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Automated Playbook Testing') {
            steps {
                sh 'cd tests && ./test_pipeline_integration.sh'
            }
        }

        stage('Security Scanning') {
            parallel {
                stage('YAML Lint') {
                    steps {
                        sh 'yamllint playbooks/'
                    }
                }
                stage('Python Lint & Scan') {
                    steps {
                        sh 'pylint scripts/*.py || true'
                        sh 'bandit -r scripts/'
                    }
                }
                stage('Docker Image Scan') {
                    steps {
                        sh 'docker build -t $COMPLIANCE_IMAGE -f docker/Dockerfile.compliance-monitor .'
                        sh 'trivy image $COMPLIANCE_IMAGE || true'
                    }
                }
            }
        }

        stage('Compliance Validation') {
            steps {
                sh 'python3 tests/validate_compliance_rules.py $PHARMA_PLAYBOOK $FINANCE_PLAYBOOK'
            }
        }

        stage('Deploy to Dev') {
            steps {
                sh 'cd terraform && terraform workspace select dev || terraform workspace new dev'
                sh 'terraform apply -auto-approve'
            }
        }

        stage('Approval for Staging') {
            steps {
                input message: 'Approve deployment to Staging?', ok: 'Deploy to Staging'
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh 'cd terraform && terraform workspace select staging || terraform workspace new staging'
                sh 'terraform apply -auto-approve'
            }
        }

        stage('Approval for Production') {
            steps {
                input message: 'Approve deployment to Production?', ok: 'Deploy to Production'
            }
        }

        stage('Deploy to Production') {
            steps {
                sh 'cd terraform && terraform workspace select prod || terraform workspace new prod'
                sh 'terraform apply -auto-approve'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'tests/**,playbooks/**,scripts/**,dashboards/**,terraform/**', allowEmptyArchive: true
            junit 'tests/**/*.xml'
        }
        failure {
            mail to: 'compliance-team@example.com', subject: 'Compliance Pipeline Failed', body: 'Check Jenkins for details.'
        }
    }
} 