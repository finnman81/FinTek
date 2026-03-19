# Design Document: AWS CDK Deployment

## Overview

This design describes the AWS CDK infrastructure for deploying the Munitor AI industrial RAG knowledge base to AWS. The deployment follows the Schools CDK reference architecture patterns (naming conventions, reusable constructs, cross-account structure) with an `industrial-{env}` prefix, targeting both dev and prod environments in `us-east-1`.

The system deploys:
- FastAPI backend on App Runner (container-based, auto-scaling)
- Next.js frontend on Amplify Hosting (GitHub-connected)
- PostgreSQL 16 with pgvector on RDS in private subnets
- Event-driven ingestion via SQS + Lambda (S3 upload triggers)
- S3 for document storage with lifecycle policies
- Microsoft Entra ID authentication replacing Clerk
- Secrets Manager for all credentials
- CloudWatch observability with dashboards, alarms, and audit log forwarding
- GitHub Actions CI/CD with OIDC (no long-lived credentials)

Budget target: under $50/month. Region: `us-east-1`.

## Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Internet"
        User[User Browser]
        GitHub[GitHub Actions]
    end

    subgraph "Shared Services Account (555555555555)"
        ECR[ECR: industrial-api]
        R53[Route53: munitor.ai]
        OIDC[GitHub OIDC Provider]
        BuildRole[IAM: github-actions-industrial-build]
        DeployDevRole[IAM: github-actions-industrial-deploy-dev]
        DeployProdRole[IAM: github-actions-industrial-deploy-prod]
    end

    subgraph "Workload Account (Industrial-Dev/Prod)"
        subgraph "Public"
            Amplify[Amplify Hosting<br/>Next.js Frontend]
            AppRunner[App Runner<br/>FastAPI API]
        end

        subgraph "VPC 10.1.0.0/16"
            subgraph "Public Subnets"
                NAT[NAT Gateway]
                IGW[Internet Gateway]
                S3EP[S3 VPC Endpoint]
            end

            subgraph "Private Subnets"
                Lambda[Lambda<br/>Ingestion Worker]
                RDS[(RDS PostgreSQL 16<br/>pgvector)]
            end
        end

        S3[S3: Documents Bucket]
        SQS[SQS: Ingestion Queue]
        DLQ[SQS: Dead Letter Queue]
        Secrets[Secrets Manager]
        CW[CloudWatch<br/>Dashboards + Alarms]
        SNS[SNS: Alarm Notifications]
        AuditLambda[Lambda: Audit Log Forwarder]
    end

    subgraph "Log Archive Account (444444444444)"
        AuditS3[S3: munitor-audit-logs]
    end

    subgraph "Microsoft Entra ID"
        EntraID[Azure AD / OIDC]
    end

    User -->|HTTPS| Amplify
    User -->|HTTPS| AppRunner
    User -->|OIDC Login| EntraID
    Amplify -->|API calls| AppRunner
    AppRunner -->|VPC Connector| RDS
    AppRunner -->|Read/Write| S3
    AppRunner -->|Read| Secrets
    S3 -->|ObjectCreated event| SQS
    SQS -->|Trigger| Lambda
    Lambda -->|Parse/Chunk/Embed| RDS
    Lambda -->|Download doc| S3
    Lambda -->|OpenAI API| NAT
    DLQ -.->|Failed messages| SQS
    CW -->|Alarm| SNS
    AuditLambda -->|Forward logs| AuditS3
    GitHub -->|OIDC| OIDC
    GitHub -->|Push image| ECR
    GitHub -->|Deploy| AppRunner
    AppRunner -->|Pull image| ECR
    Lambda -->|Pull image| ECR
    EntraID -->|JWT validation| AppRunner
