"""Unit tests for Observability stack.

Validates dashboard name, log group retention, SNS topic, audit forwarder Lambda
against Requirements 11.1–11.5.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, RESOURCE_PREFIX
from stacks.app_runner_stack import AppRunnerStack
from stacks.ecr_stack import EcrStack
from stacks.ingestion_stack import IngestionStack
from stacks.observability_stack import ObservabilityStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_observability_template(config=None) -> assertions.Template:
    """Synthesize the Observability stack and return the CloudFormation template."""
    if config is None:
        config = INDUSTRIAL_DEV
    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    ecr_stack = EcrStack(app, f"test-ecr-{config.env_name}", env=shared_env)
    ingestion_stack = IngestionStack(
        app, f"test-ingestion-{config.env_name}",
        config=config, vpc_stack=vpc_stack, s3_stack=s3_stack,
        secrets_stack=secrets_stack, rds_stack=rds_stack, ecr_stack=ecr_stack, env=env,
    )
    app_runner_stack = AppRunnerStack(
        app, f"test-apprunner-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack,
        rds_stack=rds_stack, s3_stack=s3_stack, ecr_stack=ecr_stack, env=env,
    )
    observability_stack = ObservabilityStack(
        app, f"test-obs-{config.env_name}",
        config=config, app_runner_stack=app_runner_stack,
        ingestion_stack=ingestion_stack, env=env,
    )
    return assertions.Template.from_stack(observability_stack)


class TestObservabilityStack:
    """Unit tests for ObservabilityStack — Requirements 11.1–11.5."""

    def setup_method(self) -> None:
        self.template = _synth_observability_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 11.1 — Dashboard named industrial-{env}-api-dashboard
    def test_dashboard_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Dashboard",
            {"DashboardName": f"{self.prefix}-api-dashboard"},
        )

    # Requirement 11.1 — Exactly 1 dashboard
    def test_dashboard_count(self) -> None:
        self.template.resource_count_is("AWS::CloudWatch::Dashboard", 1)

    # Requirement 11.3 — SNS topic named industrial-{env}-observability-alarms
    def test_sns_topic_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::SNS::Topic",
            {"TopicName": f"{self.prefix}-observability-alarms"},
        )

    # Requirement 11.3 — Exactly 1 SNS topic
    def test_sns_topic_count(self) -> None:
        self.template.resource_count_is("AWS::SNS::Topic", 1)

    # Requirement 11.4 — App Runner log group with 90-day retention
    def test_app_log_group(self) -> None:
        self.template.has_resource_properties(
            "AWS::Logs::LogGroup",
            {
                "LogGroupName": f"/industrial-{INDUSTRIAL_DEV.env_name}/app-runner/api",
                "RetentionInDays": 90,
            },
        )

    # Requirement 11.4 — Audit log group with 7-year retention (2557 days)
    def test_audit_log_group(self) -> None:
        self.template.has_resource_properties(
            "AWS::Logs::LogGroup",
            {
                "LogGroupName": f"/industrial-{INDUSTRIAL_DEV.env_name}/audit-logs",
                "RetentionInDays": 2557,
            },
        )

    # Requirement 11.4 — Exactly 2 log groups
    def test_log_group_count(self) -> None:
        self.template.resource_count_is("AWS::Logs::LogGroup", 2)

    # Requirement 11.2 — 4 CloudWatch alarms
    def test_alarm_count(self) -> None:
        self.template.resource_count_is("AWS::CloudWatch::Alarm", 4)

    # Requirement 11.2 — 5xx error rate alarm
    def test_alarm_5xx(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmName": f"{self.prefix}-5xx-error-rate",
                "Namespace": "AWS/AppRunner",
                "MetricName": "5xxStatusResponses",
                "ComparisonOperator": "GreaterThanThreshold",
            },
        )

    # Requirement 11.2 — p95 latency alarm
    def test_alarm_p95_latency(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmName": f"{self.prefix}-p95-latency",
                "Namespace": "AWS/AppRunner",
                "MetricName": "RequestLatency",
                "Threshold": 2000,
                "ComparisonOperator": "GreaterThanThreshold",
            },
        )

    # Requirement 11.2 — Active instances alarm
    def test_alarm_active_instances(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmName": f"{self.prefix}-active-instances",
                "Namespace": "AWS/AppRunner",
                "MetricName": "ActiveInstances",
                "Threshold": 8,
                "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            },
        )

    # Requirement 11.2 — Lambda error rate alarm
    def test_alarm_lambda_errors(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmName": f"{self.prefix}-lambda-error-rate",
                "Namespace": "AWS/Lambda",
                "MetricName": "Errors",
                "ComparisonOperator": "GreaterThanThreshold",
            },
        )

    # Requirement 11.5 — Audit log forwarder Lambda exists
    def test_audit_forwarder_lambda(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": f"{self.prefix}-audit-log-forwarder",
                "Runtime": "python3.12",
            },
        )

    # Requirement 11.5 — Audit forwarder has correct environment variables
    def test_audit_forwarder_env_vars(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Environment": assertions.Match.object_like({
                    "Variables": assertions.Match.object_like({
                        "AUDIT_BUCKET": "munitor-audit-logs",
                        "AUDIT_PREFIX": f"{self.prefix}/",
                    }),
                }),
            },
        )

    # Requirement 11.5 — Subscription filter connects audit log group to Lambda
    def test_audit_log_subscription(self) -> None:
        self.template.resource_count_is("AWS::Logs::SubscriptionFilter", 1)

    # Stack exposes expected properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        shared_env = cdk.Environment(account="555555555555", region="us-east-1")

        vpc_stack = VpcStack(app, "test-vpc-props", config=config, env=env)
        s3_stack = S3Stack(app, "test-s3-props", config=config, env=env)
        secrets_stack = SecretsStack(app, "test-secrets-props", config=config, env=env)
        rds_stack = RdsStack(
            app, "test-rds-props",
            config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
        )
        ecr_stack = EcrStack(app, "test-ecr-props", env=shared_env)
        ingestion_stack = IngestionStack(
            app, "test-ingestion-props",
            config=config, vpc_stack=vpc_stack, s3_stack=s3_stack,
            secrets_stack=secrets_stack, rds_stack=rds_stack, ecr_stack=ecr_stack, env=env,
        )
        app_runner_stack = AppRunnerStack(
            app, "test-apprunner-props",
            config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack,
            rds_stack=rds_stack, s3_stack=s3_stack, ecr_stack=ecr_stack, env=env,
        )
        obs_stack = ObservabilityStack(
            app, "test-obs-props",
            config=config, app_runner_stack=app_runner_stack,
            ingestion_stack=ingestion_stack, env=env,
        )
        assert obs_stack.dashboard is not None
        assert obs_stack.alarm_topic is not None
