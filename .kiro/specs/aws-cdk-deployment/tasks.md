# Implementation Plan: AWS CDK Deployment

## Overview

Deploy the Munitor AI industrial RAG knowledge base to AWS using CDK (Python). The implementation follows the Schools CDK reference architecture with `industrial-{env}` naming, cross-account structure, and reusable constructs. Tasks are ordered by dependency: scaffolding → foundational stacks (VPC, Secrets, S3, ECR) → dependent stacks (RDS, Ingestion, App Runner) → frontend and wiring (Amplify, DNS, Observability) → application code changes (Auth, Lambda handler, S3 upload) → CI/CD pipelines.

## Tasks

- [x] 1. Scaffold CDK project and core configuration
  - [x] 1.1 Initialize CDK project under `infrastructure/cdk/`
    - Create `requirements.txt` with `aws-cdk-lib==2.206.0`, `constructs>=10.0.0`, `pytest`, `hypothesis` as dependencies
    - Create `cdk.json` with app entry point `python3 app.py` and CDK feature flags
    - Create `stacks/__init__.py` and `constructs/__init__.py` and `tests/__init__.py`
    - _Requirements: 1.1_

  - [x] 1.2 Create config module (`stacks/config.py`)
    - Define `EnvironmentConfig` dataclass with fields: `env_name`, `account_id`, `region`, `api_domain_prefix`, `app_domain_prefix`, `branch`, `branch_previews_enabled`
    - Define `INDUSTRIAL_DEV` config (account `666666666666`, region `us-east-1`, branch `develop`, previews enabled)
    - Define `INDUSTRIAL_PROD` config (account `777777777777`, region `us-east-1`, branch `main`, previews disabled)
    - Export constants: `SHARED_SERVICES_ACCOUNT`, `LOG_ARCHIVE_ACCOUNT`, `HOSTED_ZONE_NAME`, `RESOURCE_PREFIX`, `GITHUB_REPO`
    - _Requirements: 1.2, 1.3, 1.4_

  - [x] 1.3 Create tagging aspect (`constructs/tagging_aspect.py`)
    - Implement CDK Aspect that applies tags `workload=industrial`, `tenant=fin-tek`, `environment={env}`, `managed-by=cdk` to all resources
    - _Requirements: 1.5_

  - [x] 1.4 Create CDK app entry point (`app.py`)
    - Instantiate all stacks for dev and prod environments with correct account/region targeting
    - Apply tagging aspect to all stacks
    - Use `industrial-{env}-{resource}` naming convention for stack IDs
    - _Requirements: 1.5, 1.6_

  - [x] 1.5 Write property test for mandatory tagging (Property 1)
    - **Property 1: Mandatory tagging on all resources**
    - Synthesize template for dev and prod configs, assert all resources have required tags
    - Use `hypothesis` library
    - **Validates: Requirements 1.5**

  - [x] 1.6 Write property test for resource naming convention (Property 2)
    - **Property 2: Resource naming convention**
    - Synthesize template, extract all physical names, assert pattern `industrial-{env}-*` or `industrial-{env}/*`
    - Use `hypothesis` library
    - **Validates: Requirements 1.6**

- [x] 2. Implement VPC stack
  - [x] 2.1 Create VPC stack (`stacks/vpc_stack.py`)
    - Create VPC with CIDR `10.1.0.0/16`
    - Create 2 public subnets and 2 private subnets across `us-east-1a` and `us-east-1b`
    - Create internet gateway attached to VPC
    - Create single NAT gateway in one public subnet with private subnet routes
    - Create S3 gateway VPC endpoint
    - Create security groups for Lambda and App Runner (exported as stack outputs)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Write unit tests for VPC stack (`tests/test_vpc_stack.py`)
    - Assert VPC CIDR, subnet count, NAT gateway, S3 endpoint, security groups
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement Secrets stack
  - [x] 3.1 Create Secrets stack (`stacks/secrets_stack.py`)
    - Create 6 Secrets Manager secrets per environment: `database-url`, `openai-api-key`, `cors-origins`, `entra-client-id`, `entra-client-secret`, `entra-tenant-id`
    - Use naming pattern `industrial-{env}/{secret-name}`
    - Configure 90-day automatic rotation for `database-url` using a rotation Lambda
    - Create CloudWatch alarm for rotation failures publishing to SNS topic
    - Grant read access to App Runner instance role and Lambda execution role (via IAM policy outputs)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 3.2 Write property test for secrets creation completeness (Property 5)
    - **Property 5: Secrets Manager secret creation completeness**
    - Synthesize template, extract all secret names, assert required set is present
    - Use `hypothesis` library
    - **Validates: Requirements 9.1**

