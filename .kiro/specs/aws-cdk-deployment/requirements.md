# Requirements Document

## Introduction

This document defines the requirements for deploying the Munitor AI industrial RAG knowledge base application to AWS using CDK. The deployment covers the full stack: FastAPI API on App Runner, Next.js frontend on Amplify Hosting, PostgreSQL with pgvector on RDS, SQS-triggered Lambda for document ingestion, S3 for document storage, Microsoft Entra ID authentication, secrets management, observability, CI/CD pipelines, and custom domain routing. The CDK project follows the Schools CDK reference architecture patterns (naming conventions, reusable constructs, cross-account structure) with an `industrial-{env}` prefix. Both dev and prod environments are provisioned from the start, targeting under $50/month initially.

## Glossary

- **CDK_App**: The AWS CDK application entry point located at `infrastructure/cdk/`, responsible for instantiating all Industrial stacks
- **Industrial_Config**: The environment configuration module that defines account IDs, region, domain prefixes, and branch mappings for dev and prod environments
- **VPC_Stack**: The CDK stack that provisions the Virtual Private Cloud with public and private subnets across two availability zones, internet gateway, and NAT gateway
- **RDS_Stack**: The CDK stack that provisions the PostgreSQL RDS instance with pgvector extension support, placed in private subnets with Multi-AZ redundancy
- **S3_Stack**: The CDK stack that provisions the S3 bucket for document storage with versioning, encryption, and lifecycle policies
- **ECR_Stack**: The CDK stack that provisions the Elastic Container Registry repository for the FastAPI Docker image in the Shared Services account
- **App_Runner_Stack**: The CDK stack that provisions the App Runner service for the FastAPI backend, pulling images from ECR with auto-scaling
- **Ingestion_Stack**: The CDK stack that provisions the SQS queue and Lambda function for event-driven document ingestion (parse, chunk, embed, store)
- **Amplify_Stack**: The CDK stack that provisions Amplify Hosting for the Next.js frontend with GitHub source integration
- **Secrets_Stack**: The CDK stack that provisions Secrets Manager secrets for database URL, OpenAI API key, CORS origins, and Microsoft Entra ID credentials
- **Observability_Stack**: The CDK stack that provisions CloudWatch dashboards, alarms, SNS notifications, log groups, and audit log forwarding
- **DNS_Stack**: The CDK stack that provisions Route53 records and ACM certificates for custom domains on `munitor.ai`
- **CICD_Pipeline**: The GitHub Actions workflows for PR checks, dev deployment, prod deployment, and CDK infrastructure changes
- **Auth_Integration**: The Microsoft Entra ID (Azure AD) authentication integration replacing Clerk, using OIDC JWT validation on the backend and next-auth on the frontend
- **SCP**: Service Control Policy governing which AWS services are permitted in workload accounts
- **Ingestion_Lambda**: The AWS Lambda function triggered by SQS that runs the document ingestion pipeline (parse, chunk, embed via OpenAI, store in pgvector)
- **Audit_Log_Forwarder**: A Lambda function that forwards CloudWatch audit logs to S3 in the Log Archive account

## Requirements

### Requirement 1: CDK Project Initialization

**User Story:** As a DevOps engineer, I want a CDK project scaffolded under `infrastructure/cdk/` following the Schools CDK reference patterns, so that I can manage all Industrial AWS resources as code.

#### Acceptance Criteria

