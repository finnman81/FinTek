"""Amplify Hosting stack for Industrial workload.

Creates an Amplify app connected to GitHub for the Next.js frontend,
with environment-specific branch configuration, SPA redirect rules,
custom domain association, and branch preview support.
Uses L1 CfnApp and CfnBranch constructs for full feature control.
"""

import aws_cdk as cdk
from aws_cdk import aws_amplify as amplify
from constructs import Construct

from stacks.app_runner_stack import AppRunnerStack
from stacks.config import GITHUB_REPO, HOSTED_ZONE_NAME, RESOURCE_PREFIX, EnvironmentConfig


class AmplifyStack(cdk.Stack):
    """Amplify Hosting for the Next.js frontend."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        app_runner_stack: AppRunnerStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"

        # HTTPS URL for the API (App Runner custom domain)
        api_url = f"https://{config.api_domain_prefix}.{HOSTED_ZONE_NAME}"

        # Amplify app (L1 construct)
        self._amplify_app = amplify.CfnApp(
            self,
            "App",
            name=f"{prefix}-frontend",
            repository=f"https://github.com/{GITHUB_REPO}",
            build_spec=self._build_spec(),
            environment_variables=[
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="NEXT_PUBLIC_API_URL",
                    value=api_url,
                ),
            ],
            custom_rules=[
                amplify.CfnApp.CustomRuleProperty(
                    source="/<*>",
                    target="/index.html",
                    status="200",
                ),
            ],
            enable_branch_auto_deletion=True,
        )

        # Branch configuration
        self._branch = amplify.CfnBranch(
            self,
            "Branch",
            app_id=self._amplify_app.attr_app_id,
            branch_name=config.branch,
            enable_auto_build=True,
            enable_pull_request_preview=config.branch_previews_enabled,
        )

        # Custom domain association
        custom_domain = f"{config.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self._domain = amplify.CfnDomain(
            self,
            "Domain",
            app_id=self._amplify_app.attr_app_id,
            domain_name=custom_domain,
            sub_domain_settings=[
                amplify.CfnDomain.SubDomainSettingProperty(
                    branch_name=self._branch.branch_name,
                    prefix="",
                ),
            ],
        )

    @staticmethod
    def _build_spec() -> str:
        """Return the Amplify build spec YAML for the Next.js app."""
        return "\n".join([
            "version: 1",
            "applications:",
            "  - appRoot: web",
            "    frontend:",
            "      phases:",
            "        preBuild:",
            "          commands:",
            "            - npm ci --legacy-peer-deps",
            "        build:",
            "          commands:",
            "            - npm run build",
            "      artifacts:",
            "        baseDirectory: .next",
            "        files:",
            "          - '**/*'",
            "      cache:",
            "        paths:",
            "          - node_modules/**/*",
            "          - .next/cache/**/*",
        ])

    @property
    def amplify_app(self) -> amplify.CfnApp:
        """The Amplify CfnApp construct."""
        return self._amplify_app

    @property
    def amplify_app_id(self) -> str:
        """The Amplify app ID."""
        return self._amplify_app.attr_app_id
