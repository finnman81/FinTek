# Deployment Readiness Review (Web + Mobile)

Date: 2026-02-25
Scope: AWS Terraform, container runtime, Next.js web deployment, and mobile/PWA readiness.

## Executive Summary

Overall readiness is **moderate**: architecture direction is solid, but there are multiple production blockers in infrastructure security/networking and a few functional gaps in web/mobile deploy behavior.

- **Critical blockers**: ECS/RDS are configured in public subnets with public IP exposure; Secrets Manager secrets are created without values in Terraform; PWA service worker registration appears missing.
- **High-risk gaps**: weak CI/build robustness in Amplify env injection; missing runtime error handling in mobile upload polling; lack of request timeouts/retries for field connectivity.
- **Operational improvements**: add deep readiness checks to ALB, tighten IAM/secret rotation strategy, introduce autoscaling and safer rollout defaults.

## Findings

## 1) Infrastructure / Terraform

### 1.1 Public networking posture for data and compute (Critical)
- ECS services run with `assign_public_ip = true` and use public subnets.
- RDS subnet group also uses public subnets and DB is marked `publicly_accessible = true`.
- While SG rules are somewhat scoped, this is an unnecessary internet exposure pattern for production and increases blast radius.

**Impact**
- Increased attack surface and compliance concerns.
- Harder to enforce zero-trust pathing and private service-to-service connectivity.

**Recommendation**
- Move ECS tasks and RDS to private subnets.
- Keep only ALB public.
- Add NAT gateway/egress controls, or VPC endpoints for S3/Secrets/CloudWatch where practical.

### 1.2 Secrets are declared but not versioned (Critical)
- Terraform creates `aws_secretsmanager_secret` resources but does not set `aws_secretsmanager_secret_version` values.
- ECS task definitions reference those secrets directly.

**Impact**
- ECS tasks can fail startup when secret values are absent.

**Recommendation**
- Add secret version resources in Terraform (or documented pre-deploy step that is enforced in CI).
- Add preflight validation in deployment pipeline.

### 1.3 TLS cert validation workflow incomplete in IaC (High)
- ACM cert is created, but DNS validation records and certificate validation resource are not present.

**Impact**
- HTTPS listener provisioning can stall/fail depending on orchestration timing.

**Recommendation**
- Add Route53 validation records + `aws_acm_certificate_validation`.

### 1.4 Health check is shallow only (Medium)
- ALB target group uses `/health`, which intentionally does not verify DB.

**Impact**
- Traffic can continue routing to instances even if DB is unavailable.

**Recommendation**
- Use a readiness path that verifies critical dependencies (or include separate startup gating).

## 2) Web deployment and CI/CD

### 2.1 Amplify build step can fail when env vars are missing (High)
- Build command appends env vars with `env | grep ... >> .env.production`.
- `grep` exits non-zero when no matches are found; in strict shell mode this can fail build.

**Recommendation**
- Use a guarded command (`grep ... || true`) or explicit key-by-key writes.

### 2.2 Package version alignment risk (Medium)
- Current `next` version is `14.2.0`, while Clerk peer warns expect `^14.2.25` or newer compatible range.

**Impact**
- Increased risk of subtle runtime/build incompatibilities.

**Recommendation**
- Pin to a mutually compatible Next/Clerk matrix and enforce with CI lockfile checks.

## 3) Mobile/PWA readiness

### 3.1 Service worker registration appears missing (Critical)
- PWA build config and worker source exist, but no client-side service worker registration was found.

**Impact**
- Offline fallback and installability behaviors may not activate as intended.

**Recommendation**
- Register `/sw.js` from a client component loaded in root layout (prod only).
- Add a smoke E2E test that validates SW active state and offline fallback route.

### 3.2 Upload polling lacks error handling for status checks (High)
- `documentStatus(...).then(...)` in poll loop has no `.catch(...)`.

**Impact**
- Intermittent mobile network drops can create noisy unhandled rejections and stale UI state.

**Recommendation**
- Add bounded retry/backoff + catch + user-visible transient warning.

### 3.3 API calls have no timeout / abort strategy (High)
- Frontend fetch helpers do not set request timeout or AbortController.

**Impact**
- Field users on poor connectivity can experience hanging actions with no recovery.

**Recommendation**
- Add per-endpoint timeout defaults and retry policy for idempotent calls.

## 4) Container/runtime hardening

### 4.1 Container runs as root (Medium)
- Dockerfile does not create/use non-root user.

**Recommendation**
- Add non-root runtime user and ensure filesystem permissions set accordingly.

### 4.2 Image missing migration assets (Low/Medium)
- Docker image copies `src/` and `config/` only.

**Impact**
- Running DB migrations from deployed image is not directly possible.

**Recommendation**
- Either ship Alembic assets for operational parity or define separate migration job image/step.

## Suggested pre-production checklist

1. Rework network topology to private app/data tiers.
2. Add Secrets Manager values + cert validation resources in Terraform.
3. Fix Amplify env ingestion command robustness.
4. Implement SW registration + offline E2E checks.
5. Add fetch timeouts/retries and upload poll error handling.
6. Add deployment gates: terraform validate/plan checks, smoke tests (`/health`, `/api/v1/health/db`, chat roundtrip).
7. Harden container runtime (non-root, image scan policy, explicit dependency lock checks).

## Nice-to-have next

- Add ALB WAF rules and rate limits once traffic grows.
- Add CloudWatch alarms for 5xx rate, p95 latency, and worker queue lag.
- Add staged deploy strategy (blue/green or canary) for API service.
- Add mobile UX telemetry (upload failure reasons, latency percentiles by network type).
