# AWS Lightsail deployment for SecVaultDemo
# Usage:
#   cd terraform
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Lightsail instance with Docker
resource "aws_lightsail_instance" "secvault" {
  name              = var.instance_name
  availability_zone = "${var.aws_region}a"
  blueprint_id      = "ubuntu_22_04"
  bundle_id         = var.bundle_id
  key_pair_name     = var.key_pair_name

  user_data = templatefile("${path.module}/scripts/user_data.sh", {
    repo_url    = var.repo_url
    app_dir     = "/opt/secvault"
    domain_name = var.domain_name
  })

  tags = {
    Name        = var.instance_name
    Environment = var.environment
    Project     = "SecVaultDemo"
  }
}

# Static IP for consistent DNS
resource "aws_lightsail_static_ip" "secvault" {
  name = "${var.instance_name}-ip"
}

# Attach static IP to instance
resource "aws_lightsail_static_ip_attachment" "secvault" {
  static_ip_name = aws_lightsail_static_ip.secvault.name
  instance_name  = aws_lightsail_instance.secvault.name
}

# Firewall rules - allow HTTP, HTTPS, and SSH
resource "aws_lightsail_instance_public_ports" "secvault" {
  instance_name = aws_lightsail_instance.secvault.name

  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
    cidrs     = var.ssh_allowed_cidrs
  }

  port_info {
    protocol  = "tcp"
    from_port = 80
    to_port   = 80
    cidrs     = ["0.0.0.0/0"]
  }

  port_info {
    protocol  = "tcp"
    from_port = 443
    to_port   = 443
    cidrs     = ["0.0.0.0/0"]
  }
}
