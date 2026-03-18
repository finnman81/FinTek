# Munitor AI Terraform (Phase 0)

- **VPC** + public subnet (single AZ)
- **RDS** Postgres 15, single-AZ, db.t3.small. After first apply, connect and run: `CREATE EXTENSION IF NOT EXISTS vector;`
- **S3** bucket for documents
- **ECS Fargate** cluster + service (API task)
- **ALB** with HTTP listener, health check on `/health`

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- Create ECR repo: `aws ecr create-repository --repository-name munitor-api`

## Usage

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and set `db_password`.
2. `terraform init`
3. `terraform plan`
4. `terraform apply`
5. Set Secrets Manager values for `munitor/database-url` and `munitor/openai-api-key` (or use Terraform `aws_secretsmanager_secret_version` with the RDS URL and your OpenAI key).
6. Build and push image: `docker build -t munitor-api -f ../../infrastructure/docker/Dockerfile ../..` then tag and push to ECR.
7. Update ECS service to pick up new task definition if needed.

## Outputs

- `rds_endpoint` – RDS host:port
- `database_url` – Full Postgres URL (sensitive)
- `s3_bucket_documents` – S3 bucket name
- `alb_dns_name` – ALB DNS for Route53 CNAME
- `alb_url` – http://ALB_DNS
