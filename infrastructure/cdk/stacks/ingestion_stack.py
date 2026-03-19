"""Ingestion stack for Industrial workload.

Creates an SQS queue with DLQ for document ingestion events, a Lambda function
(container image from ECR) triggered by SQS, and wires S3 ObjectCreated
notifications to the queue. The Lambda runs in VPC private subnets for RDS access.
"""

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_event_sources as event_sources,
    aws_sqs as sqs,
)
from constructs import Construct

from stacks.config import RESOURCE_PREFIX, EnvironmentConfig
from stacks.ecr_stack import EcrStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


class IngestionStack(cdk.Stack):
    """SQS queue, DLQ, Lambda ingestion worker, and S3 event wiring."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        vpc_stack: VpcStack,
        s3_stack: S3Stack,
        secrets_stack: SecretsStack,
        rds_stack: RdsStack,
        ecr_stack: EcrStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"
        vpc = vpc_stack.vpc

        # Deterministic bucket name to avoid cyclic cross-stack references.
        # The S3 notification wires S3 → SQS (S3 stack depends on this stack),
        # so we cannot also reference the bucket ARN token from the S3 stack.
        bucket_name_str = f"{prefix}-documents-{config.account_id}"
        bucket_arn = f"arn:aws:s3:::{bucket_name_str}"

        # Dead-letter queue
        self._dlq = sqs.Queue(
            self,
            "IngestionDlq",
            queue_name=f"{prefix}-ingestion-dlq",
        )

        # Main ingestion queue — visibility timeout matches Lambda timeout
        self._queue = sqs.Queue(
            self,
            "IngestionQueue",
            queue_name=f"{prefix}-ingestion",
            visibility_timeout=Duration.seconds(900),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self._dlq,
            ),
        )

        # Lambda security group — use the VPC stack's Lambda SG which already
        # allows all outbound (for OpenAI API via NAT) and is permitted by
        # the RDS security group on port 5432.
        lambda_sg = vpc_stack.lambda_security_group

        # IAM execution role for the Lambda
        self._execution_role = iam.Role(
            self,
            "IngestionWorkerRole",
            role_name=f"{prefix}-ingestion-worker-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                # VPC access (ENI management)
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole",
                ),
            ],
        )

        # S3 read/write — use deterministic ARN to avoid cross-stack cycle
        self._execution_role.add_to_policy(
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

        # Secrets Manager read access
        secrets_stack.grant_read(self._execution_role)

        # SQS consume permissions
        self._queue.grant_consume_messages(self._execution_role)

        # Lambda function — container image from ECR
        self._function = lambda_.DockerImageFunction(
            self,
            "IngestionWorker",
            function_name=f"{prefix}-ingestion-worker",
            code=lambda_.DockerImageCode.from_ecr(
                repository=ecr_stack.repository,
                tag_or_digest="latest",
                cmd=["src.lambda_handlers.ingestion_handler.handler"],
            ),
            timeout=Duration.seconds(900),
            memory_size=1024,
            role=self._execution_role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            security_groups=[lambda_sg],
            environment={
                "DATABASE_URL": secrets_stack.secrets["database-url"].secret_name,
                "OPENAI_API_KEY": secrets_stack.secrets["openai-api-key"].secret_name,
                "S3_BUCKET_NAME": bucket_name_str,
            },
        )

        # SQS event source — batch size 1
        self._function.add_event_source(
            event_sources.SqsEventSource(
                self._queue,
                batch_size=1,
            ),
        )

    @property
    def queue(self) -> sqs.Queue:
        return self._queue

    @property
    def dlq(self) -> sqs.Queue:
        return self._dlq

    @property
    def function(self) -> lambda_.DockerImageFunction:
        return self._function

    @property
    def execution_role(self) -> iam.Role:
        return self._execution_role