- [x] 4. Implement S3 stack
  - [x] 4.1 Create S3 stack (`stacks/s3_stack.py`)
    - Create bucket named `industrial-{env}-documents-{accountId}`
    - Enable versioning and SSE-S3 encryption
    - Block all public access
    - Create lifecycle rule transitioning to IA after 90 days
    - Configure `s3:ObjectCreated:*` event notification to SQS ingestion queue (queue ARN passed as prop or created later via `add_event_notification`)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 4.2 Write unit tests for S3 stack (`tests/test_s3_stack.py`)
    - Assert bucket name, versioning, encryption, public access block, lifecycle rule
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Implement ECR stack (Shared Services)
  - [x] 5.1 Create ECR stack (`stacks/ecr_stack.py`)
    - Create ECR repository `industrial-api` in Shared Services account (`555555555555`)
    - Configure lifecycle policy: retain 20 tagged images, delete untagged after 7 days
    - Grant cross-account pull access to Industrial-Dev (`666666666666`) and Industrial-Prod (`777777777777`)
    - Create IAM role `github-actions-industrial-build` trusting GitHub OIDC provider, allowing ECR push, scoped to `ref:refs/heads/*`
    - Create IAM role `github-actions-industrial-deploy-dev` allowing App Runner update in dev, scoped to `ref:refs/heads/main`
    - Create IAM role `github-actions-industrial-deploy-prod` allowing App Runner update in prod, scoped to `ref:refs/tags/*`
    - _Requirements: 5.1, 5.2, 5.3, 15.1, 15.2, 15.3_

  - [x] 5.2 Write unit tests for ECR stack (`tests/test_ecr_stack.py`)
    - Assert repository name, lifecycle policy, cross-account access, IAM role trust policies and scopes
    - _Requirements: 5.1, 5.2, 5.3, 15.1, 15.2, 15.3_

- [x] 6. Checkpoint - Ensure all foundational stack tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement RDS stack
  - [x] 7.1 Create RDS stack (`stacks/rds_stack.py`)
    - Create RDS PostgreSQL 16 instance with `db.t4g.micro`, database name `munitor`
    - Place in private subnets with DB subnet group spanning both AZs
    - Enable Multi-AZ
    - Allocate 20 GB storage with auto-scaling up to 100 GB
    - Enable storage encryption with default KMS key
    - Create security group allowing port 5432 only from App Runner and Lambda security groups
    - Set `publicly_accessible` to false
    - Create custom parameter group with `shared_preload_libraries = pg_stat_statements`
    - Retain final snapshot on deletion for prod; skip for dev
    - Store connection URL in Secrets Manager as `industrial-{env}/database-url`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

  - [x] 7.2 Write property test for RDS security group ingress (Property 3)
    - **Property 3: RDS security group ingress restriction**
    - Synthesize template, extract RDS SG ingress rules, assert only App Runner and Lambda SGs on port 5432
    - Use `hypothesis` library
    - **Validates: Requirements 3.6**

  - [x] 7.3 Write unit tests for RDS stack (`tests/test_rds_stack.py`)
    - Assert instance class, engine version, Multi-AZ, storage, encryption, parameter group, snapshot retention
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 3.8, 3.9_

- [x] 8. Implement Ingestion stack (SQS + Lambda)
  - [x] 8.1 Create Ingestion stack (`stacks/ingestion_stack.py`)
    - Create SQS queue `industrial-{env}-ingestion` with 900s visibility timeout
    - Create DLQ `industrial-{env}-ingestion-dlq` with maxReceiveCount=3
    - Create Lambda function `industrial-{env}-ingestion-worker` from ECR container image
    - Configure Lambda: 900s timeout, 1024 MB memory, batch size 1 from SQS
    - Set Lambda environment variables: `DATABASE_URL`, `OPENAI_API_KEY`, `S3_BUCKET_NAME`
    - Place Lambda in VPC private subnets with security group allowing outbound internet and port 5432 to RDS SG
    - Wire S3 `ObjectCreated` event notification → SQS queue
    - Create IAM execution role: S3 read/write, Secrets Manager read, SQS consume, VPC access
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.10_

  - [x] 8.2 Write unit tests for Ingestion stack (`tests/test_ingestion_stack.py`)
    - Assert queue names, visibility timeout, DLQ config, Lambda timeout/memory, SQS trigger, VPC placement
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.10_

