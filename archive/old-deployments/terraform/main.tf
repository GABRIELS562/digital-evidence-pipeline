###############################
# Compliance Platform on AWS  #
###############################
# This Terraform config demonstrates:
# - ECS service for container orchestration
# - Application Load Balancer for secure access
# - AWS Config for cloud compliance monitoring
# - CloudTrail for audit logging
# - Security Groups with least privilege

provider "aws" {
  region = var.aws_region
}

###############################
# VPC and Networking
###############################
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "compliance-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[0]
  tags = { Name = "compliance-public-subnet" }
}

data "aws_availability_zones" "available" {}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

###############################
# Security Groups (Least Privilege)
###############################
resource "aws_security_group" "ecs_service" {
  name        = "compliance-ecs-sg"
  description = "Allow only necessary inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow HTTP from ALB"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alb" {
  name        = "compliance-alb-sg"
  description = "Allow HTTP from the internet"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

###############################
# ECS Cluster and Service
###############################
resource "aws_ecs_cluster" "compliance" {
  name = "compliance-cluster"
}

resource "aws_ecs_task_definition" "compliance" {
  family                   = "compliance-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  container_definitions    = jsonencode([
    {
      name      = "compliance-monitor"
      image     = var.compliance_monitor_image
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = [
        { name = "PROMETHEUS_ENDPOINT", value = "http://prometheus:9090" },
        { name = "ELASTICSEARCH_ENDPOINT", value = "http://elasticsearch:9200" }
      ]
    }
  ])
}

resource "aws_ecs_service" "compliance" {
  name            = "compliance-service"
  cluster         = aws_ecs_cluster.compliance.id
  task_definition = aws_ecs_task_definition.compliance.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = [aws_subnet.public.id]
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.compliance.arn
    container_name   = "compliance-monitor"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.http]
}

###############################
# Application Load Balancer
###############################
resource "aws_lb" "compliance" {
  name               = "compliance-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public.id]
}

resource "aws_lb_target_group" "compliance" {
  name     = "compliance-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  health_check {
    path                = "/metrics"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.compliance.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.compliance.arn
  }
}

###############################
# IAM Roles for ECS and Compliance
###############################
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

###############################
# AWS Config for Cloud Compliance
###############################
resource "aws_config_configuration_recorder" "main" {
  name     = "compliance-recorder"
  role_arn = aws_iam_role.config.arn
}

resource "aws_iam_role" "config" {
  name = "awsConfigRole"
  assume_role_policy = data.aws_iam_policy_document.config_assume_role.json
}

data "aws_iam_policy_document" "config_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "config_policy" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
}

resource "aws_config_delivery_channel" "main" {
  name           = "compliance-delivery"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket
  depends_on     = [aws_config_configuration_recorder.main]
}

resource "aws_s3_bucket" "config_logs" {
  bucket = "compliance-config-logs-${random_id.suffix.hex}"
  force_destroy = true
}

resource "random_id" "suffix" {
  byte_length = 4
}

###############################
# CloudTrail for Audit Logging
###############################
resource "aws_cloudtrail" "main" {
  name                          = "compliance-cloudtrail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.bucket
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}

resource "aws_s3_bucket" "cloudtrail_logs" {
  bucket = "compliance-cloudtrail-logs-${random_id.suffix.hex}"
  force_destroy = true
}

###############################
# Variables
###############################
variable "aws_region" {
  description = "AWS region to deploy resources in"
  default     = "us-east-1"
}

variable "compliance_monitor_image" {
  description = "Docker image for the compliance monitor service"
} 