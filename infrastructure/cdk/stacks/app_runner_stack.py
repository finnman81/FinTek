"""App Runner stack for Industrial workload.

Creates an App Runner service sourced from ECR, with VPC connector for RDS
access, auto-scaling, health checks, secrets injection from Secrets Manager,
and an IAM instance role with S3 and Secrets Manager permissions.
Uses L1 CfnService construct for full feature control.
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_apprunner as apprunner,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

from stacks.config import HOSTED_ZONE_NAME, RESOURCE_PREFIX, SHARED_SERVICES_ACCOUNT, EnvironmentConfig
from stacks.ecr_stack import EcrStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack

# Map of App Runner env var name → Secrets Manager secret short name
_SECRET_ENV_MAP = {
    "DATABASE_URL": "database-url",
    "OPENAI_API_KEY": "openai-api-key",
    "CORS_ORIGINS": "cors-origins",
    "ENTRA_CLIENT_ID": "entra-client-id",
    "ENTRA_CLIENT_SECRET": "entra-client-secret",
    "ENTRA_TENANT_ID": "entra-tenant-id",
}


class AppRunnerStack(cdk.Stack):
    """App Runner service with VPC connector, auto-scaling, and secrets."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        vpc_stack: VpcStack,
        secrets_stack: SecretsStack,
        rds_stack: RdsStack,
        s3_stack: S3Stack,
        ecr_stack: EcrStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"
        vpc = vpc_stack.vpc

        # Deterministic bucket name to avoid cyclic cross-stack references
        bucket_name_str = f"{prefix}-documents-{config.account_id}"
        bucket_arn = f"arn:aws:s3:::{bucket_name_str}"

        # ECR access role — allows App Runner to pull images from cross-account ECR
        ecr_access_role = iam.Role(
            self,
            "EcrAccessRole",
            role_name=f"{prefix}-apprunner-ecr-access",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
        )
        ecr_stack.repository.grant_pull(ecr_access_role)

        # Instance role — grants the running service access to S3 and Secrets Manager
        self._instance_role = iam.Role(
            self,
            "InstanceRole",
            role_name=f"{prefix}-apprunner-instance",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
        )

        # S3 read/write
        self._instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                ],
                resources=[bucket_arn, f"{bucket_arn}/*"],
            )
        )

        # Secrets Manager read
        secrets_stack.grant_read(self._instance_role)

        # Auto-scaling configuration
        self._auto_scaling_config = apprunner.CfnAutoScalingConfiguration(
            self,
            "AutoScalingConfig",
            auto_scaling_configuration_name=f"{prefix}-api-scaling",
            min_size=1,
            max_size=10,
            max_concurrency=100,
        )

        # VPC connector for RDS access in private subnets
        app_runner_sg = vpc_stack.app_runner_security_group
        private_subnet_ids = [s.subnet_id for s in vpc.private_subnets]

        self._vpc_connector = apprunner.CfnVpcConnector(
            self,
            "VpcConnector",
            vpc_connector_name=f"{prefix}-api-vpc-connector",
            subnets=private_subnet_ids,
            security_groups=[app_runner_sg.security_group_id],
        )

        # Build runtime environment secrets (env var name → Secrets Manager ARN)
        runtime_env_secrets = [
            apprunner.CfnService.KeyValuePairProperty(
                name=env_var,
                value=secrets_stack.secrets[secret_name].secret_arn,
            )
            for env_var, secret_name in _SECRET_ENV_MAP.items()
        ]

        # Build runtime environment variables (plain values)
        runtime_env_variables = [
            apprunner.CfnService.KeyValuePairProperty(
                name="S3_BUCKET_NAME",
                value=bucket_name_str,
            ),
        ]

        # ECR image URI
        ecr_image_uri = (
            f"{SHARED_SERVICES_ACCOUNT}.dkr.ecr.{config.region}.amazonaws.com"
            f"/{RESOURCE_PREFIX}-api:latest"
        )

        # App Runner service (L1 construct for full feature control)
        self._service = apprunner.CfnService(
            self,
            "Service",
            service_name=f"{prefix}-api",
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=ecr_access_role.role_arn,
                ),
                auto_deployments_enabled=False,
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_identifier=ecr_image_uri,
                    image_repository_type="ECR",
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                        port="8000",
                        runtime_environment_secrets=runtime_env_secrets,
                        runtime_environment_variables=runtime_env_variables,
                    ),
                ),
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="1024",
                memory="2048",
                instance_role_arn=self._instance_role.role_arn,
            ),
            health_check_configuration=apprunner.CfnService.HealthCheckConfigurationProperty(
                protocol="HTTP",
                path="/health",
                interval=5,
                timeout=2,
                healthy_threshold=1,
                unhealthy_threshold=5,
            ),
            auto_scaling_configuration_arn=self._auto_scaling_config.attr_auto_scaling_configuration_arn,
            network_configuration=apprunner.CfnService.NetworkConfigurationProperty(
                egress_configuration=apprunner.CfnService.EgressConfigurationProperty(
                    egress_type="VPC",
                    vpc_connector_arn=self._vpc_connector.attr_vpc_connector_arn,
                ),
            ),
        )

        # Custom domain association (no L1 construct available, use CfnResource)
        custom_domain = f"{config.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self._custom_domain = cdk.CfnResource(
            self,
            "CustomDomain",
            type="AWS::AppRunner::CustomDomainAssociation",
            properties={
                "DomainName": custom_domain,
                "ServiceArn": self._service.attr_service_arn,
                "EnableWWWSubdomain": False,
            },
        )

    @property
    def service_url(self) -> str:
        """The default App Runner service URL (e.g. xxx.us-east-1.awsapprunner.com)."""
        return self._service.attr_service_url

    @property
    def service_arn(self) -> str:
        return self._service.attr_service_arn

    @property
    def service_name(self) -> str:
        return self._service.service_name or ""

    @property
    def instance_role(self) -> iam.Role:
        return self._instance_role
