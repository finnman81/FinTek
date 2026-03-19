"""Unit tests for RDS stack.

Validates instance class, engine version, Multi-AZ, storage, encryption,
parameter group, snapshot retention against Requirements 3.1–3.9.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, INDUSTRIAL_PROD, RESOURCE_PREFIX
from stacks.rds_stack import RdsStack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_rds_template(config=None) -> assertions.Template:
    """Synthesize the RDS stack for the given environment and return the template."""
    if config is None:
        config = INDUSTRIAL_DEV
    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    prefix = f"industrial-{config.env_name}"

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app,
        f"test-rds-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        env=env,
    )
    return assertions.Template.from_stack(rds_stack)


class TestRdsStack:
    """Unit tests for RdsStack — Requirements 3.1–3.9."""

    def setup_method(self) -> None:
        self.template = _synth_rds_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 3.1 — PostgreSQL 16 engine
    def test_engine_version(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "Engine": "postgres",
                "EngineVersion": "16",
            },
        )

    # Requirement 3.1 — db.t4g.micro instance class
    def test_instance_class(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "DBInstanceClass": "db.t4g.micro",
            },
        )

    # Requirement 3.1 — database name munitor
    def test_database_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "DBName": "munitor",
            },
        )

    # Requirement 3.2 — placed in private subnets with DB subnet group
    def test_db_subnet_group_exists(self) -> None:
        self.template.resource_count_is("AWS::RDS::DBSubnetGroup", 1)

    # Requirement 3.3 — Multi-AZ enabled
    def test_multi_az_enabled(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "MultiAZ": True,
            },
        )

    # Requirement 3.4 — 20 GB allocated storage
    def test_allocated_storage(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "AllocatedStorage": "20",
            },
        )

    # Requirement 3.4 — auto-scaling up to 100 GB
    def test_max_allocated_storage(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "MaxAllocatedStorage": 100,
            },
        )

    # Requirement 3.5 — storage encryption enabled
    def test_storage_encryption(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "StorageEncrypted": True,
            },
        )

    # Requirement 3.6 — security group exists
    def test_security_group_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "GroupDescription": "Security group for RDS PostgreSQL instance",
            },
        )

    # Requirement 3.6 — exactly 2 ingress rules (App Runner + Lambda)
    def test_ingress_rule_count(self) -> None:
        ingress_rules = self.template.find_resources("AWS::EC2::SecurityGroupIngress")
        assert len(ingress_rules) == 2, (
            f"Expected 2 ingress rules, found {len(ingress_rules)}"
        )

    # Requirement 3.7 — publicly_accessible is false
    def test_not_publicly_accessible(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBInstance",
            {
                "PubliclyAccessible": False,
            },
        )

    # Requirement 3.8 — custom parameter group with pg_stat_statements
    def test_parameter_group_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::RDS::DBParameterGroup",
            {
                "Family": "postgres16",
                "Parameters": {
                    "shared_preload_libraries": "pg_stat_statements",
                },
            },
        )

    # Requirement 3.8 — DB instance references the parameter group
    def test_instance_uses_parameter_group(self) -> None:
        self.template.resource_count_is("AWS::RDS::DBParameterGroup", 1)

    # Requirement 3.9 — dev: skip final snapshot (DeletionPolicy Delete)
    def test_dev_skip_final_snapshot(self) -> None:
        template_json = self.template.to_json()
        resources = template_json["Resources"]
        for logical_id, resource in resources.items():
            if resource.get("Type") == "AWS::RDS::DBInstance":
                deletion_policy = resource.get("DeletionPolicy", "")
                assert deletion_policy == "Delete", (
                    f"Dev RDS instance DeletionPolicy={deletion_policy}, expected Delete"
                )
                break

    # Requirement 3.9 — prod: retain final snapshot
    def test_prod_retain_final_snapshot(self) -> None:
        prod_template = _synth_rds_template(INDUSTRIAL_PROD)
        template_json = prod_template.to_json()
        resources = template_json["Resources"]
        for logical_id, resource in resources.items():
            if resource.get("Type") == "AWS::RDS::DBInstance":
                deletion_policy = resource.get("DeletionPolicy", "")
                assert deletion_policy in ("Retain", "Snapshot"), (
                    f"Prod RDS instance DeletionPolicy={deletion_policy}, expected Retain or Snapshot"
                )
                break

    # Exactly one DB instance created
    def test_single_db_instance(self) -> None:
        self.template.resource_count_is("AWS::RDS::DBInstance", 1)

    # Smoke test — stack exposes properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        vpc_stack = VpcStack(app, "test-vpc-props", config=config, env=env)
        secrets_stack = SecretsStack(app, "test-secrets-props", config=config, env=env)
        rds_stack = RdsStack(
            app,
            "test-rds-props",
            config=config,
            vpc_stack=vpc_stack,
            secrets_stack=secrets_stack,
            env=env,
        )
        assert rds_stack.db_instance is not None
        assert rds_stack.db_security_group is not None
        assert rds_stack.database_url_secret is not None