```

### CDK Stack Dependency Graph

```mermaid
graph TD
    Config[config.py<br/>EnvironmentConfig]

    VPC[VpcStack]
    S3Stack[S3Stack]
    ECRStack[EcrStack<br/>Shared Services]
    SecretsStack[SecretsStack]
    RDSStack[RdsStack]
    IngestionStack[IngestionStack]
    AppRunnerStack[AppRunnerStack]
    AmplifyStack[AmplifyStack]
    ObservabilityStack[ObservabilityStack]
    DNSStack[DnsStack]

    Config --> VPC
    Config --> S3Stack
    Config --> ECRStack
    Config --> SecretsStack

    VPC --> RDSStack
    SecretsStack --> RDSStack

    VPC --> IngestionStack
    S3Stack --> IngestionStack
    SecretsStack --> IngestionStack
    RDSStack --> IngestionStack
    ECRStack --> IngestionStack

    VPC --> AppRunnerStack
    SecretsStack --> AppRunnerStack
    RDSStack --> AppRunnerStack
    S3Stack --> AppRunnerStack
    ECRStack --> AppRunnerStack

    AppRunnerStack --> AmplifyStack
    AppRunnerStack --> DNSStack
    AmplifyStack --> DNSStack

    AppRunnerStack --> ObservabilityStack
    IngestionStack --> ObservabilityStack
```

### CDK Project Layout

```
infrastructure/cdk/
├── app.py                              # Entry point — instantiates all stacks
├── cdk.json                            # CDK config (app: python3 app.py)
├── requirements.txt                    # aws-cdk-lib, constructs, pytest, hypothesis
├── stacks/
│   ├── __init__.py
│   ├── config.py                       # EnvironmentConfig, account IDs, constants
│   ├── vpc_stack.py                    # VPC, subnets, NAT, S3 endpoint
│   ├── rds_stack.py                    # RDS PostgreSQL 16 + pgvector
│   ├── s3_stack.py                     # Document storage bucket
│   ├── ecr_stack.py                    # ECR repo + GitHub OIDC roles (Shared Services)
│   ├── app_runner_stack.py             # App Runner service + VPC connector
│   ├── ingestion_stack.py              # SQS + Lambda ingestion worker
│   ├── amplify_stack.py                # Amplify Hosting for Next.js
│   ├── secrets_stack.py                # Secrets Manager secrets + rotation
│   ├── observability_stack.py          # CloudWatch dashboards, alarms, audit forwarder
│   └── dns_stack.py                    # Route53 records + ACM certificates
├── constructs/
│   ├── __init__.py
│   └── tagging_aspect.py              # CDK Aspect for mandatory tags
└── tests/
    ├── __init__.py
    ├── test_vpc_stack.py
    ├── test_rds_stack.py
    ├── test_s3_stack.py
    ├── test_ecr_stack.py
    ├── test_app_runner_stack.py
    ├── test_ingestion_stack.py
    ├── test_amplify_stack.py
    ├── test_secrets_stack.py
    ├── test_observability_stack.py
    ├── test_dns_stack.py
    └── test_properties.py             # All property-based tests (hypothesis)
```

## Components and Interfaces

### 1. Config Module (`stacks/config.py`)

Defines the `EnvironmentConfig` dataclass and environment-specific configurations.

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class EnvironmentConfig:
    env_name: Literal['dev', 'prod']
    account_id: str
    region: str
    api_domain_prefix: str
    app_domain_prefix: str
    branch: str
    branch_previews_enabled: bool

INDUSTRIAL_DEV = EnvironmentConfig(
    env_name='dev',
    account_id='666666666666',
    region='us-east-1',
    api_domain_prefix='api.industrial-dev',
    app_domain_prefix='app.industrial-dev',
    branch='develop',
    branch_previews_enabled=True,
)

INDUSTRIAL_PROD = EnvironmentConfig(
    env_name='prod',
    account_id='777777777777',
    region='us-east-1',
    api_domain_prefix='api.industrial',
    app_domain_prefix='app.industrial',
    branch='main',
    branch_previews_enabled=False,
)

SHARED_SERVICES_ACCOUNT = '555555555555'
LOG_ARCHIVE_ACCOUNT = '444444444444'
HOSTED_ZONE_NAME = 'munitor.ai'
RESOURCE_PREFIX = 'industrial'
GITHUB_REPO = 'munitor-ai/industrial-kb'
```