1. THE CDK_App SHALL use Python with `aws-cdk-lib==2.206.0` and `constructs>=10.0.0` as dependencies
2. THE Industrial_Config SHALL define an `EnvironmentConfig` dataclass with fields: `env_name`, `account_id`, `region`, `api_domain_prefix`, `app_domain_prefix`, `branch`, and `branch_previews_enabled`
3. THE Industrial_Config SHALL define dev configuration with placeholder account ID `666666666666`, region `us-east-1`, API domain prefix `api.industrial-dev`, app domain prefix `app.industrial-dev`, branch `develop`, and branch previews enabled
4. THE Industrial_Config SHALL define prod configuration with placeholder account ID `777777777777`, region `us-east-1`, API domain prefix `api.industrial`, app domain prefix `app.industrial`, branch `main`, and branch previews disabled
5. THE CDK_App SHALL apply the tags `workload=industrial`, `tenant=fin-tek`, `environment={env}`, and `managed-by=cdk` to all resources via CDK Aspects
6. THE CDK_App SHALL use the naming convention `industrial-{env}-{resource}` for all resource identifiers

### Requirement 2: VPC Networking

**User Story:** As a DevOps engineer, I want a VPC with public and private subnets across two availability zones, so that the RDS database is isolated in private subnets while public-facing services can route traffic.

#### Acceptance Criteria

1. THE VPC_Stack SHALL create a VPC with CIDR block `10.1.0.0/16` in `us-east-1`
2. THE VPC_Stack SHALL create two public subnets and two private subnets across availability zones `us-east-1a` and `us-east-1b`
3. THE VPC_Stack SHALL create an internet gateway attached to the VPC and associated with public subnet route tables
4. THE VPC_Stack SHALL create a NAT gateway in one public subnet with a route from private subnets to the NAT gateway
5. THE VPC_Stack SHALL create a VPC endpoint for S3 (gateway type) to avoid NAT charges for S3 traffic

### Requirement 3: RDS PostgreSQL with pgvector

**User Story:** As a DevOps engineer, I want an RDS PostgreSQL instance with pgvector extension support in private subnets, so that the application can store and query vector embeddings securely.

#### Acceptance Criteria

1. THE RDS_Stack SHALL create an RDS PostgreSQL 16 instance with instance class `db.t4g.micro` and database name `munitor`
2. THE RDS_Stack SHALL place the RDS instance in private subnets with a DB subnet group spanning both availability zones
3. THE RDS_Stack SHALL enable Multi-AZ for redundancy
4. THE RDS_Stack SHALL allocate 20 GB of storage with auto-scaling up to 100 GB
5. THE RDS_Stack SHALL enable storage encryption using the default AWS KMS key
6. THE RDS_Stack SHALL create a security group allowing inbound PostgreSQL traffic (port 5432) only from the App Runner and Ingestion_Lambda security groups
7. THE RDS_Stack SHALL set `publicly_accessible` to false
8. THE RDS_Stack SHALL create a custom parameter group for PostgreSQL 16 with `shared_preload_libraries` including `pg_stat_statements`
9. IF the environment is `prod`, THEN THE RDS_Stack SHALL retain a final snapshot on deletion
10. THE RDS_Stack SHALL store the database connection URL as a Secrets Manager secret named `industrial-{env}/database-url`

### Requirement 4: S3 Document Storage

**User Story:** As a DevOps engineer, I want an S3 bucket for document storage with versioning and encryption, so that uploaded documents are durable and secure.

#### Acceptance Criteria

1. THE S3_Stack SHALL create an S3 bucket named `industrial-{env}-documents-{accountId}`
2. THE S3_Stack SHALL enable versioning on the bucket
3. THE S3_Stack SHALL enable server-side encryption using S3-managed keys (SSE-S3)
4. THE S3_Stack SHALL block all public access on the bucket
5. THE S3_Stack SHALL create a lifecycle rule that transitions objects to Infrequent Access after 90 days
6. THE S3_Stack SHALL configure event notifications to send `s3:ObjectCreated:*` events to the ingestion SQS queue

### Requirement 5: ECR Repository

**User Story:** As a DevOps engineer, I want an ECR repository in the Shared Services account for the FastAPI Docker image, so that App Runner and Lambda can pull container images cross-account.

#### Acceptance Criteria

