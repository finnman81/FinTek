# AWS Deployment Guide — Munitor AI Industrial Knowledge Base

This guide covers every step required to deploy the Munitor AI industrial RAG knowledge base to AWS using CDK. It assumes you have the CDK code implemented under `infrastructure/cdk/` and are deploying to the multi-account structure described below.

## Table of Contents

1. [Account Structure](#1-account-structure)
2. [Prerequisites](#2-prerequisites)
3. [Configuration — Replace Placeholder Values](#3-configuration--replace-placeholder-values)
4. [Azure AD / Entra ID App Registration](#4-azure-ad--entra-id-app-registration)
5. [GitHub OIDC Provider Setup](#5-github-oidc-provider-setup)
6. [SCP Updates](#6-scp-updates)
7. [CDK Bootstrap](#7-cdk-bootstrap)
8. [Build and Push Initial Docker Image](#8-build-and-push-initial-docker-image)
9. [Deploy Dev Environment](#9-deploy-dev-environment)
10. [Populate Secrets](#10-populate-secrets)
11. [Run Database Migrations](#11-run-database-migrations)
12. [Frontend Setup](#12-frontend-setup)
13. [Verify Dev Deployment](#13-verify-dev-deployment)
14. [Deploy Prod Environment](#14-deploy-prod-environment)
15. [DNS Validation](#15-dns-validation)
16. [CI/CD Pipeline Activation](#16-cicd-pipeline-activation)
17. [Post-Deployment Checklist](#17-post-deployment-checklist)
18. [Rollback Procedures](#18-rollback-procedures)
19. [Cost Monitoring](#19-cost-monitoring)

---

## 1. Account Structure

The deployment uses four AWS accounts in an AWS Organizations structure:

| Account | Account ID (placeholder) | Purpose |
|---------|--------------------------|---------|
| Shared Services | `555555555555` | ECR repository, Route53 hosted zone, GitHub OIDC provider, CI/CD IAM roles |
| Industrial-Dev | `666666666666` | Dev environment (VPC, RDS, App Runner, Lambda, S3, Amplify, etc.) |
| Industrial-Prod | `777777777777` | Prod environment (same stack set as dev) |
| Log Archive | `444444444444` | Audit log S3 bucket (`munitor-audit-logs`) |

All resources deploy to `us-east-1`.

---

## 2. Prerequisites

Before starting deployment, ensure you have:

### Local Tools
- Python 3.11+
- Node.js 18+ and npm
- AWS CDK CLI: `npm install -g aws-cdk`
- AWS CLI v2 configured with profiles for each account
- Docker (for building container images)
- Git

### AWS Access
- Admin or PowerUser access to all four accounts
- Ability to modify SCPs in the Organizations management account
- Access to create IAM OIDC providers in Shared Services

### External Services
- GitHub repository (`munitor-ai/industrial-kb` or your actual repo name)
- OpenAI API key with access to `text-embedding-3-small`
- Microsoft Entra ID (Azure AD) tenant with admin access to register applications
- Domain `munitor.ai` with a Route53 hosted zone in the Shared Services account

### Install CDK Dependencies
```bash
cd infrastructure/cdk
pip install -r requirements.txt
```

### Verify Tests Pass
```bash
cd infrastructure/cdk
python -m pytest tests/ -v --tb=short
```

All 145 CDK tests should pass before proceeding.

---

## 3. Configuration — Replace Placeholder Values

### 3.1 Account IDs

Edit `infrastructure/cdk/stacks/config.py` and replace all placeholder account IDs:

```python
# Replace these with your real account IDs
INDUSTRIAL_DEV = EnvironmentConfig(
    env_name='dev',
    account_id='YOUR_DEV_ACCOUNT_ID',    # was 666666666666
    ...
)

INDUSTRIAL_PROD = EnvironmentConfig(
    env_name='prod',
    account_id='YOUR_PROD_ACCOUNT_ID',   # was 777777777777
    ...
)

SHARED_SERVICES_ACCOUNT = 'YOUR_SHARED_SERVICES_ACCOUNT_ID'  # was 555555555555
LOG_ARCHIVE_ACCOUNT = 'YOUR_LOG_ARCHIVE_ACCOUNT_ID'          # was 444444444444
```

### 3.2 GitHub Repository

Update the `GITHUB_REPO` constant to match your actual GitHub repository:

```python
GITHUB_REPO = 'your-org/your-repo-name'  # was munitor-ai/industrial-kb
```

### 3.3 Route53 Hosted Zone ID

Edit `infrastructure/cdk/stacks/dns_stack.py` and replace the placeholder hosted zone ID:

```python
_HOSTED_ZONE_ID = "YOUR_REAL_HOSTED_ZONE_ID"  # was Z0123456789ABCDEFGHIJ
```

To find your hosted zone ID:
```bash
aws route53 list-hosted-zones-by-name \
  --dns-name munitor.ai \
  --profile shared-services \
  --query 'HostedZones[0].Id' \
  --output text
```

### 3.4 Domain Prefixes

If your domain structure differs from `munitor.ai`, update the `api_domain_prefix`, `app_domain_prefix`, and `HOSTED_ZONE_NAME` in `config.py`.

### 3.5 Re-run Tests After Config Changes

```bash
cd infrastructure/cdk
python -m pytest tests/ -v --tb=short
```

---

## 4. Azure AD / Entra ID App Registration

### 4.1 Register the Application

1. Go to Azure Portal → Azure Active Directory → App registrations → New registration
2. Name: `Munitor AI Industrial`
3. Supported account types: Single tenant (your organization only)
4. Redirect URIs:
   - Web: `https://app.industrial-dev.munitor.ai/api/auth/callback/azure-ad` (dev)
   - Web: `https://app.industrial.munitor.ai/api/auth/callback/azure-ad` (prod)
   - Web: `http://localhost:3000/api/auth/callback/azure-ad` (local dev)

### 4.2 Create Client Secret

1. Go to Certificates & secrets → New client secret
2. Description: `Munitor AI Industrial`
3. Expiry: 24 months
4. Copy the secret value immediately (you won't see it again)

### 4.3 Record These Values

You will need these for Secrets Manager:
- Application (client) ID → `ENTRA_CLIENT_ID`
- Client secret value → `ENTRA_CLIENT_SECRET`
- Directory (tenant) ID → `ENTRA_TENANT_ID`

### 4.4 Configure Token Claims

1. Go to Token configuration → Add optional claim
2. Token type: ID
3. Add claims: `email`, `preferred_username`

### 4.5 API Permissions

1. Go to API permissions
2. Ensure `Microsoft Graph > User.Read` is granted
3. Grant admin consent for your organization

---

## 5. GitHub OIDC Provider — Reuse Existing (Do NOT Recreate)

The ECR stack's IAM roles trust GitHub's OIDC provider. AWS allows only one OIDC provider per URL per account. If you're deploying into the same Shared Services account as the Schools project, the provider already exists.

The Fin-Tek ECR stack correctly uses `from_open_id_connect_provider_arn` to import the existing provider by ARN — it does not create a new one. No action needed if the provider exists.

Verify it exists:
```bash
aws iam list-open-id-connect-providers \
  --profile shared-services
```

The ARN should be: `arn:aws:iam::<SHARED_SERVICES_ACCOUNT>:oidc-provider/token.actions.githubusercontent.com`

If it does NOT exist (fresh account with no Schools deployment), create it:
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile shared-services
```

---

## 6. SCP Updates

The workload accounts need permission to use Lambda, SQS, Step Functions, and EventBridge. The current `WorkloadServiceRestriction` SCP allowlist includes: `apprunner, amplify, secretsmanager, ecr, cloudwatch, logs, s3, rds, ec2, elasticloadbalancing, iam, sts, organizations, cloudformation, ssm, kms, sns, tag`.

Lambda and SQS are missing. This is a deployment blocker.

In your shared infrastructure repo, update the `AllowApprovedServices` statement in `scp-stack.ts` to add:

- `lambda:*`
- `sqs:*`
- `states:*`
- `events:*`

This won't affect the Schools workload since it doesn't use these services.

See `infrastructure/cdk/docs/scp-changes.md` for the full reference.

Deploy the SCP changes before deploying CDK stacks.

---

## 6.1. Audit Log Bucket Policy (Log Archive Account)

The `munitor-audit-logs` S3 bucket in the Log Archive account needs a bucket policy allowing the Industrial audit forwarder Lambda to write to it. The current bucket policy only has CloudTrail write permissions and a deny-delete policy.

Add a statement to the bucket policy in `log-archive-stack.ts` (shared infra repo):

```json
{
  "Sid": "AllowIndustrialAuditForwarder",
  "Effect": "Allow",
  "Principal": {
    "AWS": [
      "arn:aws:iam::YOUR_DEV_ACCOUNT:role/industrial-dev-audit-log-forwarder-role",
      "arn:aws:iam::YOUR_PROD_ACCOUNT:role/industrial-prod-audit-log-forwarder-role"
    ]
  },
  "Action": "s3:PutObject",
  "Resource": "arn:aws:s3:::munitor-audit-logs/industrial-*"
}
```

Without this, the audit log forwarder Lambda will get `AccessDenied` when writing to the bucket.

---

## 6.2. Document VPC CIDR Allocations

The Industrial workload uses VPC CIDR `10.1.0.0/16`. To avoid future conflicts if other workloads add VPCs, document the allocation:

| CIDR | Workload | Status |
|------|----------|--------|
| `10.1.0.0/16` | Industrial (Fin-Tek) | Active |
| `10.2.0.0/16` | Schools | Reserved (future) |
| `10.3.0.0/16` | Available | — |

Schools doesn't currently deploy a VPC (it uses App Runner's default egress), but if one is added later, use a non-overlapping CIDR. Record this in the shared infra repo's README or a dedicated `network-allocations.md`.

---

## 7. CDK Bootstrap

Bootstrap CDK in all three deployment accounts. Each bootstrap command must be run with credentials for the target account.

### 7.1 Bootstrap Shared Services Account

```bash
cdk bootstrap aws://YOUR_SHARED_SERVICES_ACCOUNT/us-east-1 \
  --profile shared-services \
  --trust YOUR_DEV_ACCOUNT,YOUR_PROD_ACCOUNT \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

### 7.2 Bootstrap Dev Account

```bash
cdk bootstrap aws://YOUR_DEV_ACCOUNT/us-east-1 \
  --profile industrial-dev \
  --trust YOUR_SHARED_SERVICES_ACCOUNT \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

### 7.3 Bootstrap Prod Account

```bash
cdk bootstrap aws://YOUR_PROD_ACCOUNT/us-east-1 \
  --profile industrial-prod \
  --trust YOUR_SHARED_SERVICES_ACCOUNT \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

---

## 8. Build and Push Initial Docker Image

App Runner and the ingestion Lambda both pull from the `industrial-api` ECR repository. You need at least one image before the first CDK deploy.

### 8.1 Deploy ECR Stack First

```bash
cd infrastructure/cdk
cdk deploy industrial-ecr --profile shared-services --require-approval never
```

### 8.2 Authenticate to ECR

```bash
aws ecr get-login-password --region us-east-1 --profile shared-services | \
  docker login --username AWS --password-stdin \
  YOUR_SHARED_SERVICES_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
```

### 8.3 Build and Push

```bash
cd /path/to/project/root
docker build -f infrastructure/docker/Dockerfile -t industrial-api .
docker tag industrial-api:latest \
  YOUR_SHARED_SERVICES_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/industrial-api:latest
docker push \
  YOUR_SHARED_SERVICES_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/industrial-api:latest
```

---

## 9. Deploy Dev Environment

Deploy stacks in dependency order. The CDK handles cross-stack references, but deploying in order helps catch issues early.

### 9.1 Deploy All Dev Stacks

```bash
cd infrastructure/cdk

# Deploy foundational stacks
cdk deploy industrial-dev-vpc --profile industrial-dev --require-approval never
cdk deploy industrial-dev-secrets --profile industrial-dev --require-approval never
cdk deploy industrial-dev-s3 --profile industrial-dev --require-approval never

# Deploy dependent stacks
cdk deploy industrial-dev-rds --profile industrial-dev --require-approval never
cdk deploy industrial-dev-ingestion --profile industrial-dev --require-approval never
cdk deploy industrial-dev-app-runner --profile industrial-dev --require-approval never

# Deploy frontend and wiring
cdk deploy industrial-dev-amplify --profile industrial-dev --require-approval never
cdk deploy industrial-dev-dns --profile industrial-dev --require-approval never
cdk deploy industrial-dev-observability --profile industrial-dev --require-approval never
```

Or deploy everything at once:
```bash
cdk deploy --all --profile industrial-dev --require-approval never
```

### 9.2 Verify Stack Outputs

After deployment, note the outputs:
- App Runner service URL
- RDS endpoint
- S3 bucket name
- SQS queue URL

---

## 10. Populate Secrets

CDK creates the Secrets Manager secrets with empty/placeholder values. You must populate them with real credentials.

### 10.1 Database URL

After RDS deploys, get the endpoint:
```bash
aws rds describe-db-instances \
  --db-instance-identifier industrial-dev-db \
  --profile industrial-dev \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

Then set the secret:
```bash
aws secretsmanager put-secret-value \
  --secret-id industrial-dev/database-url \
  --secret-string "postgresql://munitor:YOUR_PASSWORD@ENDPOINT:5432/munitor" \
  --profile industrial-dev
```

Note: The RDS master password is auto-generated by CDK. Retrieve it from the RDS console or the auto-generated secret.

### 10.2 OpenAI API Key

```bash
aws secretsmanager put-secret-value \
  --secret-id industrial-dev/openai-api-key \
  --secret-string "sk-YOUR_OPENAI_KEY" \
  --profile industrial-dev
```

### 10.3 CORS Origins

```bash
aws secretsmanager put-secret-value \
  --secret-id industrial-dev/cors-origins \
  --secret-string "https://app.industrial-dev.munitor.ai,http://localhost:3000" \
  --profile industrial-dev
```

### 10.4 Entra ID Credentials

```bash
aws secretsmanager put-secret-value \
  --secret-id industrial-dev/entra-client-id \
  --secret-string "YOUR_ENTRA_CLIENT_ID" \
  --profile industrial-dev

aws secretsmanager put-secret-value \
  --secret-id industrial-dev/entra-client-secret \
  --secret-string "YOUR_ENTRA_CLIENT_SECRET" \
  --profile industrial-dev

aws secretsmanager put-secret-value \
  --secret-id industrial-dev/entra-tenant-id \
  --secret-string "YOUR_ENTRA_TENANT_ID" \
  --profile industrial-dev
```

### 10.5 Restart App Runner

After populating secrets, force App Runner to pick up the new values:
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:YOUR_DEV_ACCOUNT:service/industrial-dev-api/SERVICE_ID" \
  --profile industrial-dev
```

---

## 11. Run Database Migrations

Connect to the RDS instance through a bastion or VPN (it's in private subnets), then run:

```bash
export DATABASE_URL="postgresql://munitor:PASSWORD@RDS_ENDPOINT:5432/munitor"
alembic upgrade head
```

This creates all tables including the `entra_object_id` column on the `users` table (migration 004).

If you don't have direct access, you can run migrations from a Lambda or an EC2 instance in the same VPC.

---

## 12. Frontend Setup

### 12.1 Install Dependencies

```bash
cd web
npm install --legacy-peer-deps
```

This installs `next-auth` (which replaced `@clerk/nextjs`).

### 12.2 Set Environment Variables

For Amplify, the `NEXT_PUBLIC_API_URL` is set automatically by the CDK stack. For local development, create `web/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://api.industrial-dev.munitor.ai
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id
NEXTAUTH_SECRET=generate-a-random-32-char-string
NEXTAUTH_URL=http://localhost:3000
```

### 12.3 Verify Build

```bash
cd web
npm run build
```

---

## 13. Verify Dev Deployment

### 13.1 API Health Checks

```bash
curl https://api.industrial-dev.munitor.ai/health
curl https://api.industrial-dev.munitor.ai/api/v1/health/db
```

### 13.2 Test Document Upload

Upload a test PDF through the UI or API:
```bash
curl -X POST https://api.industrial-dev.munitor.ai/api/v1/documents/upload \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -F "file=@test-document.pdf"
```

### 13.3 Verify Ingestion Pipeline

1. Check the SQS queue for messages
2. Check CloudWatch logs for the ingestion Lambda
3. Verify chunks appear in the database

### 13.4 Test Authentication

1. Navigate to `https://app.industrial-dev.munitor.ai`
2. Click "Sign in" — should redirect to Microsoft login
3. After login, verify the user session is active

### 13.5 Check Observability

1. Open CloudWatch → Dashboards → `industrial-dev-api-dashboard`
2. Verify metrics are populating
3. Check that log groups exist: `/industrial-dev/app-runner/api` and `/industrial-dev/audit-logs`

---

## 14. Deploy Prod Environment

Once dev is validated, deploy prod using the same process:

```bash
cd infrastructure/cdk
cdk deploy --all --profile industrial-prod --require-approval never
```

Then populate prod secrets (same process as step 10, using `industrial-prod/` prefix and the prod profile).

Run migrations against the prod database.

---

## 15. DNS Validation

### 15.1 ACM Certificate Validation

After deploying the DNS stack, ACM certificates require DNS validation. CDK creates the validation records automatically if the hosted zone is accessible. If cross-account, you may need to manually create the CNAME validation records in the Shared Services Route53 hosted zone.

Check certificate status:
```bash
aws acm list-certificates --profile industrial-dev --region us-east-1
```

### 15.2 Verify DNS Resolution

```bash
dig api.industrial-dev.munitor.ai
dig app.industrial-dev.munitor.ai
dig api.industrial.munitor.ai
dig app.industrial.munitor.ai
```

---

## 16. CI/CD Pipeline Activation

### 16.1 GitHub Repository Settings

1. Go to Settings → Environments
2. Create `dev` environment (no protection rules)
3. Create `production` environment with required reviewers

### 16.2 Workflow Permissions

1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

### 16.3 Verify Pipelines

- Push a commit to `main` → `deploy-dev.yml` should trigger
- Create a PR → `pr-check.yml` should trigger
- Change files under `infrastructure/cdk/` → `cdk-deploy.yml` should trigger
- Create a release tag `v1.0.0` → `deploy-prod.yml` should trigger (with manual approval)

---

## 17. Post-Deployment Checklist

- [ ] SCP updated: `lambda:*` and `sqs:*` added to allowlist (blocker)
- [ ] GitHub OIDC provider exists in Shared Services (reused from Schools, not recreated)
- [ ] Audit log bucket policy updated in Log Archive account (blocker for audit forwarding)
- [ ] VPC CIDR allocations documented
- [ ] CDK bootstrapped in all three deployment accounts
- [ ] ECR repository has at least one image
- [ ] All dev stacks deployed successfully
- [ ] All six Secrets Manager secrets populated (dev)
- [ ] Database migrations applied (dev)
- [ ] API health checks passing (dev)
- [ ] Document upload and ingestion working (dev)
- [ ] Entra ID authentication working (dev)
- [ ] CloudWatch dashboard showing metrics (dev)
- [ ] Frontend accessible and functional (dev)
- [ ] All prod stacks deployed successfully
- [ ] All six Secrets Manager secrets populated (prod)
- [ ] Database migrations applied (prod)
- [ ] API health checks passing (prod)
- [ ] DNS resolving correctly for all four domains
- [ ] ACM certificates validated and active
- [ ] CI/CD pipelines tested and working
- [ ] SNS alarm topic has at least one subscriber (email/Slack)

---

## 18. Rollback Procedures

### App Runner
App Runner automatically rolls back if the health check fails after a deployment. To manually roll back, update the service to use a previous image tag.

### CDK Stacks
CloudFormation automatically rolls back failed stack updates. To force a rollback:
```bash
aws cloudformation cancel-update-stack --stack-name STACK_NAME --profile PROFILE
```

### Database Migrations
```bash
alembic downgrade -1
```

### Amplify
Amplify keeps build history. Roll back to a previous build from the Amplify console.

---

## 19. Cost Monitoring

Target budget: under $50/month for dev.

Key cost drivers:
- NAT Gateway: ~$32/month (single gateway, cost-optimized)
- RDS db.t4g.micro: ~$12/month (Multi-AZ doubles this)
- App Runner: ~$5/month at minimum (1 instance idle)
- S3, SQS, Lambda: negligible at low volume
- Secrets Manager: ~$2.40/month (6 secrets × $0.40)

Set up a billing alarm:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name industrial-dev-billing-50 \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions YOUR_SNS_TOPIC_ARN \
  --dimensions Name=Currency,Value=USD \
  --profile industrial-dev
```
