variable "aws_region" {
  description = "AWS region for Lightsail instance"
  type        = string
  default     = "us-east-1"
}

variable "instance_name" {
  description = "Name for the Lightsail instance"
  type        = string
  default     = "secvault-prod"
}

variable "bundle_id" {
  description = "Lightsail bundle (instance size)"
  type        = string
  default     = "nano_3_0" # $5/month, 1GB RAM - use "micro_3_0" for $3.50/512MB
}

variable "key_pair_name" {
  description = "Name of Lightsail SSH key pair (create in AWS console first)"
  type        = string
}

variable "repo_url" {
  description = "Git repository URL to clone"
  type        = string
  default     = "https://github.com/yourusername/SecVaultDemo.git"
}

variable "domain_name" {
  description = "Domain name for SSL certificate (optional, leave empty to skip)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "production"
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this to your IP in production!
}