### 2. VPC Stack

Creates a VPC with public/private subnets across 2 AZs, NAT gateway, and S3 VPC endpoint.

Inputs: `EnvironmentConfig`
Outputs: `vpc: ec2.Vpc`, `private_subnets`, `public_subnets`, `lambda_security_group`, `app_runner_security_group`

Key decisions:
- Single NAT gateway (cost optimization for <$50/month target)
- S3 gateway endpoint avoids NAT charges for S3 traffic
- CIDR `10.1.0.0/16` avoids collision with Schools VPC

### 3. RDS Stack

Provisions PostgreSQL 16 with pgvector in private subnets.

Inputs: `EnvironmentConfig`, `vpc`, `app_runner_security_group`, `lambda_security_group`
Outputs: `db_instance`, `db_security_group`, `database_url_secret`

Key decisions:
- `db.t4g.micro` for budget target; Multi-AZ for redundancy
- pgvector enabled via custom parameter group with `shared_preload_libraries = pg_stat_statements`
- The `pgvector` extension is created by Alembic migration (`CREATE EXTENSION IF NOT EXISTS vector`), not by CDK
- Security group allows port 5432 only from App Runner and Lambda security groups
- Connection URL stored in Secrets Manager as `industrial-{env}/database-url`
- Prod retains final snapshot on deletion; dev does not

### 4. S3 Stack

Creates the document storage bucket with versioning, encryption, and lifecycle rules.

Inputs: `EnvironmentConfig`
Outputs: `documents_bucket`, `bucket_name`

Key decisions:
- Bucket name: `industrial-{env}-documents-{accountId}` (globally unique)
- SSE-S3 encryption (no KMS key cost)
- Lifecycle: transition to IA after 90 days
- Event notification: `s3:ObjectCreated:*` → SQS ingestion queue

### 5. ECR Stack (Shared Services)

Creates the ECR repository and GitHub OIDC IAM roles.

Inputs: `SHARED_SERVICES_ACCOUNT`, `GITHUB_REPO`, dev/prod account IDs
Outputs: `ecr_repository`, `build_role_arn`, `deploy_dev_role_arn`, `deploy_prod_role_arn`

Key decisions:
- Separate repo `industrial-api` (not shared with Schools)
- Lifecycle: retain 20 tagged images, delete untagged after 7 days
- Cross-account pull for Industrial-Dev and Industrial-Prod
- Three IAM roles scoped to the industrial repo:
  - `github-actions-industrial-build`: ECR push, scoped to `ref:refs/heads/*`
  - `github-actions-industrial-deploy-dev`: App Runner update in dev, scoped to `ref:refs/heads/main`
  - `github-actions-industrial-deploy-prod`: App Runner update in prod, scoped to `ref:refs/tags/*`

### 6. App Runner Stack

Deploys the FastAPI backend on App Runner with VPC connectivity.

Inputs: `EnvironmentConfig`, `ecrRepository`, `vpc`, `secrets`, `s3_bucket`, `rds_security_group`
Outputs: `service_url`, `service_arn`

Key decisions:
- 1 vCPU, 2 GB memory per instance
- Auto-scaling: min 1, max 10, 100 max concurrency
- Health check: HTTP `/health`, 5s interval
- VPC connector for RDS access in private subnets
- Secrets injected as runtime env vars: `DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`
- `S3_BUCKET_NAME` set as plain environment variable
- Instance role grants S3 read/write and Secrets Manager read

### 7. Ingestion Stack (SQS + Lambda)

Event-driven document ingestion replacing the polling worker.

Inputs: `EnvironmentConfig`, `vpc`, `s3_bucket`, `secrets`, `ecr_repository`, `rds_security_group`
Outputs: `ingestion_queue`, `dlq`, `ingestion_function`

