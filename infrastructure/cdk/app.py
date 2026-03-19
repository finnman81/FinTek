#!/usr/bin/env python3
"""CDK app entry point — instantiates all Industrial stacks for dev and prod."""

import aws_cdk as cdk

from stacks.config import (
    INDUSTRIAL_DEV,
    INDUSTRIAL_PROD,
    SHARED_SERVICES_ACCOUNT,
    EnvironmentConfig,
)
from constructs.tagging_aspect import TaggingAspect

from stacks.vpc_stack import VpcStack
from stacks.s3_stack import S3Stack
from stacks.ecr_stack import EcrStack
from stacks.secrets_stack import SecretsStack
from stacks.rds_stack import RdsStack
from stacks.ingestion_stack import IngestionStack
from stacks.app_runner_stack import AppRunnerStack
from stacks.amplify_stack import AmplifyStack
from stacks.dns_stack import DnsStack
from stacks.observability_stack import ObservabilityStack


def create_environment_stacks(
    app: cdk.App,
    config: EnvironmentConfig,
    ecr_stack: EcrStack,
) -> None:
    """Instantiate all workload stacks for a single environment."""

    env = cdk.Environment(account=config.account_id, region=config.region)
    prefix = f"industrial-{config.env_name}"

    # Foundational stacks (no cross-stack deps)
    vpc_stack = VpcStack(app, f"{prefix}-vpc", config=config, env=env)
    s3_stack = S3Stack(app, f"{prefix}-s3", config=config, env=env)
    secrets_stack = SecretsStack(app, f"{prefix}-secrets", config=config, env=env)

    # RDS depends on VPC and Secrets
    rds_stack = RdsStack(
        app,
        f"{prefix}-rds",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        env=env,
    )

    # Ingestion depends on VPC, S3, Secrets, RDS, ECR
    ingestion_stack = IngestionStack(
        app,
        f"{prefix}-ingestion",
        config=config,
        vpc_stack=vpc_stack,
        s3_stack=s3_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        ecr_stack=ecr_stack,
        env=env,
    )

    # Wire S3 ObjectCreated events to the ingestion queue (done here to
    # avoid a cyclic cross-stack dependency between S3 and Ingestion stacks).
    s3_stack.add_event_notification(ingestion_stack.queue)

    # App Runner depends on VPC, Secrets, RDS, S3, ECR
    app_runner_stack = AppRunnerStack(
        app,
        f"{prefix}-app-runner",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        s3_stack=s3_stack,
        ecr_stack=ecr_stack,
        env=env,
    )

    # Amplify depends on App Runner
    amplify_stack = AmplifyStack(
        app,
        f"{prefix}-amplify",
        config=config,
        app_runner_stack=app_runner_stack,
        env=env,
    )

    # DNS depends on App Runner and Amplify
    dns_stack = DnsStack(
        app,
        f"{prefix}-dns",
        config=config,
        app_runner_stack=app_runner_stack,
        amplify_stack=amplify_stack,
        env=env,
    )

    # Observability depends on App Runner and Ingestion
    observability_stack = ObservabilityStack(
        app,
        f"{prefix}-observability",
        config=config,
        app_runner_stack=app_runner_stack,
        ingestion_stack=ingestion_stack,
        env=env,
    )

    # Apply mandatory tags to every stack in this environment
    all_stacks = [
        vpc_stack,
        s3_stack,
        secrets_stack,
        rds_stack,
        ingestion_stack,
        app_runner_stack,
        amplify_stack,
        dns_stack,
        observability_stack,
    ]
    for stack in all_stacks:
        cdk.Aspects.of(stack).add(TaggingAspect(config))


app = cdk.App()

# ECR lives in the Shared Services account (not per-environment)
shared_env = cdk.Environment(account=SHARED_SERVICES_ACCOUNT, region="us-east-1")
ecr_stack = EcrStack(app, "industrial-ecr", env=shared_env)
cdk.Aspects.of(ecr_stack).add(TaggingAspect(INDUSTRIAL_PROD))

# Instantiate all stacks for each environment
create_environment_stacks(app, INDUSTRIAL_DEV, ecr_stack)
create_environment_stacks(app, INDUSTRIAL_PROD, ecr_stack)

app.synth()
