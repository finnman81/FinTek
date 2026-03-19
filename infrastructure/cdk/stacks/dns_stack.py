"""DNS and TLS certificate stack for Industrial workload.

Creates Route53 CNAME records in the munitor.ai hosted zone for API and
frontend custom domains, and provisions ACM certificates with DNS validation
for HTTPS. The hosted zone lives in the Shared Services account (555555555555);
this stack uses a cross-account placeholder approach with CfnRecordSet.
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_route53 as route53,
)
from constructs import Construct

from stacks.amplify_stack import AmplifyStack
from stacks.app_runner_stack import AppRunnerStack
from stacks.config import HOSTED_ZONE_NAME, RESOURCE_PREFIX, EnvironmentConfig


# Placeholder hosted zone ID for the munitor.ai zone in Shared Services.
# Replace with the real hosted zone ID after initial deployment.
_HOSTED_ZONE_ID = "Z0123456789ABCDEFGHIJ"


class DnsStack(cdk.Stack):
    """Route53 records and ACM certificates for custom domains."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        app_runner_stack: AppRunnerStack,
        amplify_stack: AmplifyStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"

        api_domain = f"{config.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        app_domain = f"{config.app_domain_prefix}.{HOSTED_ZONE_NAME}"

        # Look up the existing munitor.ai hosted zone from Shared Services.
        # Uses from_hosted_zone_attributes to avoid cross-account lookup issues.
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=_HOSTED_ZONE_ID,
            zone_name=HOSTED_ZONE_NAME,
        )

        # --- ACM Certificates (DNS-validated, auto-renewing) ---

        self._api_certificate = acm.Certificate(
            self,
            "ApiCertificate",
            domain_name=api_domain,
            certificate_name=f"{prefix}-api-cert",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        self._app_certificate = acm.Certificate(
            self,
            "AppCertificate",
            domain_name=app_domain,
            certificate_name=f"{prefix}-app-cert",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # --- Route53 CNAME records ---
        # Cross-account: the hosted zone is in Shared Services. We use
        # CfnRecordSet with the hosted zone ID so CloudFormation creates
        # the records directly (requires cross-account delegation or
        # deployment from the Shared Services account context).

        route53.CfnRecordSet(
            self,
            "ApiCname",
            hosted_zone_id=_HOSTED_ZONE_ID,
            name=api_domain,
            type="CNAME",
            ttl="300",
            resource_records=[app_runner_stack.service_url],
        )

        route53.CfnRecordSet(
            self,
            "AppCname",
            hosted_zone_id=_HOSTED_ZONE_ID,
            name=app_domain,
            type="CNAME",
            ttl="300",
            resource_records=[
                f"{amplify_stack.amplify_app_id}.amplifyapp.com",
            ],
        )

    @property
    def api_certificate(self) -> acm.Certificate:
        """ACM certificate for the API custom domain."""
        return self._api_certificate

    @property
    def app_certificate(self) -> acm.Certificate:
        """ACM certificate for the frontend custom domain."""
        return self._app_certificate
