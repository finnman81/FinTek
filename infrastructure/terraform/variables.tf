variable "aws_region" {
  default     = "us-east-1"
  description = "AWS region"
}

variable "environment" {
  default     = "dev"
  description = "Environment name (dev, staging, prod)"
}

variable "db_username" {
  default     = "anchorpoint"
  description = "RDS master username"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "RDS master password"
}

variable "vpc_cidr" {
  default     = "10.0.0.0/16"
  description = "VPC CIDR"
}

variable "domain_name" {
  type        = string
  default     = ""
  description = "Domain name for HTTPS (e.g. anchorpoint.ai). Leave empty to skip ACM/HTTPS setup."
}

variable "api_image_tag" {
  type        = string
  default     = "latest"
  description = "Docker image tag for API and worker containers"
}