1. THE ECR_Stack SHALL create an ECR repository named `industrial-api` in the Shared Services account (`555555555555`)
2. THE ECR_Stack SHALL configure a lifecycle policy retaining 20 tagged images and deleting untagged images after 7 days
3. THE ECR_Stack SHALL grant cross-account pull access to the Industrial-Dev (`666666666666`) and Industrial-Prod (`777777777777`) accounts

### Requirement 6: App Runner API Service

**User Story:** As a DevOps engineer, I want the FastAPI backend deployed on App Runner with auto-scaling, so that the API serves requests with minimal operational overhead.

#### Acceptance Criteria

1. THE App_Runner_Stack SHALL create an App Runner service named `industrial-{env}-api` sourced from the `industrial-api` ECR repository
2. THE App_Runner_Stack SHALL configure the service with 1 vCPU and 2 GB memory per instance
3. THE App_Runner_Stack SHALL configure auto-scaling with minimum 1 instance, maximum 10 instances, and 100 max concurrency per instance
4. THE App_Runner_Stack SHALL configure a health check on HTTP path `/health` with 5-second interval
5. THE App_Runner_Stack SHALL inject secrets from Secrets Manager as runtime environment variables: `DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID`
6. THE App_Runner_Stack SHALL set the environment variable `S3_BUCKET_NAME` to the document storage bucket name
7. THE App_Runner_Stack SHALL create an IAM instance role granting read/write access to the S3 documents bucket and read access to the required Secrets Manager secrets
8. THE App_Runner_Stack SHALL configure a VPC connector so the App Runner service can reach the RDS instance in private subnets
9. THE App_Runner_Stack SHALL associate the custom domain `api.industrial.munitor.ai` (prod) or `api.industrial-dev.munitor.ai` (dev) with the service

### Requirement 7: SQS + Lambda Ingestion Worker

**User Story:** As a DevOps engineer, I want an event-driven ingestion pipeline using SQS and Lambda, so that document uploads trigger parsing, chunking, embedding, and storage with zero cost when idle.

#### Acceptance Criteria

1. THE Ingestion_Stack SHALL create an SQS queue named `industrial-{env}-ingestion` with a visibility timeout of 900 seconds (15 minutes)
2. THE Ingestion_Stack SHALL create a dead-letter queue named `industrial-{env}-ingestion-dlq` with a maximum receive count of 3
3. THE Ingestion_Stack SHALL create a Lambda function named `industrial-{env}-ingestion-worker` with a container image from the `industrial-api` ECR repository
4. THE Ingestion_Lambda SHALL have a timeout of 900 seconds (15 minutes) and 1024 MB memory
5. THE Ingestion_Lambda SHALL be triggered by the SQS ingestion queue with a batch size of 1
6. THE Ingestion_Lambda SHALL have environment variables: `DATABASE_URL`, `OPENAI_API_KEY`, and `S3_BUCKET_NAME`
7. THE Ingestion_Lambda SHALL have an IAM execution role granting: read/write to the S3 documents bucket, read access to Secrets Manager secrets, write access to the RDS database via the VPC, and SQS message consumption
8. THE Ingestion_Lambda SHALL be placed in the VPC private subnets with a security group allowing outbound internet access (for OpenAI API calls) and access to the RDS security group on port 5432
9. WHEN an S3 `ObjectCreated` event arrives on the SQS queue, THE Ingestion_Lambda SHALL download the document from S3, run the ingestion pipeline (parse, chunk, embed), and store the resulting chunks and embeddings in the RDS pgvector database
10. IF the Ingestion_Lambda fails to process a message after 3 attempts, THEN THE Ingestion_Stack SHALL route the message to the dead-letter queue

### Requirement 8: Amplify Frontend Hosting

**User Story:** As a DevOps engineer, I want the Next.js frontend deployed on Amplify Hosting with GitHub auto-deploy, so that frontend changes are deployed automatically on push.

#### Acceptance Criteria

