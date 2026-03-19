# Schools CDK Infrastructure — Complete Overview

Use this as a reference when building the Industrial Service Knowledge Base CDK deployment in the same AWS Organization. Everything below describes what's already deployed/defined for the School Assessment System so you can avoid naming collisions, reuse shared resources, and understand the account/OU structure.

---

## 1. AWS Organization Structure

```
Root (Munitor AI)
├── Security OU
│   ├── Security Account (333333333333)     — GuardDuty, Security Hub, IAM Identity Center
│   └── Log Archive Account (444444444444)  — CloudTrail S3, Audit Logs S3
├── Infrastructure OU
│   └── Shared Services Account (555555555555) — ECR, Route53, GitHub OIDC roles
└── Workloads OU
    ├── Schools-Prod Account (222222222222)  — App Runner, Amplify, Secrets Manager, CloudWatch
    └── Schools-Dev Account (111111111111)   — Staging mirror of prod
```

Management Account (000000000000) manages billing, SCPs, and org policies.

All account IDs above are placeholders defined in `infra/lib/config.ts`. Replace before deployment.

**For Industrial**: Add new accounts under the Workloads OU: `Industrial-Prod`, `Industrial-Dev`. First tenant: `fin-tek`. Resource prefix: `industrial-{env}`. Tagging strategy: `workload=industrial`, `tenant=fin-tek`.

---

## 2. CDK Project Layout

```
infra/
├── bin/app.ts                              # Entry point — instantiates all stacks
├── lib/
│   ├── config.ts                           # EnvironmentConfig interface, account IDs, constants
│   ├── constructs/
│   │   ├── app-runner-service.ts           # Reusable App Runner construct
│   │   ├── amplify-app.ts                  # Reusable Amplify Hosting construct
│   │   ├── secrets-bundle.ts               # Secrets Manager secret group + rotation
│   │   ├── observability-stack.ts          # CloudWatch dashboard + alarms + log groups
│   │   └── audit-log-forwarder.ts          # Lambda + subscription filter → S3
│   └── stacks/
│       ├── organization-stack.ts           # AWS Org, OUs, accounts
│       ├── scp-stack.ts                    # 5 Service Control Policies
│       ├── identity-center-stack.ts        # IAM Identity Center permission sets
│       ├── log-archive-stack.ts            # CloudTrail, S3 buckets (Object Lock, 7yr)
│       ├── shared-services-stack.ts        # ECR, Route53, GitHub OIDC
│       ├── schools-app-stack.ts            # App Runner + Amplify per env
│       ├── schools-secrets-stack.ts        # Secrets Manager per env
│       └── schools-observability-stack.ts  # Dashboards + alarms + audit forwarder per env
├── cdk.json                                # CDK app config + feature flags
├── package.json                            # aws-cdk-lib 2.206.0, constructs ^10.0.0
└── tsconfig.json
```

**CDK version**: `aws-cdk-lib@2.206.0`, `aws-cdk@2.1023.0` (CLI), Node 20, TypeScript ~5.6.3

---

## 3. Stacks — What's Deployed Where

### 3.1 Management Account (11 stacks total across all accounts)

| Stack | Account | Description |
|-------|---------|-------------|
| `OrganizationStack` | Management | AWS Org, 3 OUs, 5 accounts, SSM param exports |
| `ScpStack` | Management | 5 SCPs attached to root and Workloads OU |

### 3.2 Security Account

| Stack | Account | Description |
|-------|---------|-------------|
| `IdentityCenterStack` | Security | 4 permission sets, 5 account assignments |

### 3.3 Log Archive Account

| Stack | Account | Description |
|-------|---------|-------------|
| `LogArchiveStack` | Log Archive | CloudTrail trail, 2 S3 buckets, KMS key, SNS alarm |

### 3.4 Shared Services Account

| Stack | Account | Description |
|-------|---------|-------------|
| `SharedServicesStack` | Shared Services | ECR repo, Route53 zone, GitHub OIDC provider, 3 IAM roles |

### 3.5 Workload Accounts (per-environment: dev + prod)

| Stack | Account | Description |
|-------|---------|-------------|
| `SchoolsSecrets-{env}` | Schools-{env} | 5 Secrets Manager secrets + rotation Lambda |
| `SchoolsApp-{env}` | Schools-{env} | App Runner service + Amplify app + Route53 records |
| `SchoolsObservability-{env}` | Schools-{env} | Dashboard, 5 alarms, SNS, log groups, audit forwarder |

