"""Unit tests for Amplify stack.

Validates app name, build command, env vars, branch config, preview settings,
redirect rule, and custom domain against Requirements 8.1–8.7.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.amplify_stack import AmplifyStack
from stacks.app_runner_stack import AppRunnerStack
from stacks.config import (
    HOSTED_ZONE_NAME,
    INDUSTRIAL_DEV,
    INDUSTRIAL_PROD,
    RESOURCE_PREFIX,
)
from stacks.ecr_stack import EcrStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_amplify_template(config=None) -> assertions.Template:
    """Synthesize the Amplify stack and return the CloudFormation template."""
    if config is None:
        config = INDUSTRIAL_DEV
    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    ecr_stack = EcrStack(app, f"test-ecr-{config.env_name}", env=shared_env)
    app_runner_stack = AppRunnerStack(
        app, f"test-apprunner-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        s3_stack=s3_stack,
        ecr_stack=ecr_stack,
        env=env,
    )

    amplify_stack = AmplifyStack(
        app, f"test-amplify-{config.env_name}",
        config=config,
        app_runner_stack=app_runner_stack,
        env=env,
    )
    return assertions.Template.from_stack(amplify_stack)


class TestAmplifyStack:
    """Unit tests for AmplifyStack — Requirements 8.1–8.7."""

    def setup_method(self) -> None:
        self.template = _synth_amplify_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 8.1 — App named industrial-{env}-frontend connected to GitHub
    def test_app_name(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::App",
            {"Name": f"{self.prefix}-frontend"},
        )

    # Requirement 8.1 — Connected to GitHub repository
    def test_github_repository(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::App",
            {"Repository": assertions.Match.string_like_regexp(r"https://github\.com/")},
        )

    # Requirement 8.2 — Build spec includes npm ci --legacy-peer-deps and npm run build
    def test_build_spec_contains_install_command(self) -> None:
        apps = self.template.find_resources("AWS::Amplify::App")
        app_resource = list(apps.values())[0]
        build_spec = app_resource["Properties"]["BuildSpec"]
        assert "npm ci --legacy-peer-deps" in build_spec

    def test_build_spec_contains_build_command(self) -> None:
        apps = self.template.find_resources("AWS::Amplify::App")
        app_resource = list(apps.values())[0]
        build_spec = app_resource["Properties"]["BuildSpec"]
        assert "npm run build" in build_spec

    # Requirement 8.2 — Build runs in web/ directory
    def test_build_spec_app_root(self) -> None:
        apps = self.template.find_resources("AWS::Amplify::App")
        app_resource = list(apps.values())[0]
        build_spec = app_resource["Properties"]["BuildSpec"]
        assert "appRoot: web" in build_spec

    # Requirement 8.3 — NEXT_PUBLIC_API_URL set to HTTPS App Runner custom domain
    def test_api_url_env_var(self) -> None:
        expected_url = f"https://{INDUSTRIAL_DEV.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::Amplify::App",
            {
                "EnvironmentVariables": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Name": "NEXT_PUBLIC_API_URL",
                        "Value": expected_url,
                    }),
                ]),
            },
        )

    # Requirement 8.4 — develop branch for dev
    def test_branch_name_dev(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::Branch",
            {"BranchName": "develop"},
        )

    # Requirement 8.4 — main branch for prod
    def test_branch_name_prod(self) -> None:
        template = _synth_amplify_template(INDUSTRIAL_PROD)
        template.has_resource_properties(
            "AWS::Amplify::Branch",
            {"BranchName": "main"},
        )

    # Requirement 8.5 — Branch previews enabled for dev
    def test_branch_previews_enabled_dev(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::Branch",
            {"EnablePullRequestPreview": True},
        )

    # Requirement 8.5 — Branch previews disabled for prod
    def test_branch_previews_disabled_prod(self) -> None:
        template = _synth_amplify_template(INDUSTRIAL_PROD)
        template.has_resource_properties(
            "AWS::Amplify::Branch",
            {"EnablePullRequestPreview": False},
        )

    # Requirement 8.6 — Custom domain association for dev
    def test_custom_domain_dev(self) -> None:
        expected_domain = f"{INDUSTRIAL_DEV.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::Amplify::Domain",
            {"DomainName": expected_domain},
        )

    # Requirement 8.6 — Custom domain association for prod
    def test_custom_domain_prod(self) -> None:
        template = _synth_amplify_template(INDUSTRIAL_PROD)
        expected_domain = f"{INDUSTRIAL_PROD.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        template.has_resource_properties(
            "AWS::Amplify::Domain",
            {"DomainName": expected_domain},
        )

    # Requirement 8.7 — SPA redirect rule (200 rewrite)
    def test_spa_redirect_rule(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::App",
            {
                "CustomRules": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Source": "/<*>",
                        "Target": "/index.html",
                        "Status": "200",
                    }),
                ]),
            },
        )

    # Branch has auto-build enabled
    def test_branch_auto_build(self) -> None:
        self.template.has_resource_properties(
            "AWS::Amplify::Branch",
            {"EnableAutoBuild": True},
        )

    # Exactly 1 Amplify app
    def test_app_count(self) -> None:
        self.template.resource_count_is("AWS::Amplify::App", 1)

    # Exactly 1 branch
    def test_branch_count(self) -> None:
        self.template.resource_count_is("AWS::Amplify::Branch", 1)

    # Exactly 1 domain
    def test_domain_count(self) -> None:
        self.template.resource_count_is("AWS::Amplify::Domain", 1)

    # Stack exposes expected properties
    def test_stack_properties(self) -> None:
        app = cdk.App()
        config = INDUSTRIAL_DEV
        env = cdk.Environment(account=config.account_id, region=config.region)
        shared_env = cdk.Environment(account="555555555555", region="us-east-1")

        vpc_stack = VpcStack(app, "test-vpc-props", config=config, env=env)
        secrets_stack = SecretsStack(app, "test-secrets-props", config=config, env=env)
        rds_stack = RdsStack(
            app, "test-rds-props",
            config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
        )
        s3_stack = S3Stack(app, "test-s3-props", config=config, env=env)
        ecr_stack = EcrStack(app, "test-ecr-props", env=shared_env)
        app_runner_stack = AppRunnerStack(
            app, "test-ar-props",
            config=config,
            vpc_stack=vpc_stack, secrets_stack=secrets_stack,
            rds_stack=rds_stack, s3_stack=s3_stack, ecr_stack=ecr_stack,
            env=env,
        )

        amplify = AmplifyStack(
            app, "test-amplify-props",
            config=config,
            app_runner_stack=app_runner_stack,
            env=env,
        )
        assert amplify.amplify_app is not None
        assert amplify.amplify_app_id is not None