- [x] 9. Implement App Runner stack
  - [x] 9.1 Create App Runner stack (`stacks/app_runner_stack.py`)
    - Create App Runner service `industrial-{env}-api` sourced from ECR `industrial-api`
    - Configure 1 vCPU, 2 GB memory
    - Configure auto-scaling: min 1, max 10, 100 max concurrency
    - Configure health check on `/health` with 5s interval
    - Inject secrets from Secrets Manager: `DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`
    - Set `S3_BUCKET_NAME` environment variable
    - Create IAM instance role with S3 read/write and Secrets Manager read
    - Configure VPC connector for RDS access in private subnets
    - Associate custom domain `api.industrial.munitor.ai` (prod) / `api.industrial-dev.munitor.ai` (dev)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [x] 9.2 Write property test for App Runner secrets injection (Property 4)
    - **Property 4: App Runner secrets injection completeness**
    - Synthesize template, verify all 6 required secrets are present in App Runner config
    - Use `hypothesis` library
    - **Validates: Requirements 6.5**

  - [x] 9.3 Write unit tests for App Runner stack (`tests/test_app_runner_stack.py`)
    - Assert service name, CPU/memory, auto-scaling config, health check, VPC connector, IAM role
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.7, 6.8_

- [x] 10. Checkpoint - Ensure all core infrastructure stack tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement Amplify stack
  - [x] 11.1 Create Amplify stack (`stacks/amplify_stack.py`)
    - Create Amplify app `industrial-{env}-frontend` connected to GitHub repository
    - Configure build: `npm ci --legacy-peer-deps && npm run build` in `web/` directory
    - Set `NEXT_PUBLIC_API_URL` to App Runner custom domain URL (HTTPS)
    - Configure `main` branch for prod, `develop` branch for dev
    - Enable branch preview deployments for dev only
    - Associate custom domain `app.industrial.munitor.ai` (prod) / `app.industrial-dev.munitor.ai` (dev)
    - Configure SPA redirect rule (`/<*>` → `/index.html`, 200 rewrite)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 11.2 Write unit tests for Amplify stack (`tests/test_amplify_stack.py`)
    - Assert app name, build command, env vars, branch config, preview settings, redirect rule
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 12. Implement DNS stack
  - [x] 12.1 Create DNS stack (`stacks/dns_stack.py`)
    - Create Route53 CNAME/ALIAS records in `munitor.ai` hosted zone for API and frontend domains (dev and prod)
    - Provision ACM certificates in `us-east-1` for API and frontend custom domains with DNS validation
    - Configure auto-renewal via DNS validation records
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 12.2 Write unit tests for DNS stack (`tests/test_dns_stack.py`)
    - Assert Route53 records, ACM certificates, DNS validation
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 13. Implement Observability stack
  - [x] 13.1 Create Observability stack (`stacks/observability_stack.py`)
    - Create CloudWatch dashboard `industrial-{env}-api-dashboard` with widgets: request count, 5xx error rate, p95 latency, CPU, memory, active instances
    - Create CloudWatch alarms: 5xx > 1%, p95 > 2s, instances ≥ 8, Lambda error rate > 5%
    - Create SNS topic `industrial-{env}-observability-alarms`
    - Create log groups: `/industrial-{env}/app-runner/api` (90-day retention), `/industrial-{env}/audit-logs` (7-year retention)
    - Deploy audit log forwarder Lambda subscribing to audit log group, writing gzipped JSON to `munitor-audit-logs` S3 bucket in Log Archive account with prefix `industrial-{env}/`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 13.2 Write property test for alarm completeness (Property 7)
    - **Property 7: Observability alarm completeness**
    - Synthesize template, extract all alarms, assert required alarm set is covered with correct metrics and thresholds
    - Use `hypothesis` library
    - **Validates: Requirements 11.2**

  - [x] 13.3 Write unit tests for Observability stack (`tests/test_observability_stack.py`)
    - Assert dashboard name, log group retention, SNS topic, audit forwarder Lambda
    - _Requirements: 11.1, 11.3, 11.4, 11.5_

- [x] 14. Checkpoint - Ensure all CDK stack tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement Lambda ingestion handler (application code)
  - [x] 15.1 Create Lambda ingestion handler (`src/lambda_handlers/ingestion_handler.py`)
    - Parse SQS event body containing S3 event notification
    - Extract `tenant_id`, `document_id`, and `filename` from S3 key (`tenants/{tenant_id}/uploads/{document_id}/{filename}`)
    - Download document from S3 to `/tmp`
    - Create/update `documents` and `ingestion_jobs` rows in RDS
    - Call `IngestionPipeline.ingest_file()` with the local path and document_id
    - Update document status to `completed` or `failed`
    - Handle errors gracefully (log, update status, let SQS retry)
    - _Requirements: 7.9_

  - [x] 15.2 Write property test for Lambda handler S3 event processing (Property 6)
    - **Property 6: Lambda ingestion handler processes S3 events**
    - Generate random valid S3 events with supported document types, mock S3/DB, verify chunks produced
    - Use `hypothesis` library
    - **Validates: Requirements 7.9**

  - [x] 15.3 Write unit tests for Lambda ingestion handler
    - Test with mock S3 download, mock DB session, verify pipeline called with correct arguments
    - Test error handling (missing key, unsupported format, DB failure)
    - _Requirements: 7.9_

