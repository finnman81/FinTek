"""Unit tests for Ingestion stack.

Validates queue names, visibility timeout, DLQ config, Lambda timeout/memory,
SQS trigger, VPC placement against Requirements 7.1–7.8, 7.10.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, RESOURCE_PREFIX
from stacks.ecr_stack import EcrStack
from stacks.ingestion_stack import IngestionStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_ingestion_template(config=None) -> assertions.Template:
    """Synthesize the Ingestion stack and return the CloudFormation template."""
    if config is None:
        config = INDUSTRIAL_DEV
    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")
    prefix = f"industrial-{config.env_name}"

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    ecr_stack = EcrStack(app, "test-ecr", env=shared_env)

    ingestion_stack = IngestionStack(
        app, f"test-ingestion-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        s3_stack=s3_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        ecr_stack=ecr_stack,
        env=env,
    )
    return assertions.Template.from_stack(ingestion_stack)


class TestIngestionStack:
    """Unit tests for IngestionStack — Requirements 7.1–7.8, 7.10."""

    def setup_method(self) -> None:
        self.template = _synth_ingestion_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 7.1 — SQS queue named industrial-{env}-ingestion
    def test_queue_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::SQS::Queue",
            {"QueueName": f"{self.prefix}-ingestion"},
        )

    # Requirement 7.1 — visibility timeout 900s
    def test_queue_visibility_timeout(self) -> None:
        self.template.has_resource_properties(
            "AWS::SQS::Queue",
            {
                "QueueName": f"{self.prefix}-ingestion",
                "VisibilityTimeout": 900,
            },
        )

    # Requirement 7.2 — DLQ named industrial-{env}-ingestion-dlq
    def test_dlq_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::SQS::Queue",
            {"QueueName": f"{self.prefix}-ingestion-dlq"},
        )

    # Requirement 7.2 / 7.10 — DLQ maxReceiveCount=3
    def test_dlq_max_receive_count(self) -> None:
        self.template.has_resource_properties(
            "AWS::SQS::Queue",
            {
                "QueueName": f"{self.prefix}-ingestion",
                "RedrivePolicy": assertions.Match.object_like({
                    "maxReceiveCount": 3,
                }),
            },
        )

    # Requirement 7.3 — Lambda function name
    def test_lambda_function_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": f"{self.prefix}-ingestion-worker"},
        )

    # Requirement 7.3 — Lambda uses container image (PackageType Image)
    def test_lambda_package_type(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {"PackageType": "Image"},
        )

    # Requirement 7.4 — Lambda timeout 900s
    def test_lambda_timeout(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Timeout": 900},
        )

    # Requirement 7.4 — Lambda memory 1024 MB
    def test_lambda_memory(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {"MemorySize": 1024},
        )

    # Requirement 7.5 — SQS event source mapping with batch size 1
    def test_sqs_event_source_batch_size(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::EventSourceMapping",
            {"BatchSize": 1},
        )

    # Requirement 7.6 — Lambda environment variables
    def test_lambda_environment_variables(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Environment": assertions.Match.object_like({
                    "Variables": assertions.Match.object_like({
                        "DATABASE_URL": assertions.Match.any_value(),
                        "OPENAI_API_KEY": assertions.Match.any_value(),
                        "S3_BUCKET_NAME": assertions.Match.any_value(),
                    }),
                }),
            },
        )

    # Requirement 7.8 — Lambda placed in VPC (has VpcConfig)
    def test_lambda_vpc_placement(self) -> None:
        self.template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "VpcConfig": assertions.Match.object_like({
                    "SubnetIds": assertions.Match.any_value(),
                    "SecurityGroupIds": assertions.Match.any_value(),
                }),
            },
        )

    # Requirement 7.7 — IAM role has VPC access managed policy
    def test_execution_role_vpc_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "ManagedPolicyArns": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Fn::Join": assertions.Match.array_with([
                            "",
                            assertions.Match.array_with([
                                assertions.Match.string_like_regexp(
                                    ".*AWSLambdaVPCAccessExecutionRole.*"
                                ),
                            ]),
                        ]),
                    }),
                ]),
            },
        )

    # Exactly 2 SQS queues (main + DLQ)
    def test_queue_count(self) -> None:
        self.template.resource_count_is("AWS::SQS::Queue", 2)

    # Exactly 1 Lambda function
    def test_lambda_count(self) -> None:
        self.template.resource_count_is("AWS::Lambda::Function", 1)

    # Exactly 1 event source mapping
    def test_event_source_mapping_count(self) -> None:
        self.template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)

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
            config=config,
            vpc_stack=vpc_stack,
            s3_stack=s3_stack,
            secrets_stack=secrets_stack,
            rds_stack=rds_stack,
            ecr_stack=ecr_stack,
            env=env,
        )
        assert ingestion_stack.queue is not None
        assert ingestion_stack.dlq is not None
        assert ingestion_stack.function is not None
        assert ingestion_stack.execution_role is not None
