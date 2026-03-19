"""Unit tests for VPC stack.

Validates VPC CIDR, subnet count, NAT gateway, S3 endpoint,
and security group configuration against Requirements 2.1–2.5.
"""

import aws_cdk as cdk
import aws_cdk.assertions as assertions

from stacks.config import INDUSTRIAL_DEV, RESOURCE_PREFIX
from stacks.vpc_stack import VpcStack


def _synth_vpc_template() -> assertions.Template:
    """Synthesize the VPC stack for the dev environment and return the template."""
    app = cdk.App()
    config = INDUSTRIAL_DEV
    env = cdk.Environment(account=config.account_id, region=config.region)
    stack = VpcStack(app, "test-vpc", config=config, env=env)
    return assertions.Template.from_stack(stack)


class TestVpcStack:
    """Unit tests for VpcStack — Requirements 2.1–2.5."""

    def setup_method(self) -> None:
        self.template = _synth_vpc_template()
        self.prefix = f"{RESOURCE_PREFIX}-{INDUSTRIAL_DEV.env_name}"

    # Requirement 2.1 — VPC with CIDR 10.1.0.0/16
    def test_vpc_created_with_correct_cidr(self) -> None:
        self.template.resource_count_is("AWS::EC2::VPC", 1)
        self.template.has_resource_properties(
            "AWS::EC2::VPC",
            {"CidrBlock": "10.1.0.0/16"},
        )

    # Requirement 2.2 — 4 subnets (2 public + 2 private)
    def test_four_subnets_created(self) -> None:
        self.template.resource_count_is("AWS::EC2::Subnet", 4)

    # Requirement 2.3 — Internet gateway attached to VPC
    def test_internet_gateway_created(self) -> None:
        self.template.resource_count_is("AWS::EC2::InternetGateway", 1)
        self.template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)

    # Requirement 2.4 — Single NAT gateway
    def test_single_nat_gateway(self) -> None:
        self.template.resource_count_is("AWS::EC2::NatGateway", 1)

    # Requirement 2.5 — S3 VPC gateway endpoint
    def test_s3_vpc_endpoint(self) -> None:
        self.template.resource_count_is("AWS::EC2::VPCEndpoint", 1)
        self.template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {
                "ServiceName": {
                    "Fn::Join": [
                        "",
                        [
                            "com.amazonaws.",
                            {"Ref": "AWS::Region"},
                            ".s3",
                        ],
                    ]
                },
                "VpcEndpointType": "Gateway",
            },
        )

    # Security groups — Lambda SG
    def test_lambda_security_group(self) -> None:
        self.template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "GroupName": f"{self.prefix}-lambda-sg",
                "GroupDescription": "Security group for ingestion Lambda functions",
            },
        )

    # Security groups — App Runner SG
    def test_app_runner_security_group(self) -> None:
        self.template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "GroupName": f"{self.prefix}-app-runner-sg",
                "GroupDescription": "Security group for App Runner VPC connector",
            },
        )

    # Exactly 2 security groups created
    def test_two_security_groups(self) -> None:
        self.template.resource_count_is("AWS::EC2::SecurityGroup", 2)
