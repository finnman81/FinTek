# Fin-Tek Architecture — Munitor AI Industrial Knowledge Base

## Overview

Munitor AI is an industrial RAG (Retrieval-Augmented Generation) knowledge base built for Fin-Tek, a service company supporting industrial equipment (Teledyne 465 series analyzers and related instruments). The system allows field technicians and support staff to upload equipment manuals, schematics, and service documents, then ask natural-language questions and receive accurate, source-cited answers.

The application is deployed to AWS using CDK (Python) across a multi-account structure following the Schools CDK reference architecture patterns. All resources use the `industrial-{env}` naming convention.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                      │
│                                                                         │
│   Users ──── HTTPS ────► app.industrial.munitor.ai (Amplify)           │
│                          app.industrial-dev.munitor.ai                  │
│                                                                         │
│   Users ──── HTTPS ────► api.industrial.munitor.ai (App Runner)        │
│                          api.industrial-dev.munitor.ai                  │
│                                                                         │
│   GitHub Actions ─── OIDC ───► Shared Services IAM Roles               │
└─────────────────────────────────────────────────────────────────────────┘
```

## AWS Account Structure

The deployment spans four AWS accounts organized under AWS Organizations:

| Account | Role | Key Resources |
|---------|------|---------------|
| Shared Services | Central services | ECR repository, Route53 hosted zone, GitHub OIDC provider, CI/CD IAM roles |
| Industrial-Dev | Development | Full stack: VPC, RDS, App Runner, Lambda, S3, Amplify, CloudWatch |
| Industrial-Prod | Production | Identical stack set to dev with stricter retention policies |
| Log Archive | Compliance | Audit log S3 bucket with 7-year retention |

## CDK Stack Inventory

Each environment (dev/prod) deploys 9 stacks plus 1 shared ECR stack:

| Stack | Stack ID Pattern | Purpose |
|-------|-----------------|---------|
| VPC | `industrial-{env}-vpc` | Networking foundation |
| Secrets | `industrial-{env}-secrets` | Secrets Manager secrets |
| S3 | `industrial-{env}-s3` | Document storage bucket |
| ECR | `industrial-ecr` | Container image repository (shared) |
| RDS | `industrial-{env}-rds` | PostgreSQL 16 with pgvector |
| Ingestion | `industrial-{env}-ingestion` | SQS queue + Lambda worker |
| App Runner | `industrial-{env}-app-runner` | FastAPI backend service |
| Amplify | `industrial-{env}-amplify` | Next.js frontend hosting |
| DNS | `industrial-{env}-dns` | Route53 records + ACM certificates |
| Observability | `industrial-{env}-observability` | Dashboard, alarms, log groups, audit forwarder |

### Stack Dependency Graph

```
Config (EnvironmentConfig)
  │
  ├── VpcStack (no deps)
  ├── S3Stack (no deps)
  ├── EcrStack (Shared Services, no deps)
  ├── SecretsStack (no deps)
  │
  ├── RdsStack ← VPC, Secrets
  │
  ├── IngestionStack ← VPC, S3, Secrets, RDS, ECR
  │
  ├── AppRunnerStack ← VPC, Secrets, RDS, S3, ECR
  │
  ├── AmplifyStack ← AppRunner
  │
  ├── DnsStack ← AppRunner, Amplify
  │
  └── ObservabilityStack ← AppRunner, Ingestion
