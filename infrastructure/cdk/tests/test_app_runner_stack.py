"""Unit tests for App Runner stack.

Validates service name, CPU/memory, auto-scaling config, health check,
VPC connector, IAM role, and secrets injection against Requirements 6.1–6.8.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, INDUSTRIAL_PROD, RESOURCE_PREFIX
from stacks.app_runner_stack import AppRunnerStack
from stacks.ecr_stack import EcrStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_app_runner_template(config=None) -> assertions.Template:
    """Synthesize the App Runner stack and return the CloudFormation template."""
    if config is None:
        config = INDUSTRIAL_DEV
    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    ecr_stack = EcrStack(app, f"test-ecr-{config.env_name}", env=shared_env)

    app_runner_stack = AppRunnerStack(
        app, f"test-apprunner-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        s3_stack=s3_stack,
        ecr_stack=ecr_stack,
        env=env,
    )
    return assertions.Template.from_stack(app_runner_stack)


class TestAppRunnerStack:
    """Unit tests for AppRunnerStack — Requirements 6.1–6.8."""

    def setup_method(self) -> None:
        self.template = _synth_app_runner_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 6.1 — Service named industrial-{env}-api
    def test_service_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {"ServiceName": f"{self.prefix}-api"},
        )

    # Requirement 6.1 — Service sourced from ECR
    def test_service_ecr_source(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {
                "SourceConfiguration": assertions.Match.object_like({
                    "ImageRepository": assertions.Match.object_like({
                        "ImageRepositoryType": "ECR",
                    }),
                }),
            },
        )

    # Requirement 6.2 — 1 vCPU (1024) and 2 GB memory (2048)
    def test_cpu_memory(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {
                "InstanceConfiguration": assertions.Match.object_like({
                    "Cpu": "1024",
                    "Memory": "2048",
                }),
            },
        )

    # Requirement 6.3 — Auto-scaling: min 1, max 10, 100 max concurrency
    def test_auto_scaling_config(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::AutoScalingConfiguration",
            {
                "MinSize": 1,
                "MaxSize": 10,
                "MaxConcurrency": 100,
            },
        )

    # Requirement 6.3 — Service references auto-scaling configuration
    def test_service_references_auto_scaling(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {
                "AutoScalingConfigurationArn": assertions.Match.any_value(),
            },
        )

    # Requirement 6.4 — Health check on /health with 5s interval
    def test_health_check(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {
                "HealthCheckConfiguration": assertions.Match.object_like({
                    "Protocol": "HTTP",
                    "Path": "/health",
                    "Interval": 5,
                }),
            },
        )

    # Requirement 6.5 — All 6 secrets injected as RuntimeEnvironmentSecrets
    def test_secrets_injection(self) -> None:
        services = self.template.find_resources("AWS::AppRunner::Service")
        service = list(services.values())[0]
        image_config = (
            service["Properties"]["SourceConfiguration"]
            ["ImageRepository"]["ImageConfiguration"]
        )
        secret_names = {e["Name"] for e in image_config["RuntimeEnvironmentSecrets"]}
        expected = {
            "DATABASE_URL", "OPENAI_API_KEY", "CORS_ORIGINS",
            "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET", "ENTRA_TENANT_ID",
        }
        assert secret_names == expected

    # Requirement 6.6 — S3_BUCKET_NAME environment variable set
    def test_s3_bucket_env_var(self) -> None:
        services = self.template.find_resources("AWS::AppRunner::Service")
        service = list(services.values())[0]
        image_config = (
            service["Properties"]["SourceConfiguration"]
            ["ImageRepository"]["ImageConfiguration"]
        )
        env_vars = {e["Name"]: e["Value"] for e in image_config["RuntimeEnvironmentVariables"]}
        expected_bucket = f"{self.prefix}-documents-{INDUSTRIAL_DEV.account_id}"
        assert env_vars["S3_BUCKET_NAME"] == expected_bucket

    # Requirement 6.7 — IAM instance role with S3 and Secrets Manager permissions
    def test_instance_role_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": assertions.Match.object_like({
                    "Statement": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Principal": assertions.Match.object_like({
                                "Service": "tasks.apprunner.amazonaws.com",
                            }),
                        }),
                    ]),
                }),
            },
        )

    # Requirement 6.7 — Instance role has S3 permissions
    def test_instance_role_s3_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": assertions.Match.object_like({
                    "Statement": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Action": assertions.Match.array_with(["s3:GetObject"]),
                        }),
                    ]),
                }),
            },
        )

    # Requirement 6.8 — VPC connector exists
    def test_vpc_connector(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::VpcConnector",
            {
                "VpcConnectorName": f"{self.prefix}-api-vpc-connector",
                "Subnets": assertions.Match.any_value(),
                "SecurityGroups": assertions.Match.any_value(),
            },
        )

    # Requirement 6.8 — Service uses VPC egress configuration
    def test_service_vpc_egress(self) -> None:
        self.template.has_resource_properties(
            "AWS::AppRunner::Service",
            {
                "NetworkConfiguration": assertions.Match.object_like({
                    "EgressConfiguration": assertions.Match.object_like({
                        "EgressType": "VPC",
                        "VpcConnectorArn": assertions.Match.any_value(),
                    }),
                }),
            },
        )

    # Requirement 6.9 — Custom domain association
    def test_custom_domain_association(self) -> None:
        self.template.has_resource("AWS::AppRunner::CustomDomainAssociation", {})

    # Exactly 1 App Runner service
    def test_service_count(self) -> None:
        self.template.resource_count_is("AWS::AppRunner::Service", 1)

    # Exactly 1 VPC connector
    def test_vpc_connector_count(self) -> None:
        self.template.resource_count_is("AWS::AppRunner::VpcConnector", 1)

    # Exactly 1 auto-scaling configuration
    def test_auto_scaling_count(self) -> None:
        self.template.resource_count_is("AWS::AppRunner::AutoScalingConfiguration", 1)

    # ECR access role exists (for pulling images)
    def test_ecr_access_role(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": assertions.Match.object_like({
                    "Statement": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Principal": assertions.Match.object_like({
                                "Service": "build.apprunner.amazonaws.com",
                            }),
                        }),
                    ]),
                }),
            },
        )

    # Stack exposes expected properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        shared_env = cdk.Environment(account="555555555555", region="us-east-1")

        vpc_stack = VpcStack(app, "test-vpc-props", config=config, env=env)
        secrets_stack = SecretsStack(app, "test-secrets-props", config=config, env=env)
        rds_stack = RdsStack(
            app, "test-rds-props",
            config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
        )
        s3_stack = S3Stack(app, "test-s3-props", config=config, env=env)
        ecr_stack = EcrStack(app, "test-ecr-props", env=shared_env)

        ar = AppRunnerStack(
            app, "test-ar-props",
            config=config,
            vpc_stack=vpc_stack, secrets_stack=secrets_stack,
            rds_stack=rds_stack, s3_stack=s3_stack, ecr_stack=ecr_stack,
            env=env,
        )
        assert ar.service_url is not None
        assert ar.service_arn is not None
        assert ar.service_name is not None
        assert ar.instance_role is not None
