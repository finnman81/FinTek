"""S3 stack for Industrial workload.

Creates the document storage bucket with versioning, SSE-S3 encryption,
public access blocking, lifecycle transition to IA after 90 days, and
a helper method to wire S3 ObjectCreated event notifications to an SQS queue.
"""

import aws_cdk as cdk
from aws_cdk import Duration, aws_s3 as s3, aws_s3_notifications as s3n, aws_sqs as sqs
from constructs import Construct

from stacks.config import RESOURCE_PREFIX, EnvironmentConfig


class S3Stack(cdk.Stack):
    """Document storage bucket with versioning, encryption, and lifecycle rules."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"

        self._bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"{prefix}-documents-{config.account_id}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90),
                        ),
                    ],
                ),
            ],
        )

    @property
    def bucket(self) -> s3.Bucket:
        return self._bucket

    @property
    def bucket_name(self) -> str:
        return self._bucket.bucket_name

    def add_event_notification(self, queue: sqs.IQueue) -> None:
        """Wire s3:ObjectCreated:* events to the given SQS queue.

        Called by the Ingestion stack once the queue exists.
        """
        self._bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SqsDestination(queue),
        )
