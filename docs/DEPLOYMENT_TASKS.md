# Deployment Tasks: Weeks 1-2

## Pre-Flight: Issues in Current Terraform

Before `terraform apply` will succeed, these issues in the existing configs must be fixed:

| Issue | File | Problem | Fix |
|-------|------|---------|-----|
| ALB needs 2 AZs | `vpc.tf`, `alb.tf` | ALB requires subnets in at least 2 availability zones; only `public_a` exists | Add `public_b` subnet in AZ `us-east-1b`, reference both in ALB |
| RDS subnet group needs 2 AZs | `rds.tf` | `aws_db_subnet_group` has only 1 subnet; AWS requires at least 2 | Add `public_b` to subnet group |
| No ECR repository | `ecs.tf` | Task definition references ECR image but no `aws_ecr_repository` resource exists | Add ECR resource |
| No HTTPS | `alb.tf` | Only HTTP:80 listener; no ACM certificate or HTTPS:443 listener | Add ACM cert + HTTPS listener + HTTP→HTTPS redirect |
| No worker task | `ecs.tf` | Only API task definition; ingestion worker needs its own task/service | Add worker task definition + ECS service |
| No outputs file | - | Terraform outputs scattered across files; no centralized reference | Add `outputs.tf` |
| No tfvars example | - | `db_password` is required but no example tfvars file | Add `terraform.tfvars.example` |
| No Terraform state backend | `main.tf` | State stored locally; will be lost if machine changes | Add S3 backend for state (optional for Phase 0) |

---

## Task Breakdown

### Task 1: Fix Terraform Infrastructure

**Goal**: Make `terraform plan` and `terraform apply` work cleanly.

#### 1.1 VPC: Add second availability zone

`infrastructure/terraform/vpc.tf` — add:
- `aws_subnet.public_b` in `us-east-1b`
- Route table association for `public_b`

#### 1.2 ECR: Add container registry

New file `infrastructure/terraform/ecr.tf`:
- `aws_ecr_repository` for the API/worker image
- Lifecycle policy to keep only last 10 images (cost control)

#### 1.3 ALB: HTTPS support

`infrastructure/terraform/alb.tf` — add:
- `aws_acm_certificate` with DNS validation
- `aws_lb_listener.https` on port 443 forwarding to target group
- Change HTTP listener to redirect to HTTPS
- Reference both subnets in ALB

Note: ACM cert validation requires a domain. Add `var.domain_name` to `variables.tf`.
If no domain yet, keep HTTP-only initially and add HTTPS when domain is ready.

#### 1.4 RDS: Fix subnet group

`infrastructure/terraform/rds.tf`:
- Add `public_b` subnet to `aws_db_subnet_group`

#### 1.5 ECS: Worker service + separate task definitions

`infrastructure/terraform/ecs.tf` — add:
- `aws_ecs_task_definition.worker` (lower resources: 0.25 vCPU, 0.5 GB)
  - Entrypoint override: `python -m src.workers.ingestion_worker`
- `aws_ecs_service.worker` (desired_count=1, no load balancer)

#### 1.6 Variables + outputs

`infrastructure/terraform/variables.tf` — add:
- `var.domain_name` (optional, for ACM/Route53)
- `var.api_image_tag` (default "latest")

New file `infrastructure/terraform/outputs.tf`:
- Consolidate all outputs (ALB URL, RDS endpoint, S3 bucket, ECR repo URL)

New file `infrastructure/terraform/terraform.tfvars.example`:
- Document required variables with placeholder values

---

### Task 2: Docker Compose for Local Dev

**Goal**: One-command local environment that mirrors production.

New file `docker-compose.yml` at project root:

```yaml
services:
  db:
    image: pgvector/pgvector:pg15
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: anchorpoint
      POSTGRES_USER: anchorpoint
      POSTGRES_PASSWORD: localdev
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile
    ports: ["8000:8000"]
    env_file: .env
    environment:
      DATABASE_URL: postgresql://anchorpoint:localdev@db:5432/anchorpoint
    depends_on: [db]

  worker:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile
    command: python -m src.workers.ingestion_worker
    env_file: .env
    environment:
      DATABASE_URL: postgresql://anchorpoint:localdev@db:5432/anchorpoint
    depends_on: [db]

volumes:
  pgdata:
```

The frontend (`web/`) runs separately via `npm run dev` (hot reload is more useful than containerizing it during development).

---

### Task 3: Next.js Production Build Config

**Goal**: Frontend builds for production hosting on AWS Amplify.

#### 3.1 Standalone output mode

`web/next.config.mjs`:
- Add `output: 'standalone'` for Docker/Amplify compatibility
- Make `API_BACKEND_URL` configurable for production (rewrite target)

#### 3.2 Amplify build spec

New file `web/amplify.yml`:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
```

#### 3.3 Environment variables for Amplify

Amplify needs these env vars set in the console:
- `API_BACKEND_URL` → ALB URL (e.g., `https://api.yourdomain.com`)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` → Clerk publishable key