---

## 4. Service Control Policies (SCPs)

All attached to org root unless noted:

| SCP | Scope | What it does |
|-----|-------|-------------|
| `RegionRestriction` | Root (all accounts) | Deny all actions outside `us-east-1` except IAM, STS, Organizations, CloudFront |
| `CloudTrailProtection` | Root | Deny `cloudtrail:StopLogging`, `cloudtrail:DeleteTrail` |
| `PreventOrgLeave` | Root | Deny `organizations:LeaveOrganization` |
| `NoIAMUsers` | Root | Deny `iam:CreateUser`, `iam:CreateAccessKey` |
| `WorkloadServiceRestriction` | Workloads OU only | Allow only: App Runner, Amplify, Secrets Manager, ECR, CloudWatch, Logs, S3, RDS, EC2, ELB, IAM, STS, Organizations, CloudFormation, SSM, KMS, SNS, Tag |

**For Industrial**: If the knowledge base needs AWS services not in this allowlist (e.g., Lambda, DynamoDB, Bedrock, OpenSearch), update this SCP. File: `infra/lib/stacks/scp-stack.ts`.

---

## 5. Shared Services — Resources You Can Reuse

### 5.1 ECR Repository
- Name: `school-assessment-api`
- Lifecycle: retain 20 tagged images, delete untagged after 7 days
- Cross-account pull: Schools-Prod and Schools-Dev accounts

**For Industrial**: Create a separate ECR repo (e.g., `industrial-api`) in the same Shared Services stack or a new stack. Add cross-account pull for `Industrial-Prod` and `Industrial-Dev` accounts.

### 5.2 Route53 Hosted Zone
- Zone: `munitor.ai`
- Hosted in Shared Services account

**For Industrial**: Add records to this zone (e.g., `api.industrial.munitor.ai`, `app.industrial.munitor.ai`) or create a separate hosted zone if using a different domain.

### 5.3 GitHub OIDC Provider
- Already created — one per account, so reuse it
- Trust: `token.actions.githubusercontent.com`

**For Industrial**: Reuse the same OIDC provider. Add new IAM roles scoped to the industrial repo (e.g., `github-actions-industrial-build`, `github-actions-industrial-deploy-dev`).

### 5.4 GitHub Actions IAM Roles
- `github-actions-build` — push to ECR (scoped to `ref:refs/heads/*`)
- `github-actions-deploy-dev` — update App Runner in Schools-Dev (scoped to `ref:refs/heads/main`)
- `github-actions-deploy-prod` — update App Runner in Schools-Prod (scoped to `ref:refs/tags/*`)

**For Industrial**: Create separate roles: `github-actions-industrial-build`, `github-actions-industrial-deploy-dev`, `github-actions-industrial-deploy-prod` — scoped to the industrial repo.

---

## 6. Constructs — Reusable Building Blocks

### 6.1 AppRunnerService (`infra/lib/constructs/app-runner-service.ts`)
- ECR image source with cross-account access role
- Instance: 1 vCPU, 2 GB memory
- Auto-scaling: min 1, max 10, 300s cooldown, 100 max concurrency
- Health check: HTTP `/health`, 5s interval
- Secrets Manager integration via runtime environment secrets
- Custom domain via AwsCustomResource SDK call
- Service naming: `schools-{env}-api`

### 6.2 AmplifyApp (`infra/lib/constructs/amplify-app.ts`)
- GitHub source, branch `main` (prod) or `develop` (dev)
- Build: `npm ci && npm run build` in `web/` directory
- `VITE_API_URL` env var pointing to App Runner custom domain
- Branch preview deployments: enabled for dev only
- Custom domain association
- SPA redirect rule for client-side routing

### 6.3 SecretsBundle (`infra/lib/constructs/secrets-bundle.ts`)
- Creates 5 secrets per environment: `database-url`, `clerk-secret-key`, `clerk-jwt-issuer`, `sentry-dsn`, `cors-origins`
- Secret naming: `schools-{env}/{secret-name}`
- 90-day rotation Lambda for `database-url`
- CloudWatch alarm for rotation failures → SNS
- Optional cross-account IAM policy for App Runner task role

