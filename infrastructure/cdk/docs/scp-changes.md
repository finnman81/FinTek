# SCP Changes Required for Industrial Workload

## Status: BLOCKER — Must be resolved before CDK deploy

## Summary

The `WorkloadServiceRestriction` SCP on the Workloads OU currently allows only these services:

```
apprunner, amplify, secretsmanager, ecr, cloudwatch, logs, s3, rds, ec2,
elasticloadbalancing, iam, sts, organizations, cloudformation, ssm, kms, sns, tag
```

The Industrial workload needs `lambda:*` and `sqs:*` for the ingestion pipeline (SQS queue + Lambda worker). Both are currently blocked by this SCP. If you deploy Industrial-Dev or Industrial-Prod under the Workloads OU without this change, the Lambda function and SQS queue will fail to create.

## Services to Add to Allowlist

Add the following actions to the `AllowApprovedServices` statement in the `WorkloadServiceRestriction` SCP:

- `lambda:*`
- `sqs:*`
- `states:*` (Step Functions — future use)
- `events:*` (EventBridge — future use)

This won't affect the Schools workload since it doesn't use Lambda or SQS.

## Where to Make the Change

- Repository: shared `infra/` repo (not this CDK project)
- File: `scp-stack.ts`
- Policy: `WorkloadServiceRestriction` → `AllowApprovedServices` statement

The SCP applies to all accounts in the Workloads OU. All other services not on the allowlist remain restricted.

## Requirements Traceability

- Requirement 13.1: Add `lambda:*`, `sqs:*`, `states:*`, `events:*` to the allowlist
- Requirement 13.2: Continue restricting all other services not on the allowlist