Key decisions:
- SQS queue with 900s visibility timeout (matches Lambda timeout)
- DLQ with maxReceiveCount=3
- Lambda uses container image from ECR (same image as App Runner, different entrypoint)
- Lambda timeout: 900s, memory: 1024 MB
- Batch size: 1 (one document per invocation)
- Lambda placed in VPC private subnets for RDS access
- Lambda security group allows outbound internet (NAT) for OpenAI API calls and port 5432 to RDS
- S3 `ObjectCreated` events → SQS → Lambda trigger

#### Lambda Handler Adaptation

The existing `src/workers/ingestion_worker.py` is a polling loop. For Lambda, a thin handler adapts the SQS event to call the existing `process_one_job` function:

```python
# infrastructure/cdk/lib/constructs/lambda-handler/ingestion_handler.py
import json
import os
from uuid import UUID, uuid4
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.parsers import parse_document
# ... (downloads from S3, runs pipeline, updates DB)
```

The handler:
1. Parses the SQS event body (S3 event notification)
2. Downloads the document from S3 to `/tmp`
3. Creates/updates a `documents` row and `ingestion_jobs` row in RDS
4. Calls `IngestionPipeline.ingest_file()` with the local path
5. Updates document status to `completed` or `failed`

### 8. Amplify Stack

Deploys the Next.js frontend on Amplify Hosting.

Inputs: `EnvironmentConfig`, `app_runner_service_url`
Outputs: `amplify_app`, `amplify_branch`

Key decisions:
- Build command: `npm ci --legacy-peer-deps && npm run build` in `web/`
- `NEXT_PUBLIC_API_URL` points to App Runner custom domain (HTTPS)
- Branch: `main` for prod, `develop` for dev
- Branch previews enabled for dev only
- SPA redirect rule: `/<*>` → `/index.html` (200 rewrite)
- Custom domain: `app.industrial.munitor.ai` (prod) / `app.industrial-dev.munitor.ai` (dev)

### 9. Secrets Stack

Manages all application secrets in Secrets Manager.

Inputs: `EnvironmentConfig`
Outputs: `secrets` (map of secret name → ISecret)

Secrets created per environment:
- `industrial-{env}/database-url` — 90-day rotation via Lambda
- `industrial-{env}/openai-api-key`
- `industrial-{env}/cors-origins`
- `industrial-{env}/entra-client-id`
- `industrial-{env}/entra-client-secret`
- `industrial-{env}/entra-tenant-id`

CloudWatch alarm on rotation failures → SNS topic.

### 10. Observability Stack

CloudWatch dashboards, alarms, log groups, and audit log forwarding.

Inputs: `EnvironmentConfig`, `app_runner_service_name`, `ingestion_function_name`
Outputs: `dashboard`, `alarm_topic`

Components:
- Dashboard: `industrial-{env}-api-dashboard` with request count, 5xx rate, p95 latency, CPU, memory, active instances
- Alarms: 5xx > 1%, p95 > 2s, instances ≥ 8, Lambda error rate > 5%
- SNS topic: `industrial-{env}-observability-alarms`
- Log groups: `/industrial-{env}/app-runner/api` (90-day), `/industrial-{env}/audit-logs` (7-year)
- Audit log forwarder Lambda: subscribes to audit log group, writes gzipped JSON to `munitor-audit-logs` bucket with prefix `industrial-{env}/`

### 11. DNS Stack

Route53 records and ACM certificates for custom domains.

Inputs: `EnvironmentConfig`, `app_runner_service_url`, `amplify_app_id`
Outputs: `api_certificate`, `app_certificate`

Key decisions:
- Records created in existing `munitor.ai` hosted zone (Shared Services account)
- ACM certificates in `us-east-1` with DNS validation
- Auto-renewal via DNS validation records

### 12. Auth Integration (Microsoft Entra ID)

Replaces Clerk with Microsoft Entra ID for authentication.

Backend changes:
- Replace `auth_clerk.py` with `auth_entra.py` that validates JWTs via OIDC discovery (`https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration`)
- Replace `clerk_user_id` column on `users` table with `entra_object_id`
- Extract `tenant_id` and role from JWT claims for multi-tenant isolation

