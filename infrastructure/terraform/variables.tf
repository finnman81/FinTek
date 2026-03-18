variable "aws_region" {
  default     = "us-east-1"
  description = "AWS region"
}

variable "environment" {
  default     = "dev"
  description = "Environment name"
}

variable "db_username" {
  default     = "munitor"
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