1. THE Amplify_Stack SHALL create an Amplify app named `industrial-{env}-frontend` connected to the GitHub repository
2. THE Amplify_Stack SHALL configure the build to run `npm ci --legacy-peer-deps && npm run build` in the `web/` directory
3. THE Amplify_Stack SHALL set the environment variable `NEXT_PUBLIC_API_URL` to the App Runner API custom domain URL (HTTPS)
4. THE Amplify_Stack SHALL configure the `main` branch for prod and the `develop` branch for dev
5. WHERE the environment is dev, THE Amplify_Stack SHALL enable branch preview deployments
6. THE Amplify_Stack SHALL associate the custom domain `app.industrial.munitor.ai` (prod) or `app.industrial-dev.munitor.ai` (dev)
7. THE Amplify_Stack SHALL configure a SPA redirect rule (200 rewrite for `/<*>` to `/index.html`) for client-side routing

### Requirement 9: Secrets Management

**User Story:** As a DevOps engineer, I want application secrets stored in Secrets Manager with consistent naming, so that services can securely access credentials without hardcoding them.

#### Acceptance Criteria

1. THE Secrets_Stack SHALL create the following secrets per environment with naming pattern `industrial-{env}/{secret-name}`: `database-url`, `openai-api-key`, `cors-origins`, `entra-client-id`, `entra-client-secret`, `entra-tenant-id`
2. THE Secrets_Stack SHALL configure 90-day automatic rotation for the `database-url` secret using a rotation Lambda
3. THE Secrets_Stack SHALL create a CloudWatch alarm for rotation failures that publishes to an SNS topic
4. THE Secrets_Stack SHALL grant read access to the App Runner instance role and the Ingestion_Lambda execution role

### Requirement 10: DNS and TLS Certificates

**User Story:** As a DevOps engineer, I want custom domains with HTTPS on `munitor.ai` for both the API and frontend, so that users access the application via branded, secure URLs.

#### Acceptance Criteria

1. THE DNS_Stack SHALL create Route53 CNAME or ALIAS records in the existing `munitor.ai` hosted zone (Shared Services account `555555555555`) for `api.industrial.munitor.ai` and `app.industrial.munitor.ai` (prod)
2. THE DNS_Stack SHALL create Route53 records for `api.industrial-dev.munitor.ai` and `app.industrial-dev.munitor.ai` (dev)
3. THE DNS_Stack SHALL provision ACM certificates in `us-east-1` for the API and frontend custom domains with DNS validation
4. THE DNS_Stack SHALL configure the ACM certificates to auto-renew via DNS validation records in Route53

### Requirement 11: Observability

**User Story:** As a DevOps engineer, I want CloudWatch dashboards, alarms, and structured logging, so that I can monitor application health, detect issues, and debug problems.

#### Acceptance Criteria

1. THE Observability_Stack SHALL create a CloudWatch dashboard named `industrial-{env}-api-dashboard` displaying: request count, 5xx error rate, p95 latency, CPU utilization, memory utilization, and active App Runner instances
2. THE Observability_Stack SHALL create CloudWatch alarms for: 5xx error rate exceeding 1%, p95 latency exceeding 2 seconds, App Runner instances reaching 8 or more, and Ingestion_Lambda error rate exceeding 5%
3. THE Observability_Stack SHALL create an SNS topic named `industrial-{env}-observability-alarms` for alarm notifications
4. THE Observability_Stack SHALL create log groups: `/industrial-{env}/app-runner/api` with 90-day retention and `/industrial-{env}/audit-logs` with 7-year retention
5. THE Observability_Stack SHALL deploy an Audit_Log_Forwarder Lambda that subscribes to the audit log group and writes gzipped JSON to the `munitor-audit-logs` S3 bucket in the Log Archive account (`444444444444`) with key prefix `industrial-{env}/`

### Requirement 12: Microsoft Entra ID Authentication

**User Story:** As a DevOps engineer, I want the application to authenticate users via Microsoft Entra ID instead of Clerk, so that Fin-Tek employees can sign in with their existing Microsoft 365 accounts.