Frontend changes:
- Replace `@clerk/nextjs` with `next-auth` using the Microsoft Azure AD provider
- Read Entra credentials from environment variables (injected from Secrets Manager)

### 13. Tagging Aspect

A CDK Aspect that applies mandatory tags to all resources:

```python
Tags.of(stack).add('workload', 'industrial')
Tags.of(stack).add('tenant', 'fin-tek')
Tags.of(stack).add('environment', config.env_name)
Tags.of(stack).add('managed-by', 'cdk')
```

### 14. CI/CD Pipelines (GitHub Actions)

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `pr-check.yml` | PR to main | Python tests, ruff lint, CDK synth |
| `deploy-dev.yml` | Push to main | Docker build → ECR push → App Runner update → smoke tests |
| `deploy-prod.yml` | Release tag `v*` | Manual approval → promote image to prod App Runner |
| `cdk-deploy.yml` | Push to main (infra/cdk changes) | CDK synth → deploy dev → manual approval → deploy prod |

All workflows use GitHub OIDC with `aws-actions/configure-aws-credentials@v4`.

## Data Models

### Existing Database Schema (unchanged by CDK)

The existing PostgreSQL schema managed by Alembic migrations remains the same. Key tables:

| Table | Purpose |
|-------|---------|
| `tenants` | Multi-tenant isolation (id, name, slug) |
| `users` | User accounts (id, tenant_id, email, role, `clerk_user_id` → `entra_object_id`) |
| `documents` | Document metadata (id, tenant_id, filename, s3_key, status, chunk_count) |
| `document_parents` | Parent chunks for section-level retrieval |
| `document_chunks` | Child chunks with pgvector embeddings (vector(1536)) |
| `ingestion_jobs` | Job queue for ingestion pipeline (status, error_message) |
| `usage_logs` | API usage tracking per tenant |
| `tenant_usage_limits` | Token usage caps |
| `response_ratings` | User feedback on chat responses |
| `embedding_versions` | Embedding model version tracking |

### Auth Migration: `clerk_user_id` → `entra_object_id`

A new Alembic migration renames the `clerk_user_id` column to `entra_object_id` on the `users` table and updates the unique index.

### CDK Configuration Data Model

```python
@dataclass(frozen=True)
class EnvironmentConfig:
    env_name: Literal['dev', 'prod']
    account_id: str
    region: str
    api_domain_prefix: str
    app_domain_prefix: str
    branch: str
    branch_previews_enabled: bool
```

### SQS Message Format (S3 Event → Ingestion Lambda)

The SQS message body contains the standard S3 event notification:

```json
{
  "Records": [{
    "s3": {
      "bucket": { "name": "industrial-dev-documents-666666666666" },
      "object": { "key": "tenants/{tenant_id}/uploads/{document_id}/{filename}" }
    }
  }]
}
```

The S3 key convention encodes `tenant_id` and `document_id` so the Lambda handler can extract them without a separate lookup.

### Secrets Manager Schema

| Secret Name | Value Format |
|-------------|-------------|
| `industrial-{env}/database-url` | `postgresql://user:pass@host:5432/munitor` |
| `industrial-{env}/openai-api-key` | `sk-...` |
| `industrial-{env}/cors-origins` | `https://app.industrial.munitor.ai,https://app.industrial-dev.munitor.ai` |
| `industrial-{env}/entra-client-id` | UUID string |
| `industrial-{env}/entra-client-secret` | Secret string |
| `industrial-{env}/entra-tenant-id` | UUID string |


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Mandatory tagging on all resources

*For any* resource in the synthesized CloudFormation template (for any environment), the resource should have the tags `workload=industrial`, `tenant=fin-tek`, `environment={env}`, and `managed-by=cdk`.

**Validates: Requirements 1.5**

### Property 2: Resource naming convention

*For any* resource in the synthesized CloudFormation template that has an explicitly set physical name (bucket name, queue name, function name, service name, secret name, log group name, dashboard name, alarm name), the name should match the pattern `industrial-{env}-*` or `industrial-{env}/*` (for Secrets Manager paths).

