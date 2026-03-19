"""Unit tests for S3 stack.

Validates bucket name, versioning, encryption, public access block,
and lifecycle rule against Requirements 4.1–4.5.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, RESOURCE_PREFIX
from stacks.s3_stack import S3Stack


def _synth_s3_template() -> assertions.Template:
    """Synthesize the S3 stack for the dev environment and return the template."""
    app = cdk.App()
    config = INDUSTRIAL_DEV
    env = cdk.Environment(account=config.account_id, region=config.region)
    stack = S3Stack(app, "test-s3", config=config, env=env)
    return assertions.Template.from_stack(stack)


class TestS3Stack:
    """Unit tests for S3Stack — Requirements 4.1–4.5."""

    def setup_method(self) -> None:
        self.template = _synth_s3_template()
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 4.1 — bucket named industrial-{env}-documents-{accountId}
    def test_bucket_name(self) -> None:
        expected_name = f"{self.prefix}-documents-{INDUSTRIAL_DEV.account_id}"
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {"BucketName": expected_name},
        )

    # Requirement 4.1 — exactly one bucket created
    def test_single_bucket_created(self) -> None:
        self.template.resource_count_is("AWS::S3::Bucket", 1)

    # Requirement 4.2 — versioning enabled
    def test_versioning_enabled(self) -> None:
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "VersioningConfiguration": {"Status": "Enabled"},
            },
        )

    # Requirement 4.3 — SSE-S3 encryption
    def test_sse_s3_encryption(self) -> None:
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [
                        {
                            "ServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "AES256",
                            },
                        },
                    ],
                },
            },
        )

    # Requirement 4.4 — block all public access
    def test_public_access_blocked(self) -> None:
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                },
            },
        )

    # Requirement 4.5 — lifecycle rule transitions to IA after 90 days
    def test_lifecycle_rule_ia_transition(self) -> None:
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": assertions.Match.array_with(
                        [
                            assertions.Match.object_like(
                                {
                                    "Status": "Enabled",
                                    "Transitions": [
                                        {
                                            "StorageClass": "STANDARD_IA",
                                            "TransitionInDays": 90,
                                        },
                                    ],
                                }
                            ),
                        ]
                    ),
                },
            },
        )

    # Smoke test — stack exposes bucket and bucket_name properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        stack = S3Stack(app, "test-s3-props", config=config, env=env)
        assert stack.bucket is not None
        # bucket_name is a CDK token at synth time; verify the property exists
        assert stack.bucket_name is not None
