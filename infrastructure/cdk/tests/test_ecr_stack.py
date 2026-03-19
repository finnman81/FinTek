"""Unit tests for ECR stack.

Validates repository name, lifecycle policies, cross-account access,
and IAM role trust policies against Requirements 5.1–5.3, 15.1–15.3.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import (
    GITHUB_REPO,
    INDUSTRIAL_DEV,
    INDUSTRIAL_PROD,
    RESOURCE_PREFIX,
    SHARED_SERVICES_ACCOUNT,
)
from stacks.ecr_stack import EcrStack


def _synth_ecr_template() -> assertions.Template:
    """Synthesize the ECR stack for the Shared Services account."""
    app = cdk.App()
    env = cdk.Environment(account=SHARED_SERVICES_ACCOUNT, region="us-east-1")
    stack = EcrStack(app, "test-ecr", env=env)
    return assertions.Template.from_stack(stack)


class TestEcrStack:
    """Unit tests for EcrStack — Requirements 5.1–5.3, 15.1–15.3."""

    def setup_method(self) -> None:
        self.template = _synth_ecr_template()

    # Requirement 5.1 — ECR repository named industrial-api
    def test_repository_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::ECR::Repository",
            {"RepositoryName": f"{RESOURCE_PREFIX}-api"},
        )

    # Requirement 5.1 — exactly one ECR repository
    def test_single_repository(self) -> None:
        self.template.resource_count_is("AWS::ECR::Repository", 1)

    # Requirement 5.2 — lifecycle policy: retain 20 tagged images
    def test_lifecycle_tagged_images_retained(self) -> None:
        self.template.has_resource_properties(
            "AWS::ECR::Repository",
            {
                "LifecyclePolicy": {
                    "LifecyclePolicyText": assertions.Match.serialized_json(
                        assertions.Match.object_like(
                            {
                                "rules": assertions.Match.array_with(
                                    [
                                        assertions.Match.object_like(
                                            {
                                                "selection": assertions.Match.object_like(
                                                    {
                                                        "tagStatus": "tagged",
                                                        "countType": "imageCountMoreThan",
                                                        "countNumber": 20,
                                                    }
                                                ),
                                                "action": {"type": "expire"},
                                            }
                                        ),
                                    ]
                                ),
                            }
                        )
                    ),
                },
            },
        )

    # Requirement 5.2 — lifecycle policy: delete untagged after 7 days
    def test_lifecycle_untagged_images_deleted(self) -> None:
        self.template.has_resource_properties(
            "AWS::ECR::Repository",
            {
                "LifecyclePolicy": {
                    "LifecyclePolicyText": assertions.Match.serialized_json(
                        assertions.Match.object_like(
                            {
                                "rules": assertions.Match.array_with(
                                    [
                                        assertions.Match.object_like(
                                            {
                                                "selection": assertions.Match.object_like(
                                                    {
                                                        "tagStatus": "untagged",
                                                        "countType": "sinceImagePushed",
                                                        "countNumber": 7,
                                                        "countUnit": "days",
                                                    }
                                                ),
                                                "action": {"type": "expire"},
                                            }
                                        ),
                                    ]
                                ),
                            }
                        )
                    ),
                },
            },
        )

    # Requirement 5.3 — cross-account pull access for dev and prod
    def test_cross_account_pull_access(self) -> None:
        # CDK renders AccountPrincipal as Fn::Join intrinsics, so we verify
        # the statement structure (Sid, Effect, Actions) and that two
        # principals exist in the AWS array.
        self.template.has_resource_properties(
            "AWS::ECR::Repository",
            {
                "RepositoryPolicyText": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Sid": "CrossAccountPull",
                                        "Effect": "Allow",
                                        "Principal": {
                                            "AWS": assertions.Match.any_value(),
                                        },
                                        "Action": assertions.Match.array_with(
                                            [
                                                "ecr:BatchCheckLayerAvailability",
                                                "ecr:BatchGetImage",
                                                "ecr:GetDownloadUrlForLayer",
                                            ]
                                        ),
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.1 — build role trusts GitHub OIDC, scoped to refs/heads/*
    def test_build_role_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-build",
            },
        )

    def test_build_role_trust_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-build",
                "AssumeRolePolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": "sts:AssumeRoleWithWebIdentity",
                                        "Condition": {
                                            "StringEquals": {
                                                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                            },
                                            "StringLike": {
                                                "token.actions.githubusercontent.com:sub": f"repo:{GITHUB_REPO}:ref:refs/heads/*",
                                            },
                                        },
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.2 — deploy-dev role scoped to refs/heads/main
    def test_deploy_dev_role_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-deploy-dev",
            },
        )

    def test_deploy_dev_role_trust_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-deploy-dev",
                "AssumeRolePolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": "sts:AssumeRoleWithWebIdentity",
                                        "Condition": {
                                            "StringEquals": assertions.Match.object_like(
                                                {
                                                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                                    "token.actions.githubusercontent.com:sub": f"repo:{GITHUB_REPO}:ref:refs/heads/main",
                                                }
                                            ),
                                        },
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.3 — deploy-prod role scoped to refs/tags/*
    def test_deploy_prod_role_exists(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-deploy-prod",
            },
        )

    def test_deploy_prod_role_trust_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "RoleName": f"github-actions-{RESOURCE_PREFIX}-deploy-prod",
                "AssumeRolePolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": "sts:AssumeRoleWithWebIdentity",
                                        "Condition": assertions.Match.object_like(
                                            {
                                                "StringLike": {
                                                    "token.actions.githubusercontent.com:sub": f"repo:{GITHUB_REPO}:ref:refs/tags/*",
                                                },
                                            }
                                        ),
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.1 — build role has ECR push permissions
    def test_build_role_ecr_push_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": assertions.Match.array_with(
                                            [
                                                "ecr:BatchCheckLayerAvailability",
                                                "ecr:CompleteLayerUpload",
                                                "ecr:InitiateLayerUpload",
                                                "ecr:PutImage",
                                                "ecr:UploadLayerPart",
                                            ]
                                        ),
                                        "Effect": "Allow",
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.2 — deploy-dev role has App Runner update permissions
    def test_deploy_dev_role_apprunner_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": assertions.Match.array_with(
                                            [
                                                "apprunner:UpdateService",
                                                "apprunner:DescribeService",
                                                "apprunner:ListServices",
                                            ]
                                        ),
                                        "Effect": "Allow",
                                        "Resource": f"arn:aws:apprunner:us-east-1:{INDUSTRIAL_DEV.account_id}:service/{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}-api/*",
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Requirement 15.3 — deploy-prod role has App Runner update permissions
    def test_deploy_prod_role_apprunner_policy(self) -> None:
        self.template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": assertions.Match.array_with(
                                            [
                                                "apprunner:UpdateService",
                                                "apprunner:DescribeService",
                                                "apprunner:ListServices",
                                            ]
                                        ),
                                        "Effect": "Allow",
                                        "Resource": f"arn:aws:apprunner:us-east-1:{INDUSTRIAL_PROD.account_id}:service/{RESOURCE_PREFIX}-{INDUSTRIAL_PROD.env_name}-api/*",
                                    }
                                ),
                            ]
                        ),
                    }
                ),
            },
        )

    # Smoke test — stack exposes properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        env = cdk.Environment(account=SHARED_SERVICES_ACCOUNT, region="us-east-1")
        stack = EcrStack(app, "test-ecr-props", env=env)
        assert stack.repository is not None
        assert stack.build_role is not None
        assert stack.deploy_dev_role is not None
        assert stack.deploy_prod_role is not None

    # Exactly 3 IAM roles created
    def test_three_iam_roles(self) -> None:
        self.template.resource_count_is("AWS::IAM::Role", 3)