**Validates: Requirements 1.6**

### Property 3: RDS security group ingress restriction

*For any* inbound rule on the RDS database security group, the source should be either the App Runner security group or the Lambda ingestion worker security group, and the port should be 5432. No other ingress rules should exist.

**Validates: Requirements 3.6**

### Property 4: App Runner secrets injection completeness

*For any* secret in the required set {`DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`}, the App Runner service configuration should include that secret as a runtime environment variable sourced from Secrets Manager.

**Validates: Requirements 6.5**

### Property 5: Secrets Manager secret creation completeness

*For any* secret name in the required set {`database-url`, `openai-api-key`, `cors-origins`, `entra-client-id`, `entra-client-secret`, `entra-tenant-id`}, the synthesized template should contain a Secrets Manager secret with the name `industrial-{env}/{secret-name}`.

**Validates: Requirements 9.1**

### Property 6: Lambda ingestion handler processes S3 events

*For any* valid S3 `ObjectCreated` event containing a supported document type (PDF, DOCX, TXT, CSV, MD) at a well-formed S3 key (`tenants/{tenant_id}/uploads/{document_id}/{filename}`), the ingestion Lambda handler should download the document, run the ingestion pipeline, and produce at least one chunk stored in the database with the correct `document_id` and `tenant_id`.

**Validates: Requirements 7.9**

### Property 7: Observability alarm completeness

*For any* alarm in the required set {5xx error rate > 1%, p95 latency > 2s, App Runner instances ≥ 8, Lambda error rate > 5%}, the synthesized template should contain a CloudWatch alarm with the correct metric, threshold, and comparison operator, and the alarm should publish to the `industrial-{env}-observability-alarms` SNS topic.

**Validates: Requirements 11.2**

### Property 8: Entra ID JWT validation and claim extraction

*For any* valid JWT issued by Microsoft Entra ID (matching the configured tenant ID and client ID), the auth middleware should accept the token and correctly extract the `oid` (object ID), `tid` (tenant ID), and `roles` claims into the request context. *For any* invalid or expired JWT, the middleware should reject the request with a 401 status.

**Validates: Requirements 12.1, 12.5**

### Property 9: CI/CD workflows use OIDC authentication

*For any* GitHub Actions workflow file that authenticates with AWS, the workflow should use `aws-actions/configure-aws-credentials@v4` with `role-to-assume` (OIDC) and should not contain any hardcoded AWS access keys or secret keys.

**Validates: Requirements 14.5**

## Error Handling

### Infrastructure Provisioning Errors

| Error Scenario | Handling Strategy |
|---------------|-------------------|
| CDK synth fails (type errors, missing context) | CI pipeline fails fast; `pr-check.yml` runs `cdk synth` on every PR |
| CDK deploy fails (CloudFormation rollback) | Stack rolls back automatically; alarm via SNS; manual investigation |
| Cross-account access denied | Verify SCP allowlist includes required services; check IAM role trust policies |
| RDS creation fails (quota, AZ unavailable) | CloudFormation rollback; retry with different AZ or instance class |

### Runtime Errors

| Error Scenario | Handling Strategy |
|---------------|-------------------|
| Lambda ingestion timeout (>15 min) | Message returns to SQS queue; retried up to 3 times; then routed to DLQ |
| Lambda ingestion OOM | Increase memory allocation; monitor via CloudWatch Lambda metrics |
| S3 event delivery failure | SQS provides at-least-once delivery; DLQ captures persistent failures |
| RDS connection exhausted | App Runner and Lambda use connection pooling; CloudWatch alarm on connection count |
| OpenAI API rate limit / timeout | Lambda retries via SQS redelivery; exponential backoff in application code |
| Secrets Manager rotation failure | CloudWatch alarm fires → SNS notification; manual rotation as fallback |
| App Runner health check failure | App Runner automatically replaces unhealthy instances; 5xx alarm triggers |
| Entra ID OIDC discovery endpoint unavailable | Cache JWKS keys with TTL; return 503 if keys cannot be refreshed |
| Invalid JWT token | Return 401 with descriptive error; do not expose internal details |

