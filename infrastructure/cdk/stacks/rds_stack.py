"""RDS stack for Industrial workload.

Creates a PostgreSQL 16 instance in private subnets with Multi-AZ,
storage encryption, custom parameter group, and a security group
restricting access to App Runner and Lambda only on port 5432.
"""

import aws_cdk as cdk
from aws_cdk import (
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

from stacks.config import RESOURCE_PREFIX, EnvironmentConfig
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


class RdsStack(cdk.Stack):
    """RDS PostgreSQL 16 with pgvector support in private subnets."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        vpc_stack: VpcStack,
        secrets_stack: SecretsStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"
        vpc = vpc_stack.vpc

        # Security group — only App Runner and Lambda on port 5432
        self._db_security_group = ec2.SecurityGroup(
            self,
            "DbSg",
            vpc=vpc,
            security_group_name=f"{prefix}-rds-sg",
            description="Security group for RDS PostgreSQL instance",
            allow_all_outbound=False,
        )

        self._db_security_group.add_ingress_rule(
            peer=vpc_stack.app_runner_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow App Runner on port 5432",
        )

        self._db_security_group.add_ingress_rule(
            peer=vpc_stack.lambda_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow Lambda on port 5432",
        )

        # Custom parameter group with pg_stat_statements
        self._parameter_group = rds.ParameterGroup(
            self,
            "ParameterGroup",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16,
            ),
            description=f"{prefix} PostgreSQL 16 parameter group",
            parameters={
                "shared_preload_libraries": "pg_stat_statements",
            },
        )

        # DB subnet group spanning both AZs (private subnets)
        self._subnet_group = rds.SubnetGroup(
            self,
            "SubnetGroup",
            description=f"{prefix} DB subnet group",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
        )

        # Determine removal/snapshot policy based on environment
        is_prod = config.env_name == "prod"

        self._db_instance = rds.DatabaseInstance(
            self,
            "Instance",
            instance_identifier=f"{prefix}-db",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16,
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON,
                ec2.InstanceSize.MICRO,
            ),
            database_name="munitor",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            subnet_group=self._subnet_group,
            security_groups=[self._db_security_group],
            multi_az=True,
            allocated_storage=20,
            max_allocated_storage=100,
            storage_encrypted=True,
            publicly_accessible=False,
            parameter_group=self._parameter_group,
            removal_policy=RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY,
            delete_automated_backups=not is_prod,
        )

        # Skip final snapshot for dev; retain for prod
        if not is_prod:
            self._db_instance.node.default_child.add_property_override(
                "DeletionPolicy", "Delete"
            )
            self._db_instance.node.default_child.add_property_override(
                "DeleteAutomatedBackups", True
            )

        # Store connection URL in the existing Secrets Manager secret
        self._database_url_secret = secrets_stack.secrets["database-url"]

    @property
    def db_instance(self) -> rds.DatabaseInstance:
        return self._db_instance

    @property
    def db_security_group(self) -> ec2.SecurityGroup:
        return self._db_security_group

    @property
    def database_url_secret(self) -> secretsmanager.Secret:
        return self._database_url_secret