- [x] 16. Implement S3 document upload integration (application code)
  - [x] 16.1 Update document upload route to use S3
    - Modify `src/api/routes/documents.py` upload endpoint to upload files to S3 bucket at key `tenants/{tenant_id}/uploads/{document_id}/{filename}` instead of local temp directory
    - Read `S3_BUCKET_NAME` from environment variable
    - Update document record `s3_key` to the actual S3 key
    - Remove local temp file storage logic
    - _Requirements: 6.6, 7.9_

  - [x] 16.2 Write unit tests for S3 upload integration
    - Mock boto3 S3 client, verify correct bucket/key, verify document record updated
    - _Requirements: 6.6_

- [x] 17. Implement Microsoft Entra ID authentication (application code)
  - [x] 17.1 Create Entra ID auth middleware (`src/api/auth_entra.py`)
    - Validate JWT tokens via OIDC discovery (`https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration`)
    - Cache JWKS keys with TTL
    - Extract `oid` (object ID), `tid` (tenant ID), and `roles` claims into request context
    - Return 401 for invalid/expired tokens
    - Read Entra credentials from environment variables: `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`
    - _Requirements: 12.1, 12.4, 12.5_

  - [x] 17.2 Create Alembic migration for `clerk_user_id` → `entra_object_id`
    - Rename `clerk_user_id` column to `entra_object_id` on `users` table
    - Update unique index
    - Update `User` model in `src/db/models.py`
    - _Requirements: 12.2_

  - [x] 17.3 Update frontend auth to use next-auth with Azure AD provider
    - Replace `@clerk/nextjs` with `next-auth` in `web/package.json`
    - Configure Microsoft Azure AD provider in next-auth
    - Update auth-related components and middleware
    - _Requirements: 12.3_

  - [x] 17.4 Write property test for Entra ID JWT validation (Property 8)
    - **Property 8: Entra ID JWT validation and claim extraction**
    - Generate random valid/invalid JWTs, verify accept/reject and claim extraction
    - Use `hypothesis` library
    - **Validates: Requirements 12.1, 12.5**

  - [x] 17.5 Write unit tests for Entra ID auth middleware
    - Mock JWKS endpoint, test valid/invalid/expired tokens, verify claim extraction
    - _Requirements: 12.1, 12.5_

- [x] 18. Checkpoint - Ensure all application code tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Implement CI/CD pipelines
  - [x] 19.1 Create PR check workflow (`.github/workflows/pr-check.yml`)
    - Trigger on pull requests
    - Run Python tests, ruff lint, CDK synth validation
    - Use GitHub OIDC with `aws-actions/configure-aws-credentials@v4`
    - _Requirements: 14.1, 14.5_

  - [x] 19.2 Create dev deployment workflow (`.github/workflows/deploy-dev.yml`)
    - Trigger on push to `main`
    - Build Docker image, push to ECR, update App Runner service in Industrial-Dev
    - Run smoke tests against dev API endpoint (`/health`, `/api/v1/health/db`)
    - Use OIDC with `github-actions-industrial-build` and `github-actions-industrial-deploy-dev` roles
    - _Requirements: 14.2, 14.5_

  - [x] 19.3 Create prod deployment workflow (`.github/workflows/deploy-prod.yml`)
    - Trigger on release tags matching `v*`
    - Require manual approval before promoting image to Industrial-Prod App Runner
    - Use OIDC with `github-actions-industrial-deploy-prod` role
    - _Requirements: 14.3, 14.5_

  - [x] 19.4 Create CDK deployment workflow (`.github/workflows/cdk-deploy.yml`)
    - Trigger on push to `main` when files under `infrastructure/cdk/` change
    - Run CDK synth, deploy dev stacks, require manual approval, deploy prod stacks
    - Use OIDC authentication
    - _Requirements: 14.4, 14.5_

  - [x] 19.5 Write property test for OIDC in CI/CD workflows (Property 9)
    - **Property 9: CI/CD workflows use OIDC authentication**
    - Parse all workflow YAML files, for each AWS auth step verify OIDC usage and no hardcoded credentials
    - Use `hypothesis` library
    - **Validates: Requirements 14.5**

- [x] 20. Update SCP for Industrial workload
  - [x] 20.1 Document SCP changes required
    - Create a reference file documenting the services to add to `WorkloadServiceRestriction` allowlist: `lambda:*`, `sqs:*`, `states:*`, `events:*`
    - Note: actual SCP update is in the shared `infra/` repo's `scp-stack.ts`, not in this CDK project
    - _Requirements: 13.1, 13.2_

- [x] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- CDK stacks use Python; application code uses Python
- All CDK tests use pytest with hypothesis, run via `python -m pytest infrastructure/cdk/tests/ -v`
- The Lambda ingestion handler and S3 upload integration are application code changes that can be developed in parallel with CDK stacks
- Auth migration (Entra ID) can also be developed in parallel with infrastructure
