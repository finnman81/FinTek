# Anchorpoint AWS infrastructure (Phase 0: single-AZ, minimal)
# Requires: AWS provider config, DATABASE_URL built from RDS output

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

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "anchorpoint"
}
