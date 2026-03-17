# Munitor AI AWS Deployment Guide

Quick reference for deploying Munitor AI on AWS.

---

## AWS Architecture Summary

```
Internet
    │
    ▼
CloudFront (optional CDN)
    │
    ▼
Application Load Balancer (HTTPS)
    │
    ▼
ECS Fargate (FastAPI containers)
    │
    ├──► RDS Postgres (multi-AZ)
    ├──► ElastiCache Redis
    ├──► S3 (document storage)
    └──► Pinecone (external, API)

Frontend: Vercel (or CloudFront + S3)
```

---

## Step-by-Step AWS Setup

### 1. Prerequisites

- AWS account with admin access
- Terraform installed (`brew install terraform` or download from terraform.io)
- AWS CLI configured (`aws configure`)
- Docker installed (for local testing)

### 2. Initial Infrastructure (Terraform)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan (review changes)
terraform plan

# Apply (creates resources)
terraform apply
```

**What gets created**:
- VPC with public/private subnets (2 AZs)
- RDS Postgres instance in private subnet
- ElastiCache Redis in private subnet
- ECS Fargate cluster
- Application Load Balancer
- S3 bucket for documents
- Security groups (ECS → RDS, ECS → Redis, ALB → ECS)
- IAM roles (ECS task execution role, task role)

### 3. Build & Push Docker Image

```bash
# Build image
docker build -t munitor-api:latest -f infrastructure/docker/Dockerfile .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag munitor-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/munitor-api:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/munitor-api:latest
```

### 4. Configure ECS Task Definition

**Environment variables** (set in ECS task definition):
```
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/munitor
OPENAI_API_KEY=<from Secrets Manager>
PINECONE_API_KEY=<from Secrets Manager>
PINECONE_ENVIRONMENT=us-east-1-aws
S3_BUCKET_NAME=munitor-documents-<account-id>
REDIS_URL=redis://elasticache-endpoint:6379
CLERK_SECRET_KEY=<from Secrets Manager>
```

**Secrets Manager**:
- Create secrets: `munitor/openai-api-key`, `munitor/pinecone-api-key`, `munitor/clerk-secret`
- Reference in task definition: `secrets: [{ name: "OPENAI_API_KEY", valueFrom: "arn:aws:secretsmanager:..." }]`

### 5. Deploy ECS Service

```bash
# Update task definition (if changed)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update service (forces new deployment)
aws ecs update-service --cluster munitor --service munitor-api --force-new-deployment
```

### 6. Set Up DNS (Route53)

```bash
# Create hosted zone
aws route53 create-hosted-zone --name api.yourdomain.com --caller-reference $(date +%s)

# Get ALB DNS name from Terraform output
terraform output alb_dns_name

# Create A record (alias to ALB)
aws route53 change-resource-record-sets --hosted-zone-id <zone-id> --change-batch file://dns-record.json
```

### 7. SSL Certificate (ACM)

1. Request certificate in ACM (us-east-1 for CloudFront, or same region as ALB)
2. Validate via DNS (Route53 can auto-create validation records)
3. Attach to ALB listener (HTTPS:443 → target group)

---

## Terraform Module Structure

```hcl
# infrastructure/terraform/main.tf

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

# VPC
module "vpc" {
  source = "./modules/vpc"
  ...
}

# RDS
module "rds" {
  source = "./modules/rds"
  vpc_id = module.vpc.vpc_id
  ...
}

# ECS
module "ecs" {
  source = "./modules/ecs"
  vpc_id = module.vpc.vpc_id
  ...
}

# ALB
module "alb" {
  source = "./modules/alb"
  vpc_id = module.vpc.vpc_id
  ...
}
```

---

## Cost Optimization Tips

1. **RDS**: Use `db.t3.small` for dev, `db.t3.medium` for prod. Enable auto-stop for dev (not multi-AZ).
2. **ECS**: Use Fargate Spot for non-critical workloads (50% savings).
3. **ElastiCache**: Use `cache.t3.micro` for dev, `cache.t3.small` for prod.
4. **S3**: Enable lifecycle policies (move to Glacier after 90 days).
5. **ALB**: Use single ALB for multiple services (path-based routing).

---

## Monitoring & Logging

### CloudWatch

- **ECS logs**: Automatically sent to CloudWatch Logs (`/ecs/munitor-api`)
- **Metrics**: CPU, memory, request count (auto-collected)
- **Alarms**: Set up for high CPU (>80%), memory (>85%), error rate (>5%)

### Sentry (Optional)

- Add Sentry SDK to FastAPI
- Track errors, performance
- Free tier: 5k events/month

---

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml

name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          docker build -t munitor-api:${{ github.sha }} .
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker push $ECR_REGISTRY/munitor-api:${{ github.sha }}
      
      - name: Update ECS service
        run: |
          aws ecs update-service --cluster munitor --service munitor-api --force-new-deployment
```

---

## Security Checklist

- [ ] RDS in private subnet (no public access)
- [ ] ElastiCache in private subnet
- [ ] ECS tasks use IAM task role (least privilege)
- [ ] Secrets in Secrets Manager (not env vars)
- [ ] ALB has WAF rules (rate limiting, SQL injection protection)
- [ ] CloudWatch logs encrypted
- [ ] S3 bucket has versioning + encryption enabled
- [ ] VPC flow logs enabled
- [ ] Regular security group reviews

---

## Troubleshooting

**ECS tasks not starting**:
- Check CloudWatch logs: `/ecs/munitor-api`
- Verify task role has permissions (S3, RDS, Secrets Manager)
- Check health check endpoint (`/health`)

**Database connection errors**:
- Verify security group allows ECS → RDS (port 5432)
- Check `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`
- Test connection from ECS task: `psql $DATABASE_URL`

**High costs**:
- Review CloudWatch metrics (idle resources?)
- Check RDS instance size (right-size)
- Review S3 storage (old documents?)

---

## Next Steps After Deployment

1. **Set up monitoring**: CloudWatch dashboards, alarms
2. **Load testing**: Use Locust or k6 to test API under load
3. **Backup strategy**: RDS automated backups, S3 versioning
4. **Disaster recovery**: Document restore procedure
5. **Scaling**: Configure auto-scaling policies (CPU/memory thresholds)
