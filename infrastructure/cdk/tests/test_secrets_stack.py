"""Unit tests for Secrets stack.

Validates secret creation, naming, rotation, CloudWatch alarm,
and SNS topic against Requirements 9.1–9.4.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, RESOURCE_PREFIX
from stacks.secrets_stack import SECRET_NAMES, SecretsStack


def _synth_secrets_template() -> assertions.Template:
    """Synthesize the Secrets stack for the dev environment and return the template."""
    app = cdk.App()
    config = INDUSTRIAL_DEV
    env = cdk.Environment(account=config.account_id, region=config.region)
    stack = SecretsStack(app, "test-secrets", config=config, env=env)
    return assertions.Template.from_stack(stack)


class TestSecretsStack:
    """Unit tests for SecretsStack — Requirements 9.1–9.4."""

    def setup_method(self) -> None:
        self.template = _synth_secrets_template()
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 9.1 — 6 secrets created
    def test_six_secrets_created(self) -> None:
        self.template.resource_count_is("AWS::SecretsManager::Secret", 6)

    # Requirement 9.1 — each secret has the correct naming pattern
    def test_secret_naming_pattern(self) -> None:
        for name in SECRET_NAMES:
            self.template.has_resource_properties(
                "AWS::SecretsManager::Secret",
                {"Name": f"{self.prefix}/{name}"},
            )

    # Requirement 9.2 — rotation schedule exists for database-url
    def test_rotation_schedule_exists(self) -> None:
        self.template.resource_count_is(
            "AWS::SecretsManager::RotationSchedule", 1
        )
        self.template.has_resource_properties(
            "AWS::SecretsManager::RotationSchedule",
            {
                "RotationRules": {
                    "ScheduleExpression": "rate(90 days)",
                },
            },
        )

    # Requirement 9.2 — rotation Lambda exists
    def test_rotation_lambda_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": f"{self.prefix}-secret-rotation",
                "Runtime": "python3.12",
                "Timeout": 300,
            },
        )

    # Requirement 9.3 — SNS topic for rotation alarms
    def test_sns_topic_created(self) -> None:
        self.template.resource_count_is("AWS::SNS::Topic", 1)
        self.template.has_resource_properties(
            "AWS::SNS::Topic",
            {"TopicName": f"{self.prefix}-secret-rotation-alarms"},
        )

    # Requirement 9.3 — CloudWatch alarm for rotation failures
    def test_rotation_failure_alarm(self) -> None:
        self.template.resource_count_is("AWS::CloudWatch::Alarm", 1)
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmName": f"{self.prefix}-secret-rotation-failure",
                "Threshold": 1,
                "EvaluationPeriods": 1,
                "ComparisonOperator": "GreaterThanOrEqualToThreshold",
                "TreatMissingData": "notBreaching",
            },
        )

    # Requirement 9.3 — alarm publishes to SNS topic
    def test_alarm_has_sns_action(self) -> None:
        self.template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {
                "AlarmActions": assertions.Match.any_value(),
            },
        )

    # Requirement 9.4 — grant_read helper exists (smoke test via stack properties)
    def test_secrets_property_returns_all_keys(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        stack = SecretsStack(app, "test-secrets-props", config=config, env=env)
        assert set(stack.secrets.keys()) == set(SECRET_NAMES)