```

## Component Details

### Networking (VPC Stack)

- VPC CIDR: `10.1.0.0/16`
- 2 public subnets + 2 private subnets across `us-east-1a` and `us-east-1b`
- Single NAT gateway (cost optimization for <$50/month target)
- S3 gateway VPC endpoint (avoids NAT charges for S3 traffic)
- Two security groups:
  - `industrial-{env}-lambda-sg`: All outbound (for OpenAI API via NAT)
  - `industrial-{env}-app-runner-sg`: All outbound (for VPC connector)

### Database (RDS Stack)

- PostgreSQL 16 with pgvector extension support
- Instance: `db.t4g.micro` (Graviton, burstable)
- Database name: `munitor`
- Multi-AZ enabled for redundancy
- 20 GB allocated storage, auto-scaling to 100 GB
- Storage encryption with default AWS KMS key
- Private subnets only, not publicly accessible
- Custom parameter group: `shared_preload_libraries = pg_stat_statements`
- Security group: port 5432 open only to App Runner SG and Lambda SG
- Prod: retains final snapshot on deletion
- Dev: skips final snapshot

### Database Schema

| Table | Purpose |
|-------|---------|
| `tenants` | Multi-tenant isolation (id, name, slug) |
| `users` | User accounts (id, tenant_id, email, role, `entra_object_id`) |
| `documents` | Document metadata (id, tenant_id, filename, s3_key, status, chunk_count) |
| `document_parents` | Parent chunks for section-level retrieval |
| `document_chunks` | Child chunks with pgvector embeddings (vector(1536)) |
| `ingestion_jobs` | Job tracking for ingestion pipeline |
| `usage_logs` | API usage tracking per tenant |
| `tenant_usage_limits` | Token usage caps |
| `response_ratings` | User feedback on chat responses (1-5 stars) |
| `embedding_versions` | Embedding model version tracking |

Migrations managed by Alembic (4 versions: initial schema, response ratings, hybrid retrieval, Entra auth).

### Document Storage (S3 Stack)

- Bucket: `industrial-{env}-documents-{accountId}`
- Versioning enabled
- SSE-S3 encryption (AES-256)
- All public access blocked
- Lifecycle: transition to Infrequent Access after 90 days
- Event notification: `s3:ObjectCreated:*` → SQS ingestion queue

S3 key convention for uploads:
```
tenants/{tenant_id}/uploads/{document_id}/{filename}
```

### Container Registry (ECR Stack — Shared Services)

- Repository: `industrial-api`
- Lifecycle: retain 20 tagged images, delete untagged after 7 days
- Cross-account pull access for dev and prod accounts
- Three GitHub OIDC IAM roles:
  - `github-actions-industrial-build`: ECR push (scoped to `refs/heads/*`)
  - `github-actions-industrial-deploy-dev`: App Runner update in dev (scoped to `refs/heads/main`)
  - `github-actions-industrial-deploy-prod`: App Runner update in prod (scoped to `refs/tags/*`)

### API Backend (App Runner Stack)

- Service: `industrial-{env}-api`
- Source: ECR `industrial-api:latest`
- Runtime: FastAPI on Uvicorn, port 8000
- Instance: 1 vCPU, 2 GB memory
- Auto-scaling: min 1, max 10 instances, 100 max concurrency per instance
- Health check: HTTP `/health`, 5-second interval
- VPC connector: routes traffic through private subnets for RDS access
- Custom domain: `api.industrial.munitor.ai` (prod) / `api.industrial-dev.munitor.ai` (dev)

Secrets injected as runtime environment variables from Secrets Manager:
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — OpenAI API key for embeddings
- `CORS_ORIGINS` — Allowed CORS origins
- `ENTRA_CLIENT_ID` — Microsoft Entra ID client ID
- `ENTRA_CLIENT_SECRET` — Microsoft Entra ID client secret
- `ENTRA_TENANT_ID` — Microsoft Entra ID tenant ID

Plain environment variable:
- `S3_BUCKET_NAME` — Document storage bucket name

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/api/v1/health/db` | GET | Database connectivity check |
| `/api/v1/chat` | POST | RAG chat query (streaming supported) |
| `/api/v1/documents` | GET | List documents for tenant |
| `/api/v1/documents/upload` | POST | Upload document to S3 |
| `/api/v1/documents/{id}/status` | GET | Ingestion job status |
| `/api/v1/documents/{id}` | DELETE | Delete document and chunks |
| `/api/v1/admin/analytics` | GET | Usage stats and analytics |
| `/api/v1/feedback/rate` | POST | Submit response rating |

### Document Ingestion Pipeline (Ingestion Stack)

The ingestion pipeline is event-driven and serverless:

```
S3 Upload → S3 ObjectCreated Event → SQS Queue → Lambda Worker → RDS (pgvector)
```

Components:
- SQS queue: `industrial-{env}-ingestion` (900s visibility timeout)
- Dead-letter queue: `industrial-{env}-ingestion-dlq` (max 3 retries)
- Lambda: `industrial-{env}-ingestion-worker` (container image from ECR)
  - Timeout: 900 seconds (15 minutes)
  - Memory: 1024 MB
  - Batch size: 1 (one document per invocation)
  - VPC: private subnets (for RDS access + NAT for OpenAI API)

Lambda handler flow:
1. Parse SQS event body (S3 event notification)
2. Extract `tenant_id`, `document_id`, `filename` from S3 key
3. Download document from S3 to `/tmp`
4. Create/update `documents` and `ingestion_jobs` rows
5. Run `IngestionPipeline.ingest_file()` (parse → chunk → embed → store)
6. Update status to `completed` or `failed`
7. On failure after 3 retries, message goes to DLQ

Supported document types: PDF, DOCX, TXT, CSV, MD (determined by `PARSER_REGISTRY` in `src/ingestion/parsers.py`).

### Frontend (Amplify Stack)

- App: `industrial-{env}-frontend`
- Framework: Next.js 14
- Source: GitHub repository, auto-deploy on push
- Build: `npm ci --legacy-peer-deps && npm run build` in `web/` directory
- Branch: `main` for prod, `develop` for dev
- Branch previews: enabled for dev only
- Custom domain: `app.industrial.munitor.ai` (prod) / `app.industrial-dev.munitor.ai` (dev)
- SPA redirect: `/<*>` → `/index.html` (200 rewrite)

Frontend pages:
- Chat (`/`) — conversational RAG interface with session management
- Upload (`/upload`) — document upload with status tracking
- Admin (`/admin`) — usage analytics, document management, knowledge gap analysis

### Authentication

Authentication uses Microsoft Entra ID (Azure AD) via OIDC:

Backend (`src/api/auth_entra.py`):
- Validates JWT tokens via OIDC discovery endpoint
- Caches JWKS keys with 5-minute TTL (thread-safe)
- Extracts `oid` (object ID), `tid` (tenant ID), and `roles` claims
- Returns 401 for invalid, expired, or wrong-audience tokens
- Handles key rotation by force-refreshing JWKS when kid is not found

Frontend (`web/src/lib/auth.ts`):
- Uses `next-auth` with Azure AD provider
- `SessionProvider` wraps the app for client-side session access
- Middleware protects `/upload` and `/admin` routes
- Sign-in/sign-out buttons in the NavBar

Database mapping: `users.entra_object_id` column (migrated from `clerk_user_id` via Alembic migration 004).

### Secrets Management (Secrets Stack)

Six secrets per environment with naming pattern `industrial-{env}/{secret-name}`:

| Secret | Purpose |
|--------|---------|
| `database-url` | PostgreSQL connection string (90-day auto-rotation) |
| `openai-api-key` | OpenAI API key for embeddings |
| `cors-origins` | Allowed CORS origins |
| `entra-client-id` | Microsoft Entra ID client ID |
| `entra-client-secret` | Microsoft Entra ID client secret |
| `entra-tenant-id` | Microsoft Entra ID tenant ID |

Rotation:
- `database-url` has 90-day automatic rotation via a rotation Lambda
- CloudWatch alarm on rotation failures → SNS topic `industrial-{env}-secret-rotation-alarms`

### DNS and TLS (DNS Stack)

- Route53 CNAME records in the `munitor.ai` hosted zone (Shared Services account)
- ACM certificates with DNS validation for API and frontend domains
- Auto-renewal via DNS validation records
- Four domains total:
  - `api.industrial-dev.munitor.ai` → App Runner (dev)
  - `app.industrial-dev.munitor.ai` → Amplify (dev)
  - `api.industrial.munitor.ai` → App Runner (prod)
  - `app.industrial.munitor.ai` → Amplify (prod)

### Observability (Observability Stack)

CloudWatch Dashboard (`industrial-{env}-api-dashboard`):
- Request count
- 5xx error rate
- p95 latency
- CPU utilization
- Memory utilization
- Active App Runner instances

CloudWatch Alarms (all publish to SNS topic `industrial-{env}-observability-alarms`):

| Alarm | Metric | Threshold | Comparison |
|-------|--------|-----------|------------|
| 5xx error rate | `AWS/AppRunner` `5xxStatusResponses` | 1 | Greater than |
| p95 latency | `AWS/AppRunner` `RequestLatency` | 2000ms | Greater than |
| Active instances | `AWS/AppRunner` `ActiveInstances` | 8 | Greater than or equal |
| Lambda error rate | `AWS/Lambda` `Errors` | 5 | Greater than |

Log Groups:
- `/industrial-{env}/app-runner/api` — 90-day retention
- `/industrial-{env}/audit-logs` — 7-year retention (compliance)

Audit Log Forwarder:
- Lambda function `industrial-{env}-audit-log-forwarder`
- Subscribes to the audit log group
- Writes gzipped JSON to `munitor-audit-logs` S3 bucket in Log Archive account
- Key prefix: `industrial-{env}/`

## CI/CD Pipelines

Four GitHub Actions workflows, all using OIDC authentication (no long-lived credentials):

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `pr-check.yml` | Pull request to `main` | Ruff lint → pytest → CDK synth |
| `deploy-dev.yml` | Push to `main` | Docker build → ECR push → App Runner update → smoke tests |
| `deploy-prod.yml` | Release tag `v*` | Manual approval → promote image to prod App Runner |
| `cdk-deploy.yml` | Push to `main` (infra/cdk changes) | CDK synth → deploy dev → manual approval → deploy prod |

### Deployment Flow

```
Developer pushes to main
  │
  ├── deploy-dev.yml triggers
  │   ├── Build Docker image (SHA tag)
  │   ├── Push to ECR (build role)
  │   ├── Update App Runner in dev (deploy-dev role)
  │   └── Smoke tests: /health + /api/v1/health/db
  │
  └── cdk-deploy.yml triggers (if infra/cdk changed)
      ├── CDK synth
      ├── Deploy dev stacks
      ├── Manual approval gate
      └── Deploy prod stacks

Developer creates release tag v1.x.x
  │
  └── deploy-prod.yml triggers
      ├── Manual approval (production environment)
      └── Promote image to prod App Runner (deploy-prod role)
```

## Tagging Strategy

All resources are tagged via a CDK Aspect (`TaggingAspect`):

| Tag | Value |
|-----|-------|
| `workload` | `industrial` |
| `tenant` | `fin-tek` |
| `environment` | `dev` or `prod` |
| `managed-by` | `cdk` |

## Security Architecture

### Network Isolation
- RDS in private subnets, not publicly accessible
- Security group restricts port 5432 to App Runner and Lambda SGs only
- Lambda in private subnets with NAT for outbound internet (OpenAI API)
- S3 gateway endpoint avoids NAT for S3 traffic

### Authentication and Authorization
- Microsoft Entra ID (Azure AD) OIDC for user authentication
- JWT validation with JWKS key caching and rotation handling
- Multi-tenant isolation via `tenant_id` on all data tables
- Role-based access from JWT `roles` claim

### Secrets Management
- All credentials in Secrets Manager (never hardcoded)
- 90-day automatic rotation for database credentials
- Rotation failure alarms via CloudWatch + SNS

### CI/CD Security
- GitHub OIDC — no long-lived AWS credentials
- IAM roles scoped to specific repositories and branches
- Build role: ECR push only
- Deploy roles: App Runner update only, scoped to specific services

### Data Protection
- S3: SSE-S3 encryption, versioning, all public access blocked
- RDS: storage encryption with AWS KMS
- Secrets Manager: encrypted at rest
- TLS everywhere (HTTPS via ACM certificates)

### Compliance
- Audit logs with 7-year retention
- Audit log forwarder ships to isolated Log Archive account
- SCP restricts workload accounts to approved services only

## Cost Estimate (Dev Environment)

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| NAT Gateway | ~$32 |
| RDS db.t4g.micro (Multi-AZ) | ~$24 |
| App Runner (1 idle instance) | ~$5 |
| Secrets Manager (6 secrets) | ~$2.40 |
| S3 (low volume) | <$1 |
| SQS + Lambda (low volume) | <$1 |
| CloudWatch (dashboard + alarms) | ~$3 |
| Route53 (hosted zone + queries) | ~$1 |
| Amplify Hosting | ~$0 (free tier) |
| **Total** | **~$69/month** |

Note: Multi-AZ RDS doubles the instance cost. For a strict <$50/month target, consider disabling Multi-AZ in dev.

## Project Structure

```
├── infrastructure/
│   ├── cdk/
│   │   ├── app.py                    # CDK entry point
│   │   ├── cdk.json                  # CDK configuration
│   │   ├── requirements.txt          # CDK dependencies
│   │   ├── stacks/
│   │   │   ├── config.py             # Environment configs and constants
│   │   │   ├── vpc_stack.py
│   │   │   ├── rds_stack.py
│   │   │   ├── s3_stack.py
│   │   │   ├── ecr_stack.py
│   │   │   ├── secrets_stack.py
│   │   │   ├── ingestion_stack.py
│   │   │   ├── app_runner_stack.py
│   │   │   ├── amplify_stack.py
│   │   │   ├── dns_stack.py
│   │   │   └── observability_stack.py
│   │   ├── constructs/
│   │   │   └── tagging_aspect.py     # Mandatory tagging CDK Aspect
│   │   └── tests/                    # 145 CDK tests (unit + property-based)
│   └── docker/
│       └── Dockerfile                # FastAPI container image
├── src/
│   ├── api/                          # FastAPI routes, middleware, auth
│   │   ├── auth_entra.py             # Entra ID JWT validation
│   │   ├── routes/documents.py       # S3 upload integration
│   │   └── ...
│   ├── ingestion/                    # Parse, chunk, embed pipeline
│   ├── lambda_handlers/
│   │   └── ingestion_handler.py      # Lambda entry point for SQS events
│   ├── db/models.py                  # SQLAlchemy models
│   └── ...
├── web/                              # Next.js 14 frontend
│   ├── src/
│   │   ├── app/api/auth/[...nextauth]/route.ts  # next-auth API route
│   │   ├── lib/auth.ts               # Azure AD provider config
│   │   └── ...
│   └── package.json
├── alembic/                          # Database migrations
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_response_ratings.py
│       ├── 003_hybrid_manual_retrieval.py
│       └── 004_entra_auth_migration.py
├── .github/workflows/                # CI/CD pipelines
│   ├── pr-check.yml
│   ├── deploy-dev.yml
│   ├── deploy-prod.yml
│   └── cdk-deploy.yml
└── tests/                            # Application tests
    ├── test_lambda_handler.py
    ├── test_lambda_handler_properties.py
    ├── test_s3_upload.py
    ├── test_auth_entra.py
    ├── test_auth_entra_properties.py
    └── ...
```

## Cross-Project Parity with Schools CDK

The Industrial (Fin-Tek) and Schools workloads share the same AWS Organizations structure, Shared Services account, and Log Archive account. This section documents the resource boundaries and deployment blockers identified during cross-project review.

### Shared Resources (No Conflicts)

| Resource | Schools | Industrial | Conflict? |
|----------|---------|------------|-----------|
| ECR repository | `school-assessment-api` | `industrial-api` | No |
| IAM roles | `github-actions-build` | `github-actions-industrial-build` | No |
| Secrets | `schools-{env}/...` | `industrial-{env}/...` | No |
| Log groups | `/schools-{env}/...` | `/industrial-{env}/...` | No |
| App Runner | `schools-{env}-api` | `industrial-{env}-api` | No |
| SNS topics | `schools-{env}-observability-alarms` | `industrial-{env}-observability-alarms` | No |
| Route53 domains | `api.schools.munitor.ai` | `api.industrial.munitor.ai` | No |
| Audit log prefix | `schools-{env}/` | `industrial-{env}/` | No |
| CDK language | TypeScript | Python | No (separate templates) |

### Deployment Blockers

1. **SCP: Lambda and SQS missing from allowlist** — The `WorkloadServiceRestriction` SCP must be updated in `scp-stack.ts` to add `lambda:*` and `sqs:*`. Without this, the ingestion pipeline cannot deploy. See `infrastructure/cdk/docs/scp-changes.md`.

2. **Audit log bucket policy** — The `munitor-audit-logs` bucket in Log Archive needs a policy statement allowing the Industrial forwarder Lambda roles (`industrial-dev-audit-log-forwarder-role`, `industrial-prod-audit-log-forwarder-role`) to `s3:PutObject` on `munitor-audit-logs/industrial-*`. Update `log-archive-stack.ts` in the shared infra repo.

3. **GitHub OIDC provider** — Only one provider per URL per account. The provider already exists from the Schools deployment. The Industrial ECR stack correctly imports it via `from_open_id_connect_provider_arn` rather than creating a new one. No action needed.

### VPC CIDR Allocation

| CIDR | Workload | Status |
|------|----------|--------|
| `10.1.0.0/16` | Industrial (Fin-Tek) | Active |
| `10.2.0.0/16` | Schools | Reserved (future) |
| `10.3.0.0/16` | Available | — |

Schools doesn't currently deploy a VPC. If one is added later, use a non-overlapping CIDR.

### NAT Gateway Cost Note

Industrial's VPC includes a NAT gateway (~$32/month). If Schools later adds a VPC, consider sharing a Transit Gateway or VPC peering to avoid paying for two NAT gateways.