### DLQ Processing

Messages in the `industrial-{env}-ingestion-dlq` require manual investigation:
1. CloudWatch alarm triggers when DLQ depth > 0
2. Operator inspects message body (S3 event) to identify the failed document
3. Fix the root cause (unsupported format, corrupt file, missing permissions)
4. Re-drive the message from DLQ back to the main queue, or re-upload the document

### Deployment Rollback

- App Runner: automatic rollback to previous image if health check fails
- Amplify: automatic rollback to previous build on build failure
- CDK stacks: CloudFormation automatic rollback on stack update failure
- Database migrations: Alembic `downgrade` for reversible schema changes

## Testing Strategy

### Unit Tests

Unit tests verify specific examples, edge cases, and error conditions. They complement property-based tests by covering concrete scenarios.

CDK infrastructure tests (pytest + `aws_cdk.assertions`):
- Snapshot tests for each stack to detect unintended changes
- Fine-grained assertion tests for critical resource configurations (RDS instance class, S3 encryption, Lambda timeout, security group rules)
- Environment-specific tests (dev vs prod: branch previews, snapshot retention)
- Cross-stack reference tests (VPC ID passed to RDS stack, secret ARNs passed to App Runner)

Application tests (pytest):
- Lambda handler: mock S3 download, mock DB session, verify pipeline is called with correct arguments
- Auth middleware: mock JWKS endpoint, test valid/invalid/expired tokens
- Alembic migration: verify `entra_object_id` column exists after migration

### Property-Based Tests

Property-based tests verify universal properties across many generated inputs. Each property test runs a minimum of 100 iterations.

CDK property tests use synthesized CloudFormation templates as the test subject. The test generates different environment configurations and verifies properties hold across all of them.

Application property tests use `hypothesis` (Python) for the ingestion handler and auth middleware.

Library: `hypothesis` for all property-based tests (both CDK and application).

Each property test must be tagged with a comment referencing the design property:
```
# Feature: aws-cdk-deployment, Property 1: Mandatory tagging on all resources
```

| Property | Test Approach | Library |
|----------|--------------|---------|
| Property 1: Mandatory tagging | Synthesize template for random env config, assert all resources have required tags | hypothesis |
| Property 2: Resource naming | Synthesize template, extract all physical names, assert pattern match | hypothesis |
| Property 3: RDS SG ingress | Synthesize template, extract all ingress rules on RDS SG, assert only allowed sources | hypothesis |
| Property 4: App Runner secrets | Generate random subsets of required secrets, verify all are present in App Runner config | hypothesis |
| Property 5: Secrets creation | Synthesize template, extract all secret names, assert required set is a subset | hypothesis |
| Property 6: Lambda handler E2E | Generate random S3 events with valid document keys, mock S3/DB, verify chunks produced | hypothesis |
| Property 7: Alarm completeness | Synthesize template, extract all alarms, assert required alarm set is covered | hypothesis |
| Property 8: JWT validation | Generate random valid/invalid JWTs, verify accept/reject and claim extraction | hypothesis |
| Property 9: OIDC in workflows | Parse all workflow YAML files, for each AWS auth step verify OIDC usage | hypothesis |

### Integration Tests

- Smoke tests in `deploy-dev.yml`: after deployment, hit `/health` and `/api/v1/health/db` endpoints
- End-to-end ingestion test: upload a small PDF to S3, wait for SQS/Lambda processing, verify chunks in RDS
- Auth flow test: obtain a test token from Entra ID, call `/api/v1/auth/me`, verify response

### Test Configuration

- CDK tests: `pytest` with `hypothesis`, run via `python -m pytest infrastructure/cdk/tests/ -v`
- Python tests: `pytest` with `hypothesis`, run via `python -m pytest tests/ -v`
- Minimum 100 iterations per property-based test
- CI gate: all tests must pass before merge (`pr-check.yml`)