### 6.4 Observability (`infra/lib/constructs/observability-stack.ts`)
- CloudWatch dashboard: request count, 5xx error rate, p95 latency, CPU, memory, active instances
- 5 alarms: 5xx > 1%, p95 > 2s, instances >= 8, audit log write failures, Sentry > 10 exceptions
- SNS topic for alarm notifications
- Log groups: `/schools-{env}/app-runner/api` (90-day), `/schools-{env}/audit-logs` (7-year)

### 6.5 AuditLogForwarder (`infra/lib/constructs/audit-log-forwarder.ts`)
- Lambda function subscribed to audit log group
- Forwards log events to S3 in Log Archive account as gzipped JSON
- S3 key pattern: `schools-{env}/YYYY/MM/DD/HHMMSS-{requestId}.json.gz`
- Cross-account S3 write via IAM policy

---

## 7. Log Archive — S3 Buckets

| Bucket | Purpose | Retention |
|--------|---------|-----------|
| `munitor-cloudtrail-logs` | Organization-wide CloudTrail events | Object Lock compliance 7yr, Glacier Deep Archive after 365d |
| `munitor-audit-logs` | Application audit logs exported from CloudWatch | Same retention settings |

Both buckets: versioning enabled, SSE-KMS encryption, public access blocked, delete denied by bucket policy.

**For Industrial**: Use the same `munitor-audit-logs` bucket with prefix `industrial-prod/` and `industrial-dev/`, or create a separate bucket if compliance requirements differ.

---

## 8. Identity Center Permission Sets

| Permission Set | Managed Policy | Session | Target Accounts |
|---------------|---------------|---------|-----------------|
| OrganizationAdmin | AdministratorAccess | 8h | Management |
| SecurityAuditor | SecurityAudit | 8h | Security, Log Archive |
| Developer | PowerUserAccess | 8h | Schools-Dev |
| ProductionOperator | ReadOnlyAccess | 4h | Schools-Prod |

**For Industrial**: Add permission sets like `IndustrialDeveloper` (targeting Industrial-Dev) and `IndustrialOperator` (targeting Industrial-Prod).

---

## 9. CI/CD Pipelines (GitHub Actions)

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `pr-check.yml` | PR to main | Python tests (80% coverage gate), CDK jest tests, ruff lint, tsc check |
| `deploy-dev.yml` | Push to main | Build Docker → push to ECR → update App Runner (Schools-Dev) → smoke tests |
| `deploy-prod.yml` | Release tag `v*` | Manual approval gate → promote image to Schools-Prod App Runner |
| `cdk-deploy.yml` | Push to main (infra/ changes) | CDK synth → deploy dev stacks → manual approval → deploy prod stacks |

All workflows use GitHub OIDC (`aws-actions/configure-aws-credentials@v4`) — no long-lived credentials.

GitHub Secrets needed:
- `AWS_DEPLOY_DEV_ROLE_ARN`
- `AWS_DEPLOY_PROD_ROLE_ARN`
- `AWS_CDK_ROLE_ARN`

---

## 10. Resource Naming Conventions

Everything uses the pattern `schools-{env}-{resource}` to avoid collisions:

- App Runner: `schools-dev-api`, `schools-prod-api`
- Amplify: `schools-dev-frontend`, `schools-prod-frontend`
- Secrets: `schools-dev/database-url`, `schools-prod/clerk-secret-key`, etc.
- Log groups: `/schools-dev/app-runner/api`, `/schools-prod/audit-logs`
- IAM roles: `schools-dev-apprunner-access`, `schools-prod-apprunner-instance`
- Auto-scaling: `schools-dev-autoscaling`, `schools-prod-autoscaling`
- Dashboard: `schools-dev-api-dashboard`, `schools-prod-api-dashboard`
- Alarms: `schools-dev-5xx-error-rate`, `schools-prod-p95-latency`, etc.
- SNS topics: `schools-dev-observability-alarms`, `schools-prod-secret-rotation-alarm`
- Lambda: `schools-dev-secret-rotation`, `schools-prod-audit-log-forwarder`

**For Industrial**: Use `industrial-{env}-{resource}` as your prefix. First tenant tag: `tenant=fin-tek`. Examples:
- App Runner: `industrial-dev-api`, `industrial-prod-api`
- Secrets: `industrial-dev/database-url`, `industrial-prod/sentry-dsn`
- Log groups: `/industrial-dev/app-runner/api`, `/industrial-prod/audit-logs`
- IAM roles: `industrial-dev-apprunner-access`, `industrial-prod-apprunner-instance`
- Dashboard: `industrial-dev-api-dashboard`
- Alarms: `industrial-dev-5xx-error-rate`

