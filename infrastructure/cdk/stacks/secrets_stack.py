"""Secrets stack for Industrial workload.

Creates Secrets Manager secrets per environment, configures 90-day automatic
rotation for the database-url secret, and sets up a CloudWatch alarm for
rotation failures publishing to an SNS topic.
"""

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
)
from constructs import Construct

from stacks.config import RESOURCE_PREFIX, EnvironmentConfig

# All secrets managed by this stack
SECRET_NAMES = [
    "database-url",
    "openai-api-key",
    "cors-origins",
    "entra-client-id",
    "entra-client-secret",
    "entra-tenant-id",
]


class SecretsStack(cdk.Stack):
    """Secrets Manager secrets, rotation, and rotation-failure alarm."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"
        self._secrets: dict[str, secretsmanager.Secret] = {}

        # Create all 6 secrets with the naming pattern industrial-{env}/{secret-name}
        for name in SECRET_NAMES:
            secret = secretsmanager.Secret(
                self,
                f"Secret-{name}",
                secret_name=f"{prefix}/{name}",
                description=f"{name} for {prefix}",
            )
            self._secrets[name] = secret

        # Rotation Lambda for database-url (90-day cycle)
        rotation_fn = lambda_.Function(
            self,
            "RotationLambda",
            function_name=f"{prefix}-secret-rotation",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    # Placeholder rotation logic — replace with real implementation\n"
                "    import boto3, json\n"
                "    client = boto3.client('secretsmanager')\n"
                "    step = event['Step']\n"
                "    if step == 'createSecret':\n"
                "        current = client.get_secret_value(SecretId=event['SecretId'], VersionStage='AWSCURRENT')\n"
                "        client.put_secret_value(SecretId=event['SecretId'], ClientRequestToken=event['ClientRequestToken'], SecretString=current['SecretString'], VersionStages=['AWSPENDING'])\n"
                "    elif step == 'finishSecret':\n"
                "        metadata = client.describe_secret(SecretId=event['SecretId'])\n"
                "        for version_id, stages in metadata['VersionIdsToStages'].items():\n"
                "            if 'AWSPENDING' in stages:\n"
                "                client.update_secret_version_stage(SecretId=event['SecretId'], VersionStage='AWSCURRENT', MoveToVersionId=version_id, RemoveFromVersionId=[k for k,v in metadata['VersionIdsToStages'].items() if 'AWSCURRENT' in v][0])\n"
                "                break\n"
            ),
            timeout=Duration.minutes(5),
        )

        # Grant the rotation Lambda permission to manage the secret
        self._secrets["database-url"].grant_read(rotation_fn)
        self._secrets["database-url"].grant_write(rotation_fn)
        rotation_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:PutSecretValue",
                    "secretsmanager:UpdateSecretVersionStage",
                ],
                resources=[self._secrets["database-url"].secret_arn],
            )
        )

        # Configure 90-day automatic rotation
        self._secrets["database-url"].add_rotation_schedule(
            "RotationSchedule",
            rotation_lambda=rotation_fn,
            automatically_after=Duration.days(90),
        )

        # SNS topic for rotation failure alarms
        self._alarm_topic = sns.Topic(
            self,
            "RotationAlarmTopic",
            topic_name=f"{prefix}-secret-rotation-alarms",
        )

        # CloudWatch alarm on rotation failures
        self._rotation_alarm = cloudwatch.Alarm(
            self,
            "RotationFailureAlarm",
            alarm_name=f"{prefix}-secret-rotation-failure",
            metric=rotation_fn.metric_errors(
                period=Duration.hours(1),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description=(
                f"Rotation Lambda errors detected for {prefix}/database-url"
            ),
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        self._rotation_alarm.add_alarm_action(cw_actions.SnsAction(self._alarm_topic))

    @property
    def secrets(self) -> dict[str, secretsmanager.Secret]:
        """Map of secret short name → ISecret for cross-stack references."""
        return self._secrets

    @property
    def alarm_topic(self) -> sns.Topic:
        return self._alarm_topic

    @property
    def rotation_alarm(self) -> cloudwatch.Alarm:
        return self._rotation_alarm

    def grant_read(self, grantee: iam.IGrantable) -> None:
        """Grant read access to all secrets for a given principal."""
        for secret in self._secrets.values():
            secret.grant_read(grantee)
