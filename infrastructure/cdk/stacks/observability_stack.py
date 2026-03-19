"""Observability stack for Industrial workload.

Creates CloudWatch dashboard, alarms, SNS topic, log groups, and an audit log
forwarder Lambda that ships logs to S3 in the Log Archive account.
"""

import json

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_logs_destinations as log_destinations,
    aws_sns as sns,
)
from constructs import Construct

from stacks.app_runner_stack import AppRunnerStack
from stacks.config import LOG_ARCHIVE_ACCOUNT, RESOURCE_PREFIX, EnvironmentConfig
from stacks.ingestion_stack import IngestionStack


class ObservabilityStack(cdk.Stack):
    """CloudWatch dashboard, alarms, log groups, and audit log forwarder."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        app_runner_stack: AppRunnerStack,
        ingestion_stack: IngestionStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"
        service_name = app_runner_stack.service_name
        lambda_function_name = ingestion_stack.function.function_name

        # --- SNS topic for alarm notifications ---
        self._alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name=f"{prefix}-observability-alarms",
        )
        alarm_action = cw_actions.SnsAction(self._alarm_topic)

        # --- Log groups ---
        self._app_log_group = logs.LogGroup(
            self,
            "AppLogGroup",
            log_group_name=f"/industrial-{config.env_name}/app-runner/api",
            retention=logs.RetentionDays.THREE_MONTHS,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self._audit_log_group = logs.LogGroup(
            self,
            "AuditLogGroup",
            log_group_name=f"/industrial-{config.env_name}/audit-logs",
            retention=logs.RetentionDays.SEVEN_YEARS,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # --- CloudWatch alarms ---

        # 5xx error rate > 1%
        self._alarm_5xx = cloudwatch.Alarm(
            self,
            "Alarm5xxRate",
            alarm_name=f"{prefix}-5xx-error-rate",
            metric=cloudwatch.Metric(
                namespace="AWS/AppRunner",
                metric_name="5xxStatusResponses",
                dimensions_map={"ServiceName": service_name},
                period=Duration.minutes(5),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="App Runner 5xx error rate exceeding 1%",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        self._alarm_5xx.add_alarm_action(alarm_action)

        # p95 latency > 2s
        self._alarm_latency = cloudwatch.Alarm(
            self,
            "AlarmP95Latency",
            alarm_name=f"{prefix}-p95-latency",
            metric=cloudwatch.Metric(
                namespace="AWS/AppRunner",
                metric_name="RequestLatency",
                dimensions_map={"ServiceName": service_name},
                period=Duration.minutes(5),
                statistic="p95",
            ),
            threshold=2000,
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="App Runner p95 latency exceeding 2 seconds",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        self._alarm_latency.add_alarm_action(alarm_action)

        # Active instances >= 8
        self._alarm_instances = cloudwatch.Alarm(
            self,
            "AlarmActiveInstances",
            alarm_name=f"{prefix}-active-instances",
            metric=cloudwatch.Metric(
                namespace="AWS/AppRunner",
                metric_name="ActiveInstances",
                dimensions_map={"ServiceName": service_name},
                period=Duration.minutes(5),
                statistic="Maximum",
            ),
            threshold=8,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="App Runner active instances reaching capacity threshold",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        self._alarm_instances.add_alarm_action(alarm_action)

        # Lambda error rate > 5%
        self._alarm_lambda_errors = cloudwatch.Alarm(
            self,
            "AlarmLambdaErrors",
            alarm_name=f"{prefix}-lambda-error-rate",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={"FunctionName": lambda_function_name},
                period=Duration.minutes(5),
                statistic="Sum",
            ),
            threshold=5,
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Ingestion Lambda error rate exceeding 5%",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        self._alarm_lambda_errors.add_alarm_action(alarm_action)

        # --- CloudWatch dashboard ---
        dashboard_body = json.dumps({
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 6, "height": 6,
                    "properties": {
                        "title": "Request Count",
                        "metrics": [
                            ["AWS/AppRunner", "Requests", "ServiceName", service_name, {"stat": "Sum"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
                {
                    "type": "metric",
                    "x": 6, "y": 0, "width": 6, "height": 6,
                    "properties": {
                        "title": "5xx Error Rate",
                        "metrics": [
                            ["AWS/AppRunner", "5xxStatusResponses", "ServiceName", service_name, {"stat": "Sum"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0, "width": 6, "height": 6,
                    "properties": {
                        "title": "p95 Latency",
                        "metrics": [
                            ["AWS/AppRunner", "RequestLatency", "ServiceName", service_name, {"stat": "p95"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6, "width": 6, "height": 6,
                    "properties": {
                        "title": "CPU Utilization",
                        "metrics": [
                            ["AWS/AppRunner", "CPUUtilization", "ServiceName", service_name, {"stat": "Average"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
                {
                    "type": "metric",
                    "x": 6, "y": 6, "width": 6, "height": 6,
                    "properties": {
                        "title": "Memory Utilization",
                        "metrics": [
                            ["AWS/AppRunner", "MemoryUtilization", "ServiceName", service_name, {"stat": "Average"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
                {
                    "type": "metric",
                    "x": 12, "y": 6, "width": 6, "height": 6,
                    "properties": {
                        "title": "Active Instances",
                        "metrics": [
                            ["AWS/AppRunner", "ActiveInstances", "ServiceName", service_name, {"stat": "Maximum"}],
                        ],
                        "period": 300,
                        "region": config.region,
                    },
                },
            ],
        })

        self._dashboard = cloudwatch.CfnDashboard(
            self,
            "Dashboard",
            dashboard_name=f"{prefix}-api-dashboard",
            dashboard_body=dashboard_body,
        )

        # --- Audit log forwarder Lambda ---
        audit_bucket_name = "munitor-audit-logs"
        audit_bucket_arn = f"arn:aws:s3:::{audit_bucket_name}"

        audit_forwarder_role = iam.Role(
            self,
            "AuditForwarderRole",
            role_name=f"{prefix}-audit-log-forwarder-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole",
                ),
            ],
        )

        # Allow writing to the audit logs bucket in the Log Archive account
        audit_forwarder_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{audit_bucket_arn}/{prefix}/*"],
            )
        )

        self._audit_forwarder = lambda_.Function(
            self,
            "AuditLogForwarder",
            function_name=f"{prefix}-audit-log-forwarder",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                "import boto3, gzip, json, os, base64\n"
                "from datetime import datetime\n"
                "\n"
                "s3 = boto3.client('s3')\n"
                "BUCKET = os.environ['AUDIT_BUCKET']\n"
                "PREFIX = os.environ['AUDIT_PREFIX']\n"
                "\n"
                "def handler(event, context):\n"
                "    payload = base64.b64decode(event['awslogs']['data'])\n"
                "    log_data = json.loads(gzip.decompress(payload))\n"
                "    ts = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')\n"
                "    key = f'{PREFIX}{ts}-{context.aws_request_id}.json.gz'\n"
                "    body = gzip.compress(json.dumps(log_data).encode())\n"
                "    s3.put_object(Bucket=BUCKET, Key=key, Body=body)\n"
                "    return {'statusCode': 200}\n"
            ),
            timeout=Duration.minutes(1),
            role=audit_forwarder_role,
            environment={
                "AUDIT_BUCKET": audit_bucket_name,
                "AUDIT_PREFIX": f"{prefix}/",
            },
        )

        # Subscribe the forwarder Lambda to the audit log group
        logs.SubscriptionFilter(
            self,
            "AuditLogSubscription",
            log_group=self._audit_log_group,
            destination=log_destinations.LambdaDestination(self._audit_forwarder),
            filter_pattern=logs.FilterPattern.all_events(),
        )

    @property
    def dashboard(self) -> cloudwatch.CfnDashboard:
        return self._dashboard

    @property
    def alarm_topic(self) -> sns.Topic:
        return self._alarm_topic
