"""Unit tests for DNS stack.

Validates Route53 CNAME records, ACM certificates, and DNS validation
against Requirements 10.1–10.4.
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
from stacks.dns_stack import DnsStack
from stacks.ecr_stack import EcrStack
from stacks.rds_stack import RdsStack
from stacks.s3_stack import S3Stack
from stacks.secrets_stack import SecretsStack
from stacks.vpc_stack import VpcStack


def _synth_dns_template(config=None) -> assertions.Template:
    """Synthesize the DNS stack and return the CloudFormation template."""
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

    dns_stack = DnsStack(
        app, f"test-dns-{config.env_name}",
        config=config,
        app_runner_stack=app_runner_stack,
        amplify_stack=amplify_stack,
        env=env,
    )
    return assertions.Template.from_stack(dns_stack)


class TestDnsStack:
    """Unit tests for DnsStack — Requirements 10.1–10.4."""

    def setup_method(self) -> None:
        self.template = _synth_dns_template(INDUSTRIAL_DEV)
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # --- Requirement 10.1 — Route53 CNAME records for prod ---

    def test_api_cname_record_prod(self) -> None:
        template = _synth_dns_template(INDUSTRIAL_PROD)
        api_domain = f"{INDUSTRIAL_PROD.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"Name": api_domain, "Type": "CNAME"},
        )

    def test_app_cname_record_prod(self) -> None:
        template = _synth_dns_template(INDUSTRIAL_PROD)
        app_domain = f"{INDUSTRIAL_PROD.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"Name": app_domain, "Type": "CNAME"},
        )

    # --- Requirement 10.2 — Route53 CNAME records for dev ---

    def test_api_cname_record_dev(self) -> None:
        api_domain = f"{INDUSTRIAL_DEV.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"Name": api_domain, "Type": "CNAME"},
        )

    def test_app_cname_record_dev(self) -> None:
        app_domain = f"{INDUSTRIAL_DEV.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"Name": app_domain, "Type": "CNAME"},
        )

    # --- Requirement 10.3 — ACM certificates with DNS validation ---

    def test_api_certificate_exists(self) -> None:
        api_domain = f"{INDUSTRIAL_DEV.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {"DomainName": api_domain},
        )

    def test_app_certificate_exists(self) -> None:
        app_domain = f"{INDUSTRIAL_DEV.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {"DomainName": app_domain},
        )

    def test_api_certificate_dns_validation(self) -> None:
        api_domain = f"{INDUSTRIAL_DEV.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {
                "DomainName": api_domain,
                "ValidationMethod": "DNS",
            },
        )

    def test_app_certificate_dns_validation(self) -> None:
        app_domain = f"{INDUSTRIAL_DEV.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {
                "DomainName": app_domain,
                "ValidationMethod": "DNS",
            },
        )

    # --- Requirement 10.4 — Auto-renewal via DNS validation records ---
    # ACM certificates with DNS validation auto-renew as long as the
    # validation CNAME records exist. CDK's Certificate with
    # CertificateValidation.from_dns() creates these records automatically.

    def test_api_certificate_has_domain_validation_options(self) -> None:
        api_domain = f"{INDUSTRIAL_DEV.api_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {
                "DomainName": api_domain,
                "DomainValidationOptions": assertions.Match.any_value(),
            },
        )

    def test_app_certificate_has_domain_validation_options(self) -> None:
        app_domain = f"{INDUSTRIAL_DEV.app_domain_prefix}.{HOSTED_ZONE_NAME}"
        self.template.has_resource_properties(
            "AWS::CertificateManager::Certificate",
            {
                "DomainName": app_domain,
                "DomainValidationOptions": assertions.Match.any_value(),
            },
        )

    # --- Resource counts ---

    def test_two_cname_records(self) -> None:
        self.template.resource_count_is("AWS::Route53::RecordSet", 2)

    def test_two_certificates(self) -> None:
        self.template.resource_count_is("AWS::CertificateManager::Certificate", 2)

    # --- CNAME record TTL ---

    def test_cname_ttl(self) -> None:
        self.template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"TTL": "300", "Type": "CNAME"},
        )

    # --- Stack exposes certificate properties ---

    def test_stack_exposes_api_certificate(self) -> None:
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
        amplify_stack = AmplifyStack(
            app, "test-amplify-props",
            config=config,
            app_runner_stack=app_runner_stack,
            env=env,
        )

        dns = DnsStack(
            app, "test-dns-props",
            config=config,
            app_runner_stack=app_runner_stack,
            amplify_stack=amplify_stack,
            env=env,
        )
        assert dns.api_certificate is not None
        assert dns.app_certificate is not None