---

### Task 4: GitHub Actions Deploy Workflow

**Goal**: Push to `main` auto-deploys backend to ECS.

New file `.github/workflows/deploy.yml`:

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1

      - name: Login to ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push image
        env:
          ECR_REGISTRY: ${{ steps.ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/anchorpoint-api:$IMAGE_TAG \
                        -t $ECR_REGISTRY/anchorpoint-api:latest \
                        -f infrastructure/docker/Dockerfile .
          docker push $ECR_REGISTRY/anchorpoint-api --all-tags

      - name: Deploy API to ECS
        run: |
          aws ecs update-service \
            --cluster anchorpoint-cluster \
            --service anchorpoint-api \
            --force-new-deployment

      - name: Deploy Worker to ECS
        run: |
          aws ecs update-service \
            --cluster anchorpoint-cluster \
            --service anchorpoint-worker \
            --force-new-deployment
```

Note: Uses OIDC role assumption (no long-lived keys). Requires setting up an IAM OIDC provider for GitHub Actions in AWS.

---

### Task 5: Database Migration on First Deploy

**Goal**: RDS has the schema + pgvector extension ready.

After `terraform apply` creates the RDS instance:

1. Connect to RDS from a machine with network access (or temporarily from local if publicly accessible)
2. Run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run Alembic migrations:
   ```bash
   DATABASE_URL=postgresql://... alembic upgrade head
   ```

For subsequent deploys, Alembic migrations should run as part of the ECS task startup or as a pre-deploy step in CI/CD. Options:
- **Option A**: Add migration command to Dockerfile entrypoint (simple, works for single-task deploys)
- **Option B**: Run as a one-off ECS task in the deploy workflow (cleaner, avoids race conditions with multiple tasks)

Recommend **Option B** for production.

---

### Task 6: DNS + SSL Setup

**Goal**: `api.yourdomain.com` → ALB, `app.yourdomain.com` → Amplify.

#### If you have a domain:

1. Create Route 53 hosted zone for your domain
2. Point domain registrar nameservers to Route 53
3. Add Terraform resources:
   - `aws_acm_certificate` for `*.yourdomain.com`
   - `aws_route53_record` for ACM DNS validation
   - `aws_route53_record` A-alias `api.yourdomain.com` → ALB
4. Amplify handles `app.yourdomain.com` SSL automatically when you add a custom domain in the Amplify console

#### If no domain yet:

- Use the ALB DNS name directly (e.g., `anchorpoint-alb-123456.us-east-1.elb.amazonaws.com`)
- Amplify provides a default `*.amplifyapp.com` URL
- Add DNS/SSL later without any code changes

---

### Task 7: Secrets Manager Population

**Goal**: Secrets stored securely, referenced by ECS tasks.

Terraform creates empty secret shells. Populate them manually (one-time):

```bash
# Database URL (constructed from RDS output)
aws secretsmanager put-secret-value \
  --secret-id anchorpoint/database-url \
  --secret-string "postgresql://anchorpoint:<password>@<rds-endpoint>:5432/anchorpoint"

# OpenAI API key
aws secretsmanager put-secret-value \
  --secret-id anchorpoint/openai-api-key \
  --secret-string "<your-openai-key>"
```

If you use Clerk in production, add a third secret for `CLERK_SECRET_KEY`.

---

### Task 8: Smoke Test

**Goal**: Verify the full pipeline works end-to-end on AWS.

Checklist:
- [ ] ALB health check passes (`/health` returns 200)
- [ ] Frontend loads at Amplify URL
- [ ] Frontend can reach API through ALB
- [ ] Upload a document → ingestion job created
- [ ] Worker picks up job → document chunked + embedded
- [ ] Ask a question → get a RAG answer with citations
- [ ] CloudWatch logs appear for API + worker
- [ ] Verify tenant isolation (if multiple tenants seeded)

---

## Execution Order

```
Week 1:
  Day 1-2: Task 1 (Fix Terraform)
  Day 2:   Task 2 (Docker Compose)
  Day 3:   Task 3 (Next.js production config)
  Day 3:   Task 1 → terraform apply
  Day 4:   Task 5 (Database migration)
  Day 4:   Task 7 (Secrets)
  Day 5:   Task 6 (DNS/SSL — if domain ready)

Week 2:
  Day 1:   Task 4 (GitHub Actions deploy)
  Day 1-2: Amplify setup (console, connect repo)
  Day 3:   Task 8 (Smoke test)
  Day 4-5: Fix issues found in smoke test
```

---

## AWS Resources Checklist (what `terraform apply` creates)

- [ ] VPC with 2 public subnets (us-east-1a, us-east-1b)
- [ ] Internet gateway + route tables
- [ ] ALB with HTTP listener (HTTPS when domain ready)
- [ ] ALB security group (80, 443 inbound)
- [ ] ECS cluster
- [ ] ECR repository
- [ ] ECS task definition: API (0.5 vCPU, 1 GB)
- [ ] ECS task definition: Worker (0.25 vCPU, 0.5 GB)
- [ ] ECS service: API (desired_count=1, behind ALB)
- [ ] ECS service: Worker (desired_count=1, no ALB)
- [ ] ECS security group (8000 from ALB only)
- [ ] IAM: ECS execution role (ECR pull, Secrets Manager read, CloudWatch logs)
- [ ] IAM: ECS task role (S3 read/write)
- [ ] RDS PostgreSQL 15 (db.t3.small, single-AZ, 20 GB)
- [ ] RDS security group (5432 from VPC)
- [ ] RDS subnet group (2 subnets)
- [ ] RDS parameter group (pg15)
- [ ] S3 bucket (documents, versioning + encryption enabled, public access blocked)
- [ ] Secrets Manager: database-url, openai-api-key
- [ ] CloudWatch log group

---

## Step-by-Step Runbook

Follow these steps in order. Each step assumes the previous one succeeded.

### Step 1: Prerequisites

```bash
# Verify tools installed
terraform --version    # >= 1.0
aws --version          # AWS CLI v2
docker --version       # Docker Desktop or Engine

# Configure AWS CLI (if not already done)
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)

# Verify AWS access
aws sts get-caller-identity
```

### Step 2: Create Terraform variables file

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set a strong db_password
```

### Step 3: Deploy infrastructure

```bash
cd infrastructure/terraform

terraform init
terraform plan          # Review — should show ~20 resources to create
terraform apply         # Type "yes" to confirm

# Save outputs for later steps
terraform output -json > ../../deployment-outputs.json
```

### Step 4: Build and push first Docker image

```bash
# Get values from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)
AWS_REGION=us-east-1

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URL

# Build and push from project root
cd ../..
docker build -t $ECR_URL:latest -f infrastructure/docker/Dockerfile .
docker push $ECR_URL:latest
```

### Step 5: Populate secrets

```bash
RDS_ENDPOINT=$(cd infrastructure/terraform && terraform output -raw rds_endpoint)

aws secretsmanager put-secret-value \
  --secret-id anchorpoint/database-url \
  --secret-string "postgresql://anchorpoint:YOUR_DB_PASSWORD@$RDS_ENDPOINT/anchorpoint"

aws secretsmanager put-secret-value \
  --secret-id anchorpoint/openai-api-key \
  --secret-string "sk-your-openai-key-here"
```

### Step 6: Initialize database

```bash
# Connect to RDS and enable pgvector
psql "postgresql://anchorpoint:YOUR_DB_PASSWORD@$RDS_ENDPOINT/anchorpoint" \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
DATABASE_URL="postgresql://anchorpoint:YOUR_DB_PASSWORD@$RDS_ENDPOINT/anchorpoint" \
  alembic upgrade head
```

### Step 7: Force ECS redeploy (picks up secrets + image)

```bash
aws ecs update-service --cluster anchorpoint-cluster --service anchorpoint-api --force-new-deployment
aws ecs update-service --cluster anchorpoint-cluster --service anchorpoint-worker --force-new-deployment

# Wait for services to stabilize
aws ecs wait services-stable --cluster anchorpoint-cluster --services anchorpoint-api
```

### Step 8: Verify API

```bash
ALB_URL=$(cd infrastructure/terraform && terraform output -raw alb_url)
curl $ALB_URL/health
# Expected: {"status":"ok","version":"1.0.0"}
```

### Step 9: Set up Amplify Hosting (AWS Console)

1. Go to AWS Amplify Console → "Host web app"
2. Connect to GitHub → select FinTek repo
3. Set branch: `main`, app root: `web/`
4. Amplify should auto-detect `amplify.yml` build spec
5. Add environment variables:
   - `API_BACKEND_URL` = `http://<ALB_DNS_NAME>` (from terraform output)
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` = your Clerk key (if using Clerk)
6. Deploy

### Step 10: Set up GitHub Actions CI/CD

1. In AWS IAM, create an OIDC identity provider for GitHub Actions
2. Create an IAM role `anchorpoint-github-deploy` with permissions:
   - `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`,
     `ecr:PutImage`, `ecr:InitiateLayerUpload`, etc.
   - `ecs:UpdateService`, `ecs:DescribeServices`
3. In GitHub repo Settings → Secrets → Actions:
   - Add `AWS_DEPLOY_ROLE_ARN` = the role ARN from step 2

### Step 11: Smoke test (full pipeline)

- [ ] `curl <ALB_URL>/health` returns 200
- [ ] Amplify URL loads the frontend
- [ ] Chat page can send a question and get a response
- [ ] Upload a document → check worker logs in CloudWatch
- [ ] Ask a question about the uploaded document → get cited answer
- [ ] Check CloudWatch log groups for `/ecs/anchorpoint` logs