#### Acceptance Criteria

1. THE Auth_Integration SHALL configure the FastAPI backend to validate JWT tokens issued by Microsoft Entra ID using OIDC discovery (`https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration`)
2. THE Auth_Integration SHALL replace the `clerk_user_id` field on the User model with an `entra_object_id` field for mapping Entra ID users
3. THE Auth_Integration SHALL configure the Next.js frontend to use `next-auth` with the Microsoft Azure AD provider for sign-in
4. THE Auth_Integration SHALL read the Entra ID client ID, client secret, and tenant ID from Secrets Manager secrets (`industrial-{env}/entra-client-id`, `industrial-{env}/entra-client-secret`, `industrial-{env}/entra-tenant-id`)
5. WHEN a user authenticates via Entra ID, THE Auth_Integration SHALL extract the `tenant_id` and user role from JWT claims and apply them to request context for multi-tenant isolation

### Requirement 13: SCP Updates for Industrial Workload

**User Story:** As a DevOps engineer, I want the Workload Service Restriction SCP updated to allow Lambda, SQS, and any other AWS services required by the Industrial deployment, so that the workload accounts can provision all necessary resources.

#### Acceptance Criteria

1. THE SCP SHALL add the following services to the `WorkloadServiceRestriction` allowlist: `lambda:*`, `sqs:*`, `states:*`, `events:*`
2. THE SCP SHALL continue to restrict all other services not on the allowlist for accounts in the Workloads OU

### Requirement 14: CI/CD Pipelines

**User Story:** As a DevOps engineer, I want GitHub Actions pipelines for automated testing, building, and deploying the application, so that code changes flow safely from PR to production.

#### Acceptance Criteria

1. THE CICD_Pipeline SHALL create a `pr-check.yml` workflow triggered on pull requests that runs Python tests, ruff lint, CDK synth validation, and frontend type checking
2. THE CICD_Pipeline SHALL create a `deploy-dev.yml` workflow triggered on push to `main` that builds the Docker image, pushes to ECR, updates the App Runner service in Industrial-Dev, and runs smoke tests against the dev API endpoint
3. THE CICD_Pipeline SHALL create a `deploy-prod.yml` workflow triggered on release tags matching `v*` that requires manual approval before promoting the image to the Industrial-Prod App Runner service
4. THE CICD_Pipeline SHALL create a `cdk-deploy.yml` workflow triggered on push to `main` when files under `infrastructure/cdk/` change, that runs CDK synth, deploys dev stacks, requires manual approval, then deploys prod stacks
5. THE CICD_Pipeline SHALL use GitHub OIDC with `aws-actions/configure-aws-credentials@v4` for AWS authentication with no long-lived credentials
6. THE CICD_Pipeline SHALL create IAM roles in the Shared Services account: `github-actions-industrial-build`, `github-actions-industrial-deploy-dev`, and `github-actions-industrial-deploy-prod`, scoped to the industrial repository

### Requirement 15: GitHub OIDC IAM Roles

**User Story:** As a DevOps engineer, I want dedicated IAM roles for GitHub Actions scoped to the industrial repository, so that CI/CD pipelines authenticate securely without long-lived credentials.

#### Acceptance Criteria

1. THE ECR_Stack SHALL create an IAM role `github-actions-industrial-build` in the Shared Services account that trusts the existing GitHub OIDC provider and allows ECR push operations, scoped to `ref:refs/heads/*` of the industrial repository
2. THE ECR_Stack SHALL create an IAM role `github-actions-industrial-deploy-dev` that allows updating the App Runner service in Industrial-Dev, scoped to `ref:refs/heads/main`
3. THE ECR_Stack SHALL create an IAM role `github-actions-industrial-deploy-prod` that allows updating the App Runner service in Industrial-Prod, scoped to `ref:refs/tags/*`

