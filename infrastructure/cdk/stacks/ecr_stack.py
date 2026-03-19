"""ECR stack for Industrial workload (Shared Services account).

Creates the ECR repository for the FastAPI container image, configures
lifecycle policies, grants cross-account pull access, and provisions
GitHub OIDC IAM roles for CI/CD pipelines.
"""

import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr, aws_iam as iam
from constructs import Construct

from stacks.config import (
    GITHUB_REPO,
    INDUSTRIAL_DEV,
    INDUSTRIAL_PROD,
    RESOURCE_PREFIX,
    SHARED_SERVICES_ACCOUNT,
)


class EcrStack(cdk.Stack):
    """ECR repository and GitHub OIDC IAM roles in Shared Services account."""

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ECR repository
        self._repository = ecr.Repository(
            self,
            "IndustrialApiRepo",
            repository_name=f"{RESOURCE_PREFIX}-api",
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # Lifecycle policy: retain 20 tagged images
        self._repository.add_lifecycle_rule(
            tag_status=ecr.TagStatus.TAGGED,
            tag_prefix_list=["v", "latest", "sha-"],
            max_image_count=20,
            description="Retain 20 tagged images",
        )

        # Lifecycle policy: delete untagged images after 7 days
        self._repository.add_lifecycle_rule(
            tag_status=ecr.TagStatus.UNTAGGED,
            max_image_age=cdk.Duration.days(7),
            description="Delete untagged images after 7 days",
        )

        # Cross-account pull access for dev and prod accounts
        self._repository.add_to_resource_policy(
            iam.PolicyStatement(
                sid="CrossAccountPull",
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.AccountPrincipal(INDUSTRIAL_DEV.account_id),
                    iam.AccountPrincipal(INDUSTRIAL_PROD.account_id),
                ],
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                ],
            )
        )

        # Reference the existing GitHub OIDC provider in Shared Services
        github_oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self,
            "GitHubOidc",
            open_id_connect_provider_arn=(
                f"arn:aws:iam::{SHARED_SERVICES_ACCOUNT}"
                ":oidc-provider/token.actions.githubusercontent.com"
            ),
        )

        oidc_provider_url = "token.actions.githubusercontent.com"

        # IAM role: github-actions-industrial-build
        # Allows ECR push, scoped to ref:refs/heads/*
        self._build_role = iam.Role(
            self,
            "GitHubActionsBuildRole",
            role_name=f"github-actions-{RESOURCE_PREFIX}-build",
            assumed_by=iam.FederatedPrincipal(
                github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{oidc_provider_url}:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        f"{oidc_provider_url}:sub": (
                            f"repo:{GITHUB_REPO}:ref:refs/heads/*"
                        ),
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        # Grant ECR push permissions to the build role
        self._repository.grant(
            self._build_role,
            "ecr:BatchCheckLayerAvailability",
            "ecr:CompleteLayerUpload",
            "ecr:InitiateLayerUpload",
            "ecr:PutImage",
            "ecr:UploadLayerPart",
        )
        self._build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        # IAM role: github-actions-industrial-deploy-dev
        # Allows App Runner update in dev, scoped to ref:refs/heads/main
        self._deploy_dev_role = iam.Role(
            self,
            "GitHubActionsDeployDevRole",
            role_name=f"github-actions-{RESOURCE_PREFIX}-deploy-dev",
            assumed_by=iam.FederatedPrincipal(
                github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{oidc_provider_url}:aud": "sts.amazonaws.com",
                        f"{oidc_provider_url}:sub": (
                            f"repo:{GITHUB_REPO}:ref:refs/heads/main"
                        ),
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        self._deploy_dev_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "apprunner:UpdateService",
                    "apprunner:DescribeService",
                    "apprunner:ListServices",
                ],
                resources=[
                    f"arn:aws:apprunner:us-east-1:{INDUSTRIAL_DEV.account_id}:service/{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}-api/*",
                ],
            )
        )

        # IAM role: github-actions-industrial-deploy-prod
        # Allows App Runner update in prod, scoped to ref:refs/tags/*
        self._deploy_prod_role = iam.Role(
            self,
            "GitHubActionsDeployProdRole",
            role_name=f"github-actions-{RESOURCE_PREFIX}-deploy-prod",
            assumed_by=iam.FederatedPrincipal(
                github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{oidc_provider_url}:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        f"{oidc_provider_url}:sub": (
                            f"repo:{GITHUB_REPO}:ref:refs/tags/*"
                        ),
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
        )

        self._deploy_prod_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "apprunner:UpdateService",
                    "apprunner:DescribeService",
                    "apprunner:ListServices",
                ],
                resources=[
                    f"arn:aws:apprunner:us-east-1:{INDUSTRIAL_PROD.account_id}:service/{RESOURCE_PREFIX}-{INDUSTRIAL_PROD.env_name}-api/*",
                ],
            )
        )

    @property
    def repository(self) -> ecr.IRepository:
        return self._repository

    @property
    def build_role(self) -> iam.IRole:
        return self._build_role

    @property
    def deploy_dev_role(self) -> iam.IRole:
        return self._deploy_dev_role

    @property
    def deploy_prod_role(self) -> iam.IRole:
        return self._deploy_prod_role