---

## 11. Environment Config Interface

```typescript
export interface EnvironmentConfig {
  readonly envName: string;        // 'dev' or 'prod'
  readonly accountId: string;      // AWS account ID
  readonly region: string;         // 'us-east-1'
  readonly apiDomainPrefix: string;  // e.g. 'api.schools-dev'
  readonly appDomainPrefix: string;  // e.g. 'app.schools-dev'
  readonly branch: string;           // Git branch for deployments
  readonly branchPreviewsEnabled: boolean;
}
```

All constructs are parameterized by this interface, so dev and prod share the same code with different config. Industrial should follow the same pattern with its own configs:

```typescript
// Example for Industrial
export const INDUSTRIAL_DEV_CONFIG: EnvironmentConfig = {
  envName: 'dev',
  accountId: '666666666666',  // Industrial-Dev account
  region: 'us-east-1',
  apiDomainPrefix: 'api.industrial-dev',
  appDomainPrefix: 'app.industrial-dev',
  branch: 'develop',
  branchPreviewsEnabled: true,
};

export const INDUSTRIAL_PROD_CONFIG: EnvironmentConfig = {
  envName: 'prod',
  accountId: '777777777777',  // Industrial-Prod account
  region: 'us-east-1',
  apiDomainPrefix: 'api.industrial',
  appDomainPrefix: 'app.industrial',
  branch: 'main',
  branchPreviewsEnabled: false,
};
```

---

## 12. Cross-Account References

CDK can't use token references across accounts. The Schools setup handles this with:
- SSM parameters in Management Account for account IDs and OU IDs
- Hardcoded resource names/ARNs constructed from known patterns (e.g., ECR URI built from account ID + region + repo name)
- `cdk.json` context for values like `hostedZoneId` that are only known after initial deployment

---

## 13. Key Dependencies Between Stacks

```
OrganizationStack
├── ScpStack (needs OU IDs)
├── IdentityCenterStack (needs account IDs)
├── LogArchiveStack (needs org ID)
└── SharedServicesStack (needs account IDs)
    └── SchoolsApp-{env} (needs ECR URI, hosted zone)
        └── SchoolsObservability-{env} (needs App Runner service name)

SchoolsSecrets-{env}
└── SchoolsApp-{env} (needs secret ARNs)
```

---

## 14. What to Watch Out For — Adding Industrial Workload

1. **SCP allowlist**: The `WorkloadServiceRestriction` SCP on the Workloads OU limits which AWS services can be used. If Industrial needs services not listed (Lambda, DynamoDB, Bedrock, OpenSearch, etc.), update the SCP first.

2. **ECR repo**: Create `industrial-api` (or similar). Don't share `school-assessment-api`.

3. **Route53**: Add records to the existing `munitor.ai` zone (e.g., `api.industrial.munitor.ai`) or create a new zone for a different domain.

4. **GitHub OIDC**: The provider already exists in Shared Services. Just add new IAM roles scoped to the industrial repo.

5. **CloudTrail**: Already org-wide — Industrial accounts are automatically covered.

6. **Log Archive buckets**: Use `industrial-{env}/` as S3 key prefix for audit logs.

7. **Naming**: Use `industrial-{env}-` prefix for all resources. Tag everything with `workload=industrial`, `tenant=fin-tek`.

8. **CDK app entry point**: Recommended: create a separate CDK app in the industrial repo rather than adding to `infra/bin/app.ts` here. The org-level stacks (Organization, SCP, Identity Center, Log Archive, Shared Services) are shared — only the workload stacks are per-product.

9. **Secrets**: Create your own SecretsBundle with different secret names under `industrial-{env}/` prefix. The construct is reusable.

10. **Observability**: The Observability construct is reusable. Pass `industrial-{env}-api` as `appRunnerServiceName`.

11. **Tagging strategy**: Apply these tags to all Industrial resources:
    ```
    workload: industrial
    tenant: fin-tek
    environment: dev | prod
    managed-by: cdk
    ```
    Schools uses `workload: schools`, `tenant: peck-school` for comparison.
